# -*- coding: utf-8 -*-
from __future__ import annotations

from flask import Flask, render_template

from .routes import CHAT_ROUTE, DECISION_PAGE_ROUTE, INDEX_ROUTE


def register_page_routes(app: Flask) -> None:
    '''
    功能：
    注册页面路由（本地操作台）。

    :param app: Flask 应用实例
    :type app: Flask
    :return: 无
    :rtype: None
    '''

    @app.get(INDEX_ROUTE)
    def index() -> str:
        '''
        功能：
        返回导航主页。

        :return: HTML 页面字符串
        :rtype: str
        '''
        return render_template("index.html")

    @app.get(DECISION_PAGE_ROUTE)
    def decision_page() -> str:
        '''
        功能：
        返回选品操作台页面。

        :return: HTML 页面字符串
        :rtype: str
        '''
        return render_template("decision.html")

    @app.get(CHAT_ROUTE)
    def chat() -> str:
        '''
        功能：
        返回 AI 对话页面。

        :return: HTML 页面字符串
        :rtype: str
        '''
        return render_template("chat.html")

    if INDEX_ROUTE != "/":
        @app.get("/")
        def index_root() -> str:
            '''
            功能：
            提供根路径回退，确保访问 / 时也能打开导航页。

            :return: HTML 页面字符串
            :rtype: str
            '''
            return render_template("index.html")
