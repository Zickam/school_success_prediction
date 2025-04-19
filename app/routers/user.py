from __future__ import annotations

import datetime
import logging
from typing import Annotated
import os

from fastapi import APIRouter
from fastapi import Response
from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..models import schemas, engine
from ..models import declaration

router = APIRouter(tags=["User"], prefix="/user")


@router.get("", response_model=schemas.user.UserRead, responses={404: {}})
async def getUser(user_id: int):
    user = declaration.user.User()
    if not user:
        return Response(status_code=404, content="User not found")
    return user

@router.post("", response_model=schemas.user.UserRead)
async def create_user(user: schemas.user.UserCreate, session: AsyncSession = Depends(engine.getSession)):
    new_user = declaration.user.User(**user.dict())
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


# @router.post("", responses={404: {}})
# async def createUser(user: Annotated[dict, Depends(pydantic_models.User_Pydantic)]):
#     user: pydantic_models.User_Pydantic
#
#     user_db = await models.user.User.get_or_none(user_id=user.user_id)
#     if user_db:
#         return Response(status_code=404, content="User already exists")
#     if user.referral_id == user.user_id:
#         return Response(status_code=404, content="User can't be its referral")
#     if user.referral_id and not await models.user.User.get_or_none(
#         user_id=user.referral_id
#     ):
#         return Response(status_code=404, content="Referral user not exists")
#
#     data = user.model_dump(exclude_unset=True, exclude_none=True)
#     await models.user.User.create(**data)
#
#     return Response(status_code=200, content="User created")
#
#
# @router.patch("", responses={404: {}})
# async def updateUser(user: Annotated[dict, Depends(pydantic_models.User_Pydantic)]):
#     user: pydantic_models.User_Pydantic
#     del user.role # admin role is always resetting because user.role="user" by default
#
#     user_db = await models.user.User.get_or_none(user_id=user.user_id)
#     if not user_db:
#         return Response(status_code=404, content="User not exists")
#     if user.referral_id == user.user_id:
#         return Response(status_code=404, content="User can't be its referral")
#     if user.referral_id and not await models.user.User.get_or_none(
#         user_id=user.referral_id
#     ):
#         return Response(status_code=404, content="Referral user not exists")
#
#     data = user.model_dump(exclude_unset=True, exclude_none=True)
#     await user_db.update_from_dict(data)
#     await user_db.save()
#
#     return Response(status_code=200, content="User updated")
#
#
# @router.delete("", responses={404: {}})
# async def deleteUser(user_id: int):
#     user = await models.user.User.get_or_none(user_id=user_id)
#     if not user:
#         return Response(status_code=404, content="User not found")
#     await user.delete()
#     return Response(status_code=200)
#
#
# @router.get("/by_username", response_model=pydantic_models.User_Pydantic, responses={404: {}})
# async def getUserByUsername(username: str):
#     user = await user_model.User.get_or_none(username=username)
#     if not user:
#         return Response(status_code=404, content="User not found")
#     return user
#
#
# @router.get(
#     "/referral/referees",
#     response_model=list[pydantic_models.User_Pydantic],
#     responses={404: {}},
# )
# async def getUserReferees(user_id: int):
#     user = await models.user.User.get_or_none(user_id=user_id)
#     if not user:
#         return Response(status_code=404, content="User not found")
#     users = await user_model.User.filter(referral_id=user.user_id)
#     return users
#
#
# @router.get("/referral/link", response_model=str, responses={404: {}})
# async def getUserReferralLink(user_id: int):
#     user = await models.user.User.get_or_none(user_id=user_id)
#     if not user:
#         return Response(status_code=404, content="User not found")
#     referral_link = f"{os.getenv('BOT_URL')}?start=_u{user_id}"
#     return referral_link
#
#
# @router.get(
#     "/subscription/active_tariff",
#     response_model=pydantic_models.Tariff_Pydantic | None,
#     responses={404: {}}
# )
# async def getActiveTariff(user_id: int):
#     user = await models.user.User.get_or_none(user_id=user_id)
#     if not user:
#         return Response(status_code=404, content="User not found")
#     if await isSubscriptionActive(user_id):
#         return await user.getActiveTariff()
#     return None
#
#
# @router.get(
#     "/subscription/last_active_tariff",
#     response_model=pydantic_models.Tariff_Pydantic,
#     responses={404: {}}
# )
# async def getLastActiveTariff(user_id: int):
#     user = await models.user.User.get_or_none(user_id=user_id)
#     if not user:
#         return Response(status_code=404, content="User not found")
#
#     last_invoice = await models.invoice.Invoice.filter(user_id=user_id).exclude(paid_at=None).order_by("-paid_at").first()
#     last_bonus_activation = await models.tariff.BonusDaysActivations.filter(user_id=user_id).order_by("-created_at").first()
#
#     if last_invoice and not last_bonus_activation:
#         tariff = await models.tariff.Tariff.get(id=last_invoice.tariff_id)
#     elif not last_invoice and last_bonus_activation:
#         tariff = await models.tariff.Tariff.get(id=last_bonus_activation.tariff_id)
#     elif not last_invoice and not last_bonus_activation:
#         raise Exception("Unexpected conditions: last_active_tariff called when there was no any active tariff so long")
#
#     if last_invoice and last_bonus_activation:
#         if last_invoice.paid_at > last_bonus_activation.created_at:
#             tariff = await models.tariff.Tariff.get(id=last_invoice.tariff_id)
#         else:
#             tariff = await models.tariff.Tariff.get(id=last_bonus_activation.tariff_id)
#
#     return tariff
#
#
# @router.get(
#     "/subscription/active_until",
#     response_model=datetime.datetime,
#     responses={404: {}}
# )
# async def getSubscriptionActiveUntil(user_id: int):
#     user = await models.user.User.get_or_none(user_id=user_id)
#     if not user:
#         return Response(status_code=404, content="User not found")
#     return await user.getSubExpiresAt()
#
#
# @router.get(
#     "/subscription/is_active",
#     response_model=bool,
#     responses={404: {}}
# )
# async def isSubscriptionActive(user_id: int):
#     user = await models.user.User.get_or_none(user_id=user_id)
#     if not user:
#         return Response(status_code=404, content="User not found")
#     return await user.isSubActive()
#
#
# # @router.get(
# #     "/subscription/link/android",
# #     response_model=str,
# #     responses={404: {}}
# # )
# # async def isSubscriptionActive(user_id: int):
# #     user = await models.user.User.get_or_none(user_id=user_id)
# #     if not user:
# #         return Response(status_code=404, content="User not found")
# #     if not await user.isSubActive():
# #         return "https://google.com"
# #     await httpx_client
# #     return