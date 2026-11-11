from typing import Annotated

from fastapi import status, HTTPException, Depends, APIRouter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import UserORMModel, VoteORMModel, PostORMModel
from ..oauth2 import get_current_user
from ..schemas import VoteCreateSchema, VoteResponseSchema
from ..database import get_async_db


router = APIRouter(
    prefix="/vote",
    tags=["vote"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=VoteResponseSchema,
)
async def create_vote(
    vote: VoteCreateSchema,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[UserORMModel, Depends(get_current_user)]
):
    post_orm = await db.get(PostORMModel, vote.post_id)
    if post_orm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id = {vote.post_id} was not found",
        )

    existing_vote = await db.get(VoteORMModel, (vote.post_id, current_user.id))
    if existing_vote:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {current_user.id} has already liked post {vote.post_id}"
        )

    new_vote = VoteORMModel(
        post_id=vote.post_id,
        user_id=current_user.id
    )
    db.add(new_vote)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(new_vote)
    return new_vote


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_vote(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[UserORMModel, Depends(get_current_user)]
):
    vote_orm = await db.get(VoteORMModel, (post_id, current_user.id))

    if vote_orm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vote for post {post_id} was not found"
        )

    await db.delete(vote_orm)
    await db.commit()