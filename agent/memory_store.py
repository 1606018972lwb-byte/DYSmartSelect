# -*- coding: utf-8 -*-
from __future__ import annotations

import threading
from typing import Dict

from .state import default_state

_store_lock = threading.Lock()
_store: Dict[str, dict] = {}


def get_state(user_id: str) -> dict:
    '''
    功能：
    从内存存储读取用户状态，不存在则返回默认状态。

    :param user_id: 用户唯一标识
    :type user_id: str
    :return: 用户状态字典
    :rtype: dict
    '''
    with _store_lock:
        return _store.get(user_id, default_state(user_id)).copy()


def set_state(state: dict) -> None:
    '''
    功能：
    写入或更新用户状态到内存存储。

    :param state: 用户状态字典
    :type state: dict
    :return: 无
    :rtype: None
    '''
    with _store_lock:
        _store[state["user_id"]] = state.copy()
