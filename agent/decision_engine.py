# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .config import CANDIDATE_POOL, TEMPLATES
from .models import DecisionRequest
from .state import utc_now


def parse_price_mid(price_band: str) -> int:
    '''
    功能：
    从价格区间字符串计算中位价，用于粗略匹配价位。

    :param price_band: 价格区间字符串（如 "79-129"）
    :type price_band: str
    :return: 价格区间的中位整数，解析失败时返回默认值
    :rtype: int
    '''
    try:
        parts = price_band.split("-")
        low = int(parts[0])
        high = int(parts[1])
        return (low + high) // 2
    except Exception:
        return 100


def season_now() -> str:
    '''
    功能：
    根据当前 UTC 月份返回季节标签。

    :return: 季节标签（winter/spring/summer/autumn）
    :rtype: str
    '''
    month = datetime.utcnow().month
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


def hard_filters(
    req: DecisionRequest, candidate: Dict[str, Any]
) -> Tuple[Optional[str], Optional[str]]:
    '''
    功能：
    根据硬规则判定候选方向是否需要暂缓或回避。

    :param req: 用户请求参数
    :type req: DecisionRequest
    :param candidate: 候选方向信息
    :type candidate: Dict[str, Any]
    :return: (状态, 原因)，状态为 defer/avoid 或 None
    :rtype: Tuple[Optional[str], Optional[str]]
    '''
    if not req.in_stock and req.daily_slots <= 1:
        return "avoid", "库存不足且当日名额有限"

    if "return_risk" in candidate["risk_tags"] and req.account_stage == "explore":
        return "avoid", "退货风险偏高，探索期不建议"

    if "homogeneous" in candidate["risk_tags"] and req.account_stage == "explore":
        return "defer", "同质化高，探索期先避开"

    return None, None


def timing_heuristic(candidate: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    '''
    功能：
    根据季节判断是否需要暂缓该方向。

    :param candidate: 候选方向信息
    :type candidate: Dict[str, Any]
    :return: (状态, 原因)，状态为 defer 或 None
    :rtype: Tuple[Optional[str], Optional[str]]
    '''
    now_season = season_now()
    if candidate["season"] != now_season:
        return "defer", "季节不匹配，时机不足"
    return None, None


def score_candidate(req: DecisionRequest, candidate: Dict[str, Any]) -> int:
    '''
    功能：
    对候选方向进行规则打分，用于排序选择。

    :param req: 用户请求参数
    :type req: DecisionRequest
    :param candidate: 候选方向信息
    :type candidate: Dict[str, Any]
    :return: 分数（越高越优）
    :rtype: int
    '''
    score = 50
    if req.category in candidate["categories"]:
        score += 15

    price_mid = parse_price_mid(req.price_band)
    score -= min(abs(candidate["price_mid"] - price_mid) // 10, 10)

    if req.account_stage == candidate["stage_fit"]:
        score += 10
    else:
        score -= 5

    if req.in_stock:
        score += 5
    if req.daily_slots == 1:
        score -= 3

    if "return_risk" in candidate["risk_tags"]:
        score -= 5
    if "homogeneous" in candidate["risk_tags"]:
        score -= 3

    return score


def choose_primary_risk(candidate: Dict[str, Any], env_trigger: bool) -> str:
    '''
    功能：
    选择主要风险类型（环境优先，其次产品/内容/阶段）。

    :param candidate: 候选方向信息
    :type candidate: Dict[str, Any]
    :param env_trigger: 是否触发环境不利
    :type env_trigger: bool
    :return: 风险类型标识（env/product/content/stage）
    :rtype: str
    '''
    if env_trigger:
        return "env"
    if "return_risk" in candidate["risk_tags"]:
        return "product"
    if "homogeneous" in candidate["risk_tags"]:
        return "content"
    return "stage"


def env_unfavorable(state: Dict[str, Any]) -> bool:
    '''
    功能：
    基于最近 7 天失败情况判断是否环境不利。

    :param state: 用户状态
    :type state: Dict[str, Any]
    :return: 是否触发环境不利
    :rtype: bool
    '''
    history = state.get("history", [])
    if not history:
        return False

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent = [
        r
        for r in history
        if r.get("ts") and datetime.fromisoformat(r["ts"]) >= seven_days_ago
    ]

    recent_fail = [r for r in recent if r.get("outcome") == "no_volume"]
    if len(recent_fail) < 3:
        return False

    labels = {r.get("label") for r in recent_fail if r.get("label")}
    if len(labels) < 2:
        return False

    if state.get("stats", {}).get("env_trigger_count", 0) >= 1:
        return False

    return True


def apply_pool_item(pool: List[Dict[str, Any]], item: Dict[str, Any]) -> None:
    '''
    功能：
    将条目追加到回避池/暂缓池。

    :param pool: 池列表
    :type pool: List[Dict[str, Any]]
    :param item: 要追加的条目
    :type item: Dict[str, Any]
    :return: 无
    :rtype: None
    '''
    pool.append(item)


def ensure_dont_do(
    avoid_pool: List[Dict[str, Any]],
    defer_pool: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    '''
    功能：
    构造不拍清单，优先使用历史回避/暂缓池补足到 2~3 项。

    :param avoid_pool: 回避池
    :type avoid_pool: List[Dict[str, Any]]
    :param defer_pool: 暂缓池
    :type defer_pool: List[Dict[str, Any]]
    :param candidates: 候选方向列表
    :type candidates: List[Dict[str, Any]]
    :return: 不拍清单条目列表
    :rtype: List[Dict[str, Any]]
    '''
    items: List[Dict[str, Any]] = []
    for it in avoid_pool[-2:]:
        items.append({
            "label": it["label"],
            "status": "avoid",
            "reason": it["reason"],
        })
    for it in defer_pool[-2:]:
        if len(items) >= 3:
            break
        items.append({
            "label": it["label"],
            "status": "defer",
            "reason": it["reason"],
        })

    if len(items) < 2:
        for c in candidates:
            if len(items) >= 2:
                break
            items.append({
                "label": c["label"],
                "status": "defer",
                "reason": TEMPLATES["dont_do"]["defer"],
            })

    if len(items) < 3 and candidates:
        items.append({
            "label": candidates[-1]["label"],
            "status": "avoid",
            "reason": TEMPLATES["dont_do"]["avoid"],
        })

    return items[:3]


def rule_decision(
    req: DecisionRequest, state: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Any], List[str]]:
    '''
    功能：
    按规则完成候选筛选、评分选择与输出组装，并更新用户状态。

    :param req: 用户请求参数
    :type req: DecisionRequest
    :param state: 当前用户状态
    :type state: Dict[str, Any]
    :return: (决策输出, 更新后的状态, 触发规则列表)
    :rtype: Tuple[Dict[str, Any], Dict[str, Any], List[str]]
    '''
    mode = "best" if state["onboarding_step"] < 2 else "only"
    rules_fired: List[str] = []

    candidates = [c for c in CANDIDATE_POOL if req.category in c["categories"]]
    if not candidates:
        candidates = CANDIDATE_POOL[:]

    avoid_pool = state.get("avoid_pool", [])
    defer_pool = state.get("defer_pool", [])

    scored: List[Tuple[int, Dict[str, Any]]] = []
    filtered: List[Dict[str, Any]] = []

    for c in candidates:
        status, reason = hard_filters(req, c)
        if status:
            rules_fired.append(f"hard_filter:{status}")
            if status == "avoid":
                apply_pool_item(avoid_pool, {
                    "label": c["label"],
                    "reason": reason,
                    "ts": utc_now(),
                })
            else:
                apply_pool_item(defer_pool, {
                    "label": c["label"],
                    "reason": reason,
                    "ts": utc_now(),
                })
            continue

        t_status, t_reason = timing_heuristic(c)
        if t_status:
            rules_fired.append(f"timing:{t_status}")
            apply_pool_item(defer_pool, {
                "label": c["label"],
                "reason": t_reason,
                "ts": utc_now(),
            })
            continue

        filtered.append(c)
        scored.append((score_candidate(req, c), c))

    if not scored:
        scored = [(score_candidate(req, c), c) for c in candidates]
        rules_fired.append("fallback:no_filtered")

    scored.sort(key=lambda x: x[0], reverse=True)
    top_score, top_candidate = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else top_score

    confidence_style = "strong" if (top_score - second_score) >= 8 else "conservative"
    if not req.in_stock:
        confidence_style = "conservative"

    env_trigger = env_unfavorable(state)
    if env_trigger:
        rules_fired.append("env_unfavorable")

    primary_risk = choose_primary_risk(top_candidate, env_trigger)

    decision_id = uuid.uuid4().hex

    headline = TEMPLATES["headline"][mode]
    action = TEMPLATES["action"][confidence_style]
    reason_one_line = TEMPLATES["reason"][confidence_style]
    if env_trigger:
        reason_one_line = "最近环境偏冷，先稳住节奏"

    dont_do = ensure_dont_do(avoid_pool, defer_pool, filtered or candidates)

    output = {
        "decision_id": decision_id,
        "headline": headline,
        "action": action,
        "reason_one_line": reason_one_line,
        "primary_risk": TEMPLATES["risk"][primary_risk],
        "why_it": [
            f"类目匹配：{req.category}",
            f"价位贴近：{req.price_band}",
            f"阶段匹配：{req.account_stage}",
        ],
        "dont_do": dont_do,
        "failure_expectation": {
            "likely": primary_risk,
            "next_action": TEMPLATES["failure_next"][primary_risk],
        },
        "meta": {
            "mode": mode,
            "confidence_style": confidence_style,
            "rules_fired": rules_fired,
            "state_snapshot_version": state["onboarding_step"],
        },
    }

    state["onboarding_step"] = state.get("onboarding_step", 0) + 1
    state["account_stage"] = req.account_stage
    state["daily_slots"] = req.daily_slots
    state["updated_at"] = utc_now()

    last_reco = {
        "decision_id": decision_id,
        "label": top_candidate["label"],
        "ts": utc_now(),
        "category": req.category,
        "price_band": req.price_band,
        "in_stock": req.in_stock,
    }
    state["last_reco"] = last_reco

    history = state.get("history", [])
    history.append({
        "ts": utc_now(),
        "decision_id": decision_id,
        "label": top_candidate["label"],
        "category": req.category,
        "price_band": req.price_band,
        "in_stock": req.in_stock,
        "decision": confidence_style,
        "outcome": None,
    })
    state["history"] = history[-30:]

    if env_trigger:
        state.setdefault("stats", {}).setdefault("env_trigger_count", 0)
        state["stats"]["env_trigger_count"] += 1
    else:
        if "stats" in state:
            state["stats"]["env_trigger_count"] = 0

    state["avoid_pool"] = avoid_pool[-30:]
    state["defer_pool"] = defer_pool[-30:]

    return output, state, rules_fired
