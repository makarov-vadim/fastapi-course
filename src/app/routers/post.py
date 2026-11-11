from typing import Annotated, Optional

from fastapi import status, HTTPException, Depends, APIRouter

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PostORMModel, VoteORMModel
from ..oauth2 import get_current_user
from ..schemas import (
    PostCreateSchema, PostResponseSchema, PostsResponseSchema, PostVoteResponseSchema, PostsVoteResponseSchema
)
from ..database import get_async_db

router = APIRouter(
    prefix="/posts",
    tags=["Posts"],
)

@router.get(
    "/",
    response_model=PostsVoteResponseSchema,
)
async def get_posts(
        db: Annotated[AsyncSession, Depends(get_async_db)],
        current_user: Annotated[str, Depends(get_current_user)],
        limit: int = 10,
        skip: int = 0,
        search: Optional[str] = None
):

    stmt = (
        select(PostORMModel, func.count(VoteORMModel.post_id).label("vote_count"))
        .outerjoin(VoteORMModel, PostORMModel.id == VoteORMModel.post_id)
        .group_by(PostORMModel.id)
    )

    if search:
        stmt = stmt.where(PostORMModel.title.contains(search))
    stmt = stmt.limit(limit).offset(skip)

    result = await db.execute(stmt)
    posts = result.all()
    posts_data = []
    for post_orm, vote_count in posts:
        posts_data.append({
            "post": post_orm,
            "vote_count": vote_count
        })

    return posts_data

@router.get(
    "/{id}",
    response_model=PostVoteResponseSchema
)
async def get_post(
    id: int,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[str, Depends(get_current_user)]
):

    # Считаем количество голосов для каждого поста
    stmt = (
        select(PostORMModel, func.count(VoteORMModel.post_id).label("vote_count"))
        .outerjoin(VoteORMModel, PostORMModel.id == VoteORMModel.post_id)
        .where(PostORMModel.id == id)
        .group_by(PostORMModel.id)
    )
    result = await db.execute(stmt)
    row = result.first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id = {id} was not found"
        )
    post_orm, vote_count = row

    return {
        "post": post_orm,
        "vote_count": vote_count
    }

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=PostResponseSchema,
)
async def create_post(
    post: PostCreateSchema,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[str, Depends(get_current_user)]
):
    post_orm = PostORMModel(user_id=current_user.id, **post.model_dump())
    db.add(post_orm)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(post_orm)
    return post_orm

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    id: int,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[str, Depends(get_current_user)]
):
    post_orm = await db.get(PostORMModel, id)
    if post_orm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id = {id} was not found"
        )
    if post_orm.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to delete this post"
        )

    await db.delete(post_orm)
    await db.commit()

@router.put(
    "/{id}",
    status_code=status.HTTP_201_CREATED,
    response_model=PostResponseSchema
)
async def update_post(
    id: int,
    updated_post: PostCreateSchema,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[str, Depends(get_current_user)]
):
    post_orm = await db.get(PostORMModel, id)
    if post_orm is None:
        raise HTTPException(
            status_code=404,
            detail=f"Post with id = {id} was not found"
        )
    if post_orm.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to delete this post"
        )
    for field, value in updated_post.model_dump().items():
        setattr(post_orm, field, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(post_orm)
    return post_orm
