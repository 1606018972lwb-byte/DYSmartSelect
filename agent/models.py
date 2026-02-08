# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DecisionRequest(BaseModel):
    user_id: str
    category: str = Field(..., pattern="^(top|pants|outer|set)$")
    price_band: str
    account_stage: str = Field(..., pattern="^(explore|converge)$")
    daily_slots: int = Field(..., ge=1, le=3)
    in_stock: bool
    notes: Optional[str] = None


class FeedbackRequest(BaseModel):
    user_id: str
    decision_id: Optional[str] = None
    outcome: str = Field(..., pattern="^(no_volume|some_volume|scaled)$")
