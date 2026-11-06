from typing import Annotated, Optional

from fastapi import status, HTTPException, Depends, APIRouter, Response

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import VoteORMModel, PostORMModel
from ..oauth2 import get_current_user
from ..schemas import VoteUpdateSchema, VoteResponseSchema
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
async def vote(
    vote: VoteUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[str, Depends(get_current_user)]
):

    vote_orm = await db.get(VoteORMModel, (vote.post_id, current_user.id))
    post_orm = await db.get(PostORMModel, vote.post_id)
    if post_orm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id = {vote.post_id} was not found",
        )

    if vote.dir == 1:
        if vote_orm:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User {current_user.id} has already voted on post {vote.post_id}"
            )

        new_vote_orm = VoteORMModel(
            post_id=vote.post_id,
            user_id=current_user.id
        )
        db.add(new_vote_orm)

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        await db.refresh(new_vote_orm)
        return new_vote_orm

    elif vote.dir == 0:
        if vote_orm is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vote from user {current_user.id} on post {vote.post_id} was not found"
            )

        await db.delete(vote_orm)
        await db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=VoteResponseSchema,
)
async def create_vote(
        vote: VoteResponseSchema,
        db: Annotated[AsyncSession, Depends(get_async_db)],
        current_user: Annotated[str, Depends(get_current_user)]
):
    vote_orm = VoteORMModel(
        post_id=vote.post_id,
        user_id=current_user.id
    )
    db.add(vote_orm)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(vote_orm)
    return vote_orm


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vote(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[str, Depends(get_current_user)]
):
    vote_orm = await db.get(VoteORMModel, id)
    if vote_orm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id = {id} was not found"
        )
    if vote_orm.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to delete this post"
        )

    await db.delete(vote_orm)
    await db.commit()
