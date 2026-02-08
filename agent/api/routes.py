# -*- coding: utf-8 -*-
from __future__ import annotations

import os


def _load_routes(path: str) -> dict:
    '''
    功能：
    从 .routes 文件读取路由配置（key=value）。

    :param path: 配置文件路径
    :type path: str
    :return: 路由配置字典
    :rtype: dict
    '''
    data = {}
    if not os.path.exists(path):
        return data
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


_routes_path = os.path.join(os.path.dirname(__file__), ".routes")
_routes = _load_routes(_routes_path)

INDEX_ROUTE = _routes.get("INDEX_ROUTE", "/")
DECISION_PAGE_ROUTE = _routes.get("DECISION_PAGE_ROUTE", "/decision")
CHAT_ROUTE = _routes.get("CHAT_ROUTE", "/chat")
DECISION_FLASK_API = _routes.get("DECISION_FLASK_API", "/v1/decision")
FEEDBACK_FLASK_API = _routes.get("FEEDBACK_FLASK_API", "/v1/feedback")
QA_FLASK_API = _routes.get("QA_FLASK_API", "/v1/qa")
