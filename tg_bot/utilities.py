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
    def __init__(self, auth_url: str, username: str, password: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_url: str = auth_url # e.g. https://app:8443/token
        self.username: str = username
        self.password: str = password
        self.expire_in: int = int(os.getenv("AUTH_EXPIRATION"))
        self.updated_at: float = 0

        self.access_token: str = None # = asyncio.run(self.authCustom())

    async def authCustom(self):
        """returns actual Bearer token"""

        if self.updated_at + self.expire_in <= time.time():

            try:
                resp = await super().request(
                    "POST",
                    self.auth_url,
                    data={
                        "username": self.username,
                        "password": self.password,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                resp_json = resp.json()
                if not "access_token" in resp_json:
                    raise Exception(resp_json)

                self.updated_at = time.time()

                self.access_token = resp_json["access_token"]

            except httpx.ConnectError as ex:
                logging.error("Most possibly, requested server is not responding.")
                logging.error(ex)
                raise Exception(f"Most possibly, requested server is not responding. Original exception: {ex}")

            except Exception as ex:
                logging.error(ex)
                raise ex

        return self.access_token

    async def request(
        self,
        # need_auth: bool = True,
        *args,
        **kwargs
    ) -> Response:
        access_token = await self.authCustom()

        if not ("headers" in kwargs) or kwargs["headers"] is None:
            kwargs["headers"] = {}
        kwargs["headers"]["Authorization"] = f"Bearer {access_token}"

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