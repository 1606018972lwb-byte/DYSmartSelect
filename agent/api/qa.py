# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from flask import Flask, jsonify, request

from ..llm_agent import run_qa
from ..memory_store import append_chat_history, get_chat_history
from .routes import QA_FLASK_API


def register_qa_routes(app: Flask) -> None:
    '''
    功能：
    注册简单问答 API 路由。

    :param app: Flask 应用实例
    :type app: Flask
    :return: 无
    :rtype: None
    '''

    @app.post(QA_FLASK_API)
    def qa() -> Any:
        '''
        功能：
        接收问题并返回模型回答。

        :return: Flask JSON Response
        :rtype: Any
        '''
        payload: Dict[str, Any] = request.get_json(silent=True) or {}
        question = str(payload.get("question", "")).strip()
        user_id = str(payload.get("user_id", "guest")).strip() or "guest"
        if not question:
            return jsonify({"error": "question_required"}), 400

        history = get_chat_history(user_id)
        answer = run_qa(question, history=history)
        append_chat_history(user_id, "user", question)
        append_chat_history(user_id, "ai", answer)
        return jsonify({"question": question, "answer": answer, "user_id": user_id})
