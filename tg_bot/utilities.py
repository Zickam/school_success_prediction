from __future__ import annotations

import os
import time
import logging
import typing
from typing import Callable
from functools import wraps
import asyncio

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

import httpx
from httpx import AsyncClient, URL, USE_CLIENT_DEFAULT, Response

class CustomAsyncClient(AsyncClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def request(
        self,
        *args,
        **kwargs
    ) -> Response:
        if not ("headers" in kwargs) or kwargs["headers"] is None:
            kwargs["headers"] = {}

        response = await super().request(*args, **kwargs)

        if 200 <= response.status_code < 300:
            logging.debug(f"status_code: {response.status_code} response.text: {response.text}")
        elif 300 <= response.status_code < 400:
            logging.debug(f"status_code: {response.status_code} response.text: {response.text}")
        elif 400 <= response.status_code < 500:
            logging.info(f"status_code: {response.status_code} response.text: {response.text}")
        elif 500 <= response.status_code < 600:
            logging.error(f"status_code: {response.status_code} response.text: {response.text}")
        else:
            logging.warning(f"status_code: {response.status_code} response.text: {response.text}")

        return response