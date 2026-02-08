# -*- coding: utf-8 -*-
from __future__ import annotations

import sqlite3

from .config import DB_PATH


def get_conn() -> sqlite3.Connection:
    '''
    功能：
    创建并返回 SQLite 连接（带 Row 工厂）。

    :return: SQLite 连接对象
    :rtype: sqlite3.Connection
    '''
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    '''
    功能：
    初始化用户状态表结构（如果不存在则创建）。

    :return: 无
    :rtype: None
    '''
    conn = get_conn()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_state (
                user_id TEXT PRIMARY KEY,
                created_at TEXT,
                updated_at TEXT,
                onboarding_step INTEGER,
                account_stage TEXT,
                daily_slots INTEGER,
                last_reco TEXT,
                avoid_pool TEXT,
                defer_pool TEXT,
                stats TEXT,
                history TEXT
            )
            """
        )
    conn.close()
