from typing import Annotated

from fastapi import status, HTTPException, Depends, APIRouter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..models import UserORMModel
from ..oauth2 import get_current_user
from ..schemas import (
    UserCreateSchema, UserResponseSchema
)
from ..database import get_async_db
from ..utils import get_password_hash

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponseSchema,
)
async def create_user(
    user: UserCreateSchema,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    user_data = user.model_dump()
    plain_password = user_data.pop("password")
    user_data["hashed_password"] = get_password_hash(plain_password)
    user_orm = UserORMModel(**user_data)
    db.add(user_orm)

    try:
        await db.commit()
    except IntegrityError:  # Ловим именно IntegrityError, а не всё подряд
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    except Exception:
        await db.rollback()
        raise
    await db.refresh(user_orm)
    return user_orm


@router.get(
    "/{id}",
    response_model=UserResponseSchema
)
async def get_user(
    id: int,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[str, Depends(get_current_user)]
):
    result = await db.execute(select(UserORMModel).where(UserORMModel.id == id))
    user_orm = result.scalars().first()

    if user_orm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id = {id} was not found"
        )
    return user_orm
