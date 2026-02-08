# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os

from flask import Flask

from ..config import APP_VERSION
from .decision import register_decision_routes
from .feedback import register_feedback_routes
from .pages import register_page_routes
from .qa import register_qa_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("agent")

_base_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
_templates_dir = os.path.join(_base_dir, "templates")
app = Flask(__name__, template_folder=_templates_dir)
app.config["APP_VERSION"] = APP_VERSION

register_page_routes(app)
register_decision_routes(app)
register_feedback_routes(app)
register_qa_routes(app)
logger.info("registered routes: %s", app.url_map)
