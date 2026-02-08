# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any, Dict

from langchain_core.tools import tool


@tool
def get_draft_decision(payload: Dict[str, Any]) -> str:
    '''
    功能：
    将决策草案序列化为 JSON，供 Agent 工具调用。

    :param payload: 决策草案的结构化数据
    :type payload: Dict[str, Any]
    :return: JSON 字符串
    :rtype: str
    '''

    return json.dumps(payload, ensure_ascii=False)
