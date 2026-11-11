import pytest
import jwt
from app.schemas import UserResponseSchema, TokenSchema

from app.config import settings


@pytest.mark.asyncio
async def test_create_user(async_client):
    res = await async_client.post(
        "/users/",
        json={
            "email": "email@email.email",
            "password": "password"
        }
    )
    assert res.status_code == 201

    new_user = UserResponseSchema(**res.json())
    assert new_user.email == "email@email.email"


@pytest.mark.asyncio
async def test_login_user(async_client, new_user):
    res = await async_client.post(
        "/login",
        data={
            "username": new_user.get("email"),
            "password": new_user.get("password")
        }            
    )

    assert res.status_code == 200

    login_res = TokenSchema(**res.json())
    assert login_res.token_type == "bearer"

    payload = jwt.decode(
        jwt=login_res.access_token, 
        key=settings.SECRET_KEY,
        algorithms=settings.ALGORITHM
    )
    id = payload.get("user_id")
    assert id == new_user.get("id")


@pytest.mark.parametrize("email, password, status_code", [
    ('wrongemail@gmail.com', 'password123', 403),
    ('sanjeev@gmail.com', 'wrongpassword', 403),
    ('wrongemail@gmail.com', 'wrongpassword', 403),
    (None, 'password123', 422),
    ('sanjeev@gmail.com', None, 422)
])
@pytest.mark.asyncio
async def test_incorrect_login(async_client, email, password, status_code):
    res = await async_client.post(
        "/login", 
        data={"username": email, "password": password}
    )
    
    assert res.status_code == status_code


@pytest.mark.asyncio
async def test_get_user(authorized_async_client, new_user):
    res = await authorized_async_client.get(
        f"/users/{new_user.get("id")}"
    )

    assert res.status_code == 200

    test_user = UserResponseSchema(**new_user) 
    user_res = UserResponseSchema(**res.json())
    assert test_user == user_res
