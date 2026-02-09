# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import threading
from typing import Dict, List

from .config import (
    CHAT_MAX_TURNS,
    POSTGRES_CONNECT_TIMEOUT,
    POSTGRES_DSN,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_ADMIN_DB,
    POSTGRES_AUTO_CREATE_DB,
    POSTGRES_SCHEMA,
    POSTGRES_USER,
    STORE_BACKEND,
)
from .state import clone_state, default_state

_store_lock = threading.Lock()
_store: Dict[str, dict] = {}
_chat_store: Dict[str, List[dict]] = {}
_CHAT_MAX_TURNS = CHAT_MAX_TURNS

_pg_lock = threading.Lock()
_pg_inited = False


def _use_postgres() -> bool:
    return str(STORE_BACKEND or "").lower() == "postgres"


def _pg_connect():
    os.environ.setdefault("PGCLIENTENCODING", "UTF8")
    dsn = POSTGRES_DSN
    use_kwargs = False
    if not dsn:
        if not all([POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER]):
            raise RuntimeError(
                "POSTGRES_DSN or POSTGRES_HOST/POSTGRES_DB/POSTGRES_USER is required when STORE_BACKEND=postgres"
            )
        use_kwargs = True
    try:
        import psycopg2
        from psycopg2 import errorcodes
        from psycopg2.extras import register_default_jsonb
    except ImportError as exc:
        raise RuntimeError("psycopg2-binary is not installed") from exc

    try:
        if use_kwargs:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD or "",
                connect_timeout=POSTGRES_CONNECT_TIMEOUT,
            )
        else:
            conn = psycopg2.connect(dsn, connect_timeout=POSTGRES_CONNECT_TIMEOUT)
        register_default_jsonb(conn, loads=json.loads)
        return conn
    except UnicodeDecodeError as exc:
        raise RuntimeError(
            "Postgres connection failed due to non-UTF8 locale. "
            "请确认数据库可连接、账号密码正确，并在系统环境中设置 PGCLIENTENCODING=UTF8。"
        ) from exc
    except psycopg2.Error as exc:
        if not POSTGRES_AUTO_CREATE_DB:
            raise
        if not POSTGRES_DB or not POSTGRES_HOST or not POSTGRES_USER:
            raise
        if exc.pgcode != errorcodes.INVALID_CATALOG_NAME:
            raise

        admin_conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_ADMIN_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD or "",
            connect_timeout=POSTGRES_CONNECT_TIMEOUT,
        )
        try:
            admin_conn.autocommit = True
            with admin_conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (POSTGRES_DB,))
                if not cur.fetchone():
                    cur.execute(f'CREATE DATABASE "{POSTGRES_DB}"')
        finally:
            admin_conn.close()

        if use_kwargs:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD or "",
                connect_timeout=POSTGRES_CONNECT_TIMEOUT,
            )
        else:
            conn = psycopg2.connect(dsn, connect_timeout=POSTGRES_CONNECT_TIMEOUT)
        register_default_jsonb(conn, loads=json.loads)
        return conn


def _pg_init() -> None:
    global _pg_inited
    if _pg_inited:
        return
    with _pg_lock:
        if _pg_inited:
            return
        try:
            import psycopg2
            from psycopg2 import sql
        except ImportError as exc:
            raise RuntimeError("psycopg2-binary is not installed") from exc

        conn = _pg_connect()
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(POSTGRES_SCHEMA)
                ))
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.user_state (
                            user_id TEXT PRIMARY KEY,
                            state JSONB NOT NULL,
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    ).format(sql.Identifier(POSTGRES_SCHEMA))
                )
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.chat_history (
                            id BIGSERIAL PRIMARY KEY,
                            user_id TEXT NOT NULL,
                            role TEXT NOT NULL,
                            content TEXT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    ).format(sql.Identifier(POSTGRES_SCHEMA))
                )
                cur.execute(
                    sql.SQL(
                        """
                        CREATE INDEX IF NOT EXISTS chat_history_user_id_id
                        ON {}.chat_history (user_id, id DESC)
                        """
                    ).format(sql.Identifier(POSTGRES_SCHEMA))
                )
        conn.close()
        _pg_inited = True


def get_state(user_id: str) -> dict:
    '''
    功能：
    从内存存储读取用户状态，不存在则返回默认状态。

    :param user_id: 用户唯一标识
    :type user_id: str
    :return: 用户状态字典
    :rtype: dict
    '''
    if _use_postgres():
        _pg_init()
        conn = _pg_connect()
        try:
            from psycopg2 import sql
        except ImportError as exc:
            conn.close()
            raise RuntimeError("psycopg2-binary is not installed") from exc
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT state FROM {}.user_state WHERE user_id=%s").format(
                        sql.Identifier(POSTGRES_SCHEMA)
                    ),
                    (user_id,),
                )
                row = cur.fetchone()
        conn.close()
        if row and row[0]:
            return clone_state(row[0])
        return default_state(user_id)

    with _store_lock:
        return clone_state(_store.get(user_id, default_state(user_id)))


def set_state(state: dict) -> None:
    '''
    功能：
    写入或更新用户状态到内存存储。

    :param state: 用户状态字典
    :type state: dict
    :return: 无
    :rtype: None
    '''
    if _use_postgres():
        _pg_init()
        conn = _pg_connect()
        try:
            from psycopg2 import sql
            from psycopg2.extras import Json
        except ImportError as exc:
            conn.close()
            raise RuntimeError("psycopg2-binary is not installed") from exc
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {}.user_state (user_id, state, updated_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (user_id)
                        DO UPDATE SET state=EXCLUDED.state, updated_at=NOW()
                        """
                    ).format(sql.Identifier(POSTGRES_SCHEMA)),
                    (state["user_id"], Json(state)),
                )
        conn.close()
        return

    with _store_lock:
        _store[state["user_id"]] = state.copy()


def get_chat_history(user_id: str) -> List[dict]:
    '''
    功能：
    获取用户聊天历史，返回浅拷贝列表。

    :param user_id: 用户唯一标识
    :type user_id: str
    :return: 聊天历史列表
    :rtype: List[dict]
    '''
    if _use_postgres():
        _pg_init()
        conn = _pg_connect()
        try:
            from psycopg2 import sql
        except ImportError as exc:
            conn.close()
            raise RuntimeError("psycopg2-binary is not installed") from exc
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        SELECT role, content
                        FROM {}.chat_history
                        WHERE user_id=%s
                        ORDER BY id DESC
                        LIMIT %s
                        """
                    ).format(sql.Identifier(POSTGRES_SCHEMA)),
                    (user_id, _CHAT_MAX_TURNS * 2),
                )
                rows = cur.fetchall() or []
        conn.close()
        history = [{"role": row[0], "content": row[1]} for row in rows]
        history.reverse()
        return history

    with _store_lock:
        return list(_chat_store.get(user_id, []))


def append_chat_history(user_id: str, role: str, content: str) -> None:
    '''
    功能：
    追加用户聊天历史，并限制最大轮数。

    :param user_id: 用户唯一标识
    :type user_id: str
    :param role: 角色（user/ai/system）
    :type role: str
    :param content: 内容
    :type content: str
    :return: 无
    :rtype: None
    '''
    if _use_postgres():
        _pg_init()
        conn = _pg_connect()
        try:
            from psycopg2 import sql
        except ImportError as exc:
            conn.close()
            raise RuntimeError("psycopg2-binary is not installed") from exc
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        "INSERT INTO {}.chat_history (user_id, role, content) VALUES (%s, %s, %s)"
                    ).format(sql.Identifier(POSTGRES_SCHEMA)),
                    (user_id, role, content),
                )
                cur.execute(
                    sql.SQL(
                        """
                        DELETE FROM {}.chat_history
                        WHERE user_id=%s AND id NOT IN (
                            SELECT id FROM {}.chat_history
                            WHERE user_id=%s
                            ORDER BY id DESC
                            LIMIT %s
                        )
                        """
                    ).format(sql.Identifier(POSTGRES_SCHEMA), sql.Identifier(POSTGRES_SCHEMA)),
                    (user_id, user_id, _CHAT_MAX_TURNS * 2),
                )
        conn.close()
        return

    item = {"role": role, "content": content}
    with _store_lock:
        history = _chat_store.get(user_id, [])
        history.append(item)
        if len(history) > _CHAT_MAX_TURNS * 2:
            history = history[-_CHAT_MAX_TURNS * 2 :]
        _chat_store[user_id] = history
