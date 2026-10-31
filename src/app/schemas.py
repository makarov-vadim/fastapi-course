from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, RootModel, EmailStr

class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class TokenDataSchema(BaseModel):
    id: int | None = None


class UserBaseSchema(BaseModel):
    email: EmailStr
    password: str


class UserCreateSchema(UserBaseSchema):
    pass


class UserUpdateSchema(UserBaseSchema):
    pass


class UserResponseSchema(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLoginSchema(UserBaseSchema):
    pass


class PostBaseSchema(BaseModel):
    title: str
    content: str
    published: bool = True


class PostCreateSchema(PostBaseSchema):
    pass


class PostResponseSchema(PostBaseSchema):
    id: int
    user_id: int
    created_at: datetime

    user: UserResponseSchema

    model_config = ConfigDict(from_attributes=True)

class PostVoteResponseSchema(BaseModel):
    post: PostResponseSchema
    vote_count: int

    model_config = ConfigDict(from_attributes=True)


class PostsResponseSchema(RootModel[List[PostResponseSchema]]):
    pass

class PostsVoteResponseSchema(RootModel[List[PostVoteResponseSchema]]):
    pass


class VoteBaseSchema(BaseModel):
    post_id: int


class VoteUpdateSchema(VoteBaseSchema):
    dir: Literal[0, 1]


class VoteResponseSchema(VoteBaseSchema):
    created_at: datetime

