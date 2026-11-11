import pytest

import pytest
from app.models import VoteORMModel


@pytest.fixture
async def test_vote(db_session, test_posts, new_user):
    new_vote = VoteORMModel(
        post_id=test_posts[0].id, 
        user_id=new_user["id"]
    )
    db_session.add(new_vote)

    await db_session.commit()
    
    return new_vote


@pytest.mark.asyncio
async def test_vote_on_post(authorized_async_client, test_posts):
    res = await authorized_async_client.post(
        "/vote/",
        json={
            "post_id": test_posts[0].id
        }
    )

    assert res.status_code == 201


@pytest.mark.asyncio
async def test_vote_twice_post(
    authorized_async_client, 
    test_vote
):
    res = await authorized_async_client.post(
        "/vote/", 
        json={"post_id": test_vote.post_id}
    )
    
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_delete_vote(
    authorized_async_client, 
    test_vote
):
    res = await authorized_async_client.delete(
        f"/vote/{test_vote.post_id}"
    )
    
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_delete_vote_non_exist(
    authorized_async_client, 
    test_posts
):
    post_id = test_posts[0].id
    res = await authorized_async_client.delete(
        f"/vote/{post_id}"
    )

    assert res.status_code == 404


@pytest.mark.asyncio
async def test_vote_post_non_exist(authorized_async_client):
    post_id = 2147483647
    
    res = await authorized_async_client.post(
        "/vote/", 
        json={"post_id": post_id}
    )

    assert res.status_code == 404


@pytest.mark.asyncio
async def test_vote_unauthorized_user(
    async_client, 
    test_posts
):
    res = await async_client.post(
        "/vote/", 
        json={"post_id": test_posts[0].id}
    )

    assert res.status_code == 401
