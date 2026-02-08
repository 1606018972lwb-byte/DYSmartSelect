# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

APP_VERSION = os.getenv("APP_VERSION", "0.260208.07")
LLM_BASE_URL = os.getenv("BASE_URL", "")
LLM_MODEL = os.getenv("MODEL", "")
LLM_MODEL_API = os.getenv("MODEL_API", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

TEMPLATES = {
    "headline": {
        "best": "今日最优选择",
        "only": "今天只建议拍这一款",
    },
    "action": {
        "strong": "按当前节奏直接上架并观察24小时",
        "conservative": "先小量测试，控制成本观察反馈",
    },
    "reason": {
        "strong": "趋势窗口清晰，试错成本低",
        "conservative": "阶段稳妥，先验证再放量",
    },
    "risk": {
        "env": "环境不利，别急于放量",
        "content": "内容承接可能偏弱",
        "product": "产品差异度不足",
        "stage": "当前阶段匹配度低",
    },
    "failure_next": {
        "env": "先换时段与内容结构，再做一次小测",
        "content": "优化主图/视频前3秒再复测",
        "product": "调整卖点或换同价位差异款",
        "stage": "回到基础款测试，等数据稳定再进阶",
    },
    "dont_do": {
        "defer": "阶段或时机不合适，先等等",
        "avoid": "高风险方向，暂时回避",
    },
}

CANDIDATE_POOL = [
    {
        "label": "基础短袖T恤",
        "categories": ["top"],
        "price_mid": 69,
        "season": "spring",
        "stage_fit": "explore",
        "risk_tags": ["homogeneous"],
    },
    {
        "label": "修身针织上衣",
        "categories": ["top"],
        "price_mid": 119,
        "season": "spring",
        "stage_fit": "converge",
        "risk_tags": ["return_risk"],
    },
    {
        "label": "阔腿休闲裤",
        "categories": ["pants"],
        "price_mid": 129,
        "season": "spring",
        "stage_fit": "explore",
        "risk_tags": [],
    },
    {
        "label": "直筒牛仔裤",
        "categories": ["pants"],
        "price_mid": 159,
        "season": "spring",
        "stage_fit": "converge",
        "risk_tags": ["homogeneous"],
    },
    {
        "label": "短款风衣",
        "categories": ["outer"],
        "price_mid": 199,
        "season": "spring",
        "stage_fit": "converge",
        "risk_tags": [],
    },
    {
        "label": "轻薄棒球夹克",
        "categories": ["outer"],
        "price_mid": 169,
        "season": "spring",
        "stage_fit": "explore",
        "risk_tags": [],
    },
    {
        "label": "针织套装",
        "categories": ["set"],
        "price_mid": 199,
        "season": "spring",
        "stage_fit": "converge",
        "risk_tags": ["return_risk"],
    },
    {
        "label": "运动休闲套装",
        "categories": ["set"],
        "price_mid": 159,
        "season": "spring",
        "stage_fit": "explore",
        "risk_tags": ["homogeneous"],
    },
    {
        "label": "修身长袖打底",
        "categories": ["top"],
        "price_mid": 79,
        "season": "spring",
        "stage_fit": "explore",
        "risk_tags": [],
    },
    {
        "label": "加绒卫衣",
        "categories": ["top"],
        "price_mid": 129,
        "season": "winter",
        "stage_fit": "explore",
        "risk_tags": ["season_mismatch"],
    },
    {
        "label": "轻薄羽绒马甲",
        "categories": ["outer"],
        "price_mid": 239,
        "season": "winter",
        "stage_fit": "converge",
        "risk_tags": ["season_mismatch"],
    },
    {
        "label": "高腰A字半裙",
        "categories": ["pants"],
        "price_mid": 119,
        "season": "spring",
        "stage_fit": "explore",
        "risk_tags": [],
    },
]
