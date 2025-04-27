from __future__ import annotations

import datetime
import logging
from uuid import UUID
from typing import Annotated
import os

from fastapi import APIRouter, Response, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, or_, not_

from ..db import schemas, engine
from ..db import declaration
from ..db.declaration.user import User
from ..db.schemas.user import UserCreate, User as UserSchema
from ..db.engine import getSession

router = APIRouter(tags=["User"], prefix="/user")


@router.get("", responses={404: {}}, response_model=UserSchema)
async def get_user(
    chat_id: int | None = None,
    user_uuid: UUID | None = None,
    session: AsyncSession = Depends(getSession)
):
    filters = []
    if chat_id is not None:
        filters.append(User.chat_id == chat_id)
    if user_uuid is not None:
        filters.append(User.uuid == user_uuid)

    if not filters:
        raise HTTPException(status_code=400, detail="Missing query params")

    query = select(User).where(or_(*filters))
    result = await session.execute(query)
    users = result.scalars().all()

    if len(users) == 1:
        return users[0]
    elif users:
        raise HTTPException(status_code=409, detail="Multiple users found")

    raise HTTPException(status_code=404, detail="User not found")


@router.post("", response_model=UserSchema)
async def create_user(
    user: UserCreate,
    session: AsyncSession = Depends(getSession)
):
    try:
        # Check if user with this chat_id already exists
        result = await session.execute(
            select(User).where(User.chat_id == user.chat_id)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(status_code=409, detail="User with such chat_id already exists")

        # Create new user
        new_user = User(**user.model_dump())
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        return new_user
    except Exception as e:
        await session.rollback()
        logging.error(f"Failed to create user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("", responses={404: {}})
# async def createUser(
#     user: Annotated[schemas.user.UserCreate, Depends()],
#     session: AsyncSession = Depends(engine.getSession)
# ):
#     try:
#         new_user = declaration.user.User(**user.model_dump(exclude_unset=False))
#         session.add(new_user)
#         logging.info(new_user)
#         await session.commit()
#         # await session.refresh(new_user)
#         logging.info(123123123123123123)
#         logging.info(new_user)
#         await session.begin()
#         result = await session.execute(select(declaration.user.User))
#         await session.commit()
#         logging.info(result)
#         users = result.scalars().all()
#         logging.info(users)
#         return new_user
#     except Exception as e:
#         await session.rollback()
#         logging.error("❌ Commit failed:", e)
#         raise HTTPException(status_code=500, detail=str(e))
#
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