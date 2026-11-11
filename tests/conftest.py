import pytest

from collections.abc import AsyncGenerator
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.config import settings
from app.database import get_async_db, BaseORMModel
from app.models import PostORMModel, UserORMModel
from app.oauth2 import create_access_token
from app.utils import get_password_hash


test_engine = create_async_engine(
    url=f"{settings.DATABASE_URL_asyncpg}_test",
    echo=False
)


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(BaseORMModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(BaseORMModel.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        
        session = AsyncSession(bind=connection, expire_on_commit=False)
        
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def get_async_db_override():
        yield db_session

    app.dependency_overrides[get_async_db] = get_async_db_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
        
    app.dependency_overrides.clear()


@pytest.fixture
async def new_user(async_client):
    email = "email@email.email"
    password = "password"
    
    res = await async_client.post(
        "/users/",
        json={"email": email, "password": password}
    )
    assert res.status_code == 201
    
    user_data = res.json()
    user_data["password"] = password
    return user_data


@pytest.fixture
async def other_user(db_session: AsyncSession):
    user = UserORMModel(
        email="other@other.other",
        hashed_password=get_password_hash("other_password")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def token(new_user):
    return create_access_token({"user_id": new_user.get("id")})

@pytest.fixture
def other_user_token(other_user):
    return create_access_token({"user_id": other_user.id})

@pytest.fixture
async def authorized_async_client(token):
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, 
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"}
    ) as client:
        yield client

@pytest.fixture
async def authorized_other_user_async_client(other_user_token):
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, 
        base_url="http://test",
        headers={"Authorization": f"Bearer {other_user_token}"}
    ) as client:
        yield client


@pytest.fixture
def test_posts_data():
    return [
        {
            "title": "First title",
            "content": "First content",
            "published": True,
        },
        {
            "title": "Second title",
            "content": "Second content",
            "published": True,
        },
        {
            "title": "Third title",
            "content": "Third content",
            "published": True,
        }
    ]

@pytest.fixture
async def test_posts(db_session, test_posts_data, new_user):
    posts = []
    for data in test_posts_data:
        post = PostORMModel(
            **data,
            user_id=new_user["id"]
        )
        db_session.add(post)
        posts.append(post)
        
    await db_session.commit()
    
    for post in posts:
        await db_session.refresh(post, attribute_names=["user"])
        
    return posts
