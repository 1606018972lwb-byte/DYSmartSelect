# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from flask import Flask, jsonify, request

from .routes import FEEDBACK_FLASK_API
from ..memory_store import get_state, set_state
from ..models import FeedbackRequest
from ..state import utc_now


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


def register_feedback_routes(app: Flask) -> None:
    '''
    功能：
    注册反馈相关 API 路由。

    :param app: Flask 应用实例
    :type app: Flask
    :return: 无
    :rtype: None
    '''

    @app.post(FEEDBACK_FLASK_API)
    def feedback() -> Any:
        '''
        功能：
        接收反馈并更新用户状态与统计信息。

        :return: Flask JSON Response
        :rtype: Any
        '''
        payload = request.get_json(silent=True) or {}
        req, err = _parse_pydantic(FeedbackRequest, payload)
        if err:
            return jsonify({"error": "invalid_request", "detail": err}), 400

        state = get_state(req.user_id)
        if not state:
            return jsonify({"error": "not_found"}), 404

        decision_id = req.decision_id
        if not decision_id:
            if state.get("last_reco"):
                decision_id = state["last_reco"].get("decision_id")
                weak_link = True
            else:
                return jsonify({"error": "decision_id_required"}), 400
        else:
            weak_link = False

        history = state.get("history", [])
        for record in reversed(history):
            if record.get("decision_id") == decision_id:
                record["outcome"] = req.outcome
                break

        stats = state.get("stats", {})
        if req.outcome in ("scaled", "some_volume"):
            stats["success"] = stats.get("success", 0) + 1
            stats["consecutive_fail"] = 0
        else:
            stats["fail"] = stats.get("fail", 0) + 1
            stats["consecutive_fail"] = stats.get("consecutive_fail", 0) + 1

        state["stats"] = stats
        state["history"] = history[-30:]
        state["updated_at"] = utc_now()

        set_state(state)

        app.logger.info(
            "feedback user_id=%s decision_id=%s outcome=%s weak_link=%s",
            req.user_id,
            decision_id,
            req.outcome,
            weak_link,
        )

        return jsonify(
            {
                "ok": True,
                "updated_state": {
                    "consecutive_fail": stats.get("consecutive_fail", 0),
                    "success": stats.get("success", 0),
                    "fail": stats.get("fail", 0),
                    "weak_link": weak_link,
                },
            }
        )
