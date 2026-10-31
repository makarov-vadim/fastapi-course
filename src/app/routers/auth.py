from fastapi import status, HTTPException, Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import UserORMModel
from ..schemas import TokenSchema
from ..database import get_async_db
from ..utils import verify_password
from ..oauth2 import create_access_token



router = APIRouter(
    # prefix="/posts",
    tags=["Authentication"]
)

@router.post(
    "/login",
    response_model=TokenSchema,
)
async def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(
        select(UserORMModel).where(UserORMModel.email == user_credentials.username)
    )
    user_orm = result.scalars().first()

    if user_orm is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid Credentials. Please try again."
        )

    if not verify_password(
        plain_password=user_credentials.password,
        hashed_password=user_orm.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid Credentials. Please try again."
        )

    access_token = create_access_token(
        data = {"user_id": user_orm.id}
    )

    return {"access_token": access_token, "token_type": "bearer"}
    # return TokenSchema(**{"token": access_token, "token_type": "bearer"})


