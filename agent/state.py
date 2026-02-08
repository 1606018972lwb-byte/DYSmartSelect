# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict


def utc_now() -> str:
    '''
    功能：
    获取当前 UTC 时间的 ISO 字符串。

    :return: ISO 时间字符串
    :rtype: str
    '''
    return datetime.utcnow().isoformat()


def default_state(user_id: str) -> Dict[str, Any]:
    '''
    功能：
    构造用户的初始状态结构。

    :param user_id: 用户唯一标识
    :type user_id: str
    :return: 初始状态字典
    :rtype: Dict[str, Any]
    '''
    return {
        "user_id": user_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "onboarding_step": 0,
        "account_stage": "explore",
        "daily_slots": 1,
        "last_reco": None,
        "avoid_pool": [],
        "defer_pool": [],
        "stats": {
            "success": 0,
            "fail": 0,
            "consecutive_fail": 0,
            "env_trigger_count": 0,
        },
        "history": [],
    }


def clone_state(state: Dict[str, Any]) -> Dict[str, Any]:
    '''
    功能：
    深拷贝状态，避免引用被外部修改。

    :param state: 用户状态字典
    :type state: Dict[str, Any]
    :return: 深拷贝后的状态字典
    :rtype: Dict[str, Any]
    '''
    return json.loads(json.dumps(state, ensure_ascii=False))
