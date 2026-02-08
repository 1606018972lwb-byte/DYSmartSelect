# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from flask import Flask, jsonify, request

from .routes import DECISION_FLASK_API
from ..decision_engine import rule_decision
from ..llm_agent import run_langchain_agent
from ..memory_store import get_state, set_state
from ..models import DecisionRequest


def _parse_pydantic(model_cls, payload: Dict[str, Any]):
    '''
    功能：
    将请求体解析为 Pydantic 模型，并返回错误信息。

    :param model_cls: Pydantic 模型类
    :type model_cls: Any
    :param payload: 请求体 JSON
    :type payload: Dict[str, Any]
    :return: (模型实例, 错误信息)
    :rtype: Any
    '''
    try:
        return model_cls(**payload), None
    except Exception as exc:
        return None, str(exc)


def register_decision_routes(app: Flask) -> None:
    '''
    功能：
    注册决策相关 API 路由。

    :param app: Flask 应用实例
    :type app: Flask
    :return: 无
    :rtype: None
    '''

    @app.post(DECISION_FLASK_API)
    def decision() -> Any:
        '''
        功能：
        生成选品决策，返回统一结构的 JSON 响应。

        :return: Flask JSON Response
        :rtype: Any
        '''
        payload = request.get_json(silent=True) or {}
        req, err = _parse_pydantic(DecisionRequest, payload)
        if err:
            return jsonify({"error": "invalid_request", "detail": err}), 400

        state = get_state(req.user_id)

        draft, updated_state, rules_fired = rule_decision(req, state)
        final_output, agent_flags = run_langchain_agent(draft)

        set_state(updated_state)

        app.logger.info(
            "decision user_id=%s decision_id=%s mode=%s confidence=%s rules=%s agent=%s",
            req.user_id,
            final_output.get("decision_id"),
            final_output.get("meta", {}).get("mode"),
            final_output.get("meta", {}).get("confidence_style"),
            rules_fired,
            agent_flags,
        )

        return jsonify(final_output)
