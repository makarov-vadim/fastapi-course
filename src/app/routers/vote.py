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

# @router.get(
#     "/",
#     response_model=PostsResponseSchema,
# )
# async def get_votes(
#         db: Annotated[AsyncSession, Depends(get_async_db)],
#         current_user: Annotated[str, Depends(get_current_user)],
#         limit: int = 10,
#         skip: int = 0,
#         search: Optional[str] = None
# ):
#     stmt = select(PostORMModel)
#
#     if search:
#         stmt = stmt.where(PostORMModel.title.contains(search))
#
#     stmt = stmt.limit(limit).offset(skip)
#
#     result = await db.execute(stmt)
#     posts = result.scalars().all()
#     return posts

# @router.get(
#     "/{id}",
#     response_model=PostResponseSchema
# )
# async def get_vote(
#     id: int,
#     db: Annotated[AsyncSession, Depends(get_async_db)],
#     current_user: Annotated[str, Depends(get_current_user)]
# ):
#     result = await db.execute(
#         select(PostORMModel).where(PostORMModel.id == id)
#     )
#     post_orm = result.scalars().first()
#
#     if post_orm is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Post with id = {id} was not found"
#         )
#     return post_orm

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

# @router.put(
#     "/{id}",
#     status_code=status.HTTP_201_CREATED,
#     response_model=PostResponseSchema
# )
# async def update_vote(
#     id: int,
#     updated_post: PostCreateSchema,
#     db: Annotated[AsyncSession, Depends(get_async_db)],
#     current_user: Annotated[str, Depends(get_current_user)]
# ):
#     post_orm = await db.get(PostORMModel, id)
#     if post_orm is None:
#         raise HTTPException(
#             status_code=404,
#             detail=f"Post with id = {id} was not found"
#         )
#     if post_orm.user_id != current_user.id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail=f"Not authorized to delete this post"
#         )
#     for field, value in updated_post.model_dump().items():
#         setattr(post_orm, field, value)
#
#     try:
#         await db.commit()
#     except Exception:
#         await db.rollback()
#         raise
#
#     await db.refresh(post_orm)
#     return post_orm
