# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from langchain.agents import create_openai_functions_agent
try:
    from langchain.agents import AgentExecutor
except ImportError:  # LangChain >=0.2.15 moved AgentExecutor
    from langchain.agents.agent import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .config import LLM_BASE_URL, LLM_MODEL, LLM_MODEL_API, OPENAI_API_KEY
from .tools import get_draft_decision


def _build_llm() -> ChatOpenAI:
    '''
    功能：
    构建 OpenAI 兼容的 Chat 模型客户端。

    :return: ChatOpenAI 实例
    :rtype: ChatOpenAI
    '''
    base_url = LLM_BASE_URL or ""
    # ChatOpenAI 会自动使用 /chat/completions，
    # 这里不再拼接 MODEL_API，避免重复路径。
    return ChatOpenAI(
        model=LLM_MODEL or "",
        base_url=base_url or None,
        api_key=OPENAI_API_KEY or None,
        temperature=0.2,
    )


def run_langchain_agent(draft: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    '''
    功能：
    调用 LangChain Agent 在规则草案上生成最终决策，解析失败则回退草案。

    :param draft: 规则层生成的决策草案
    :type draft: Dict[str, Any]
    :return: (最终决策, agent 标记列表)
    :rtype: Tuple[Dict[str, Any], List[str]]
    '''
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是决策Agent。必须调用工具获取草案后再输出最终JSON。"
                "输出必须严格是JSON，不要额外文本。"
                "不要使用软弱措辞（如 可能/建议你考虑/大概）。",
            ),
            ("human", "请根据草案输出最终决策JSON。"),
        ]
    )

    llm = _build_llm()
    tool_instance = get_draft_decision.bind(payload=draft)
    agent = create_openai_functions_agent(llm, [tool_instance], prompt)
    executor = AgentExecutor(agent=agent, tools=[tool_instance], verbose=False)

    result = executor.invoke({"input": "generate"})
    text = result.get("output", "")

    try:
        parsed = json.loads(text)
        return parsed, ["agent:ok"]
    except Exception:
        return draft, ["agent:fallback"]


def _build_qa_messages(question: str, history: List[Dict[str, str]]) -> List[Any]:
    '''
    功能：
    组装聊天消息，包含简短系统提示与历史上下文。

    :param question: 用户问题
    :type question: str
    :param history: 历史消息列表
    :type history: List[Dict[str, str]]
    :return: LangChain 消息列表
    :rtype: List[Any]
    '''
    messages: List[Any] = [
        SystemMessage(
            content="你是一个简洁、专业的电商选品与经营助手。回答要直接、可执行。"
        )
    ]
    for item in history:
        role = str(item.get("role", "")).lower()
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "ai":
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=question))
    return messages


def run_qa(question: str, history: List[Dict[str, str]] | None = None) -> str:
    '''
    功能：
    执行简单问答，返回模型文本回答。

    :param question: 用户问题
    :type question: str
    :param history: 历史消息列表
    :type history: List[Dict[str, str]] | None
    :return: 模型回答文本
    :rtype: str
    '''
    llm = _build_llm()
    history = history or []
    messages = _build_qa_messages(question, history)
    response = llm.invoke(messages)
    return getattr(response, "content", str(response))
