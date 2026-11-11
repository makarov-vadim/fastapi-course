import pytest
from app.schemas import (
    PostResponseSchema, 
    PostVoteResponseSchema, 
    PostsVoteResponseSchema,
)


@pytest.mark.asyncio
async def test_get_all_posts(authorized_async_client, test_posts):
    res = await authorized_async_client.get(
        "/posts/"
    )
    assert res.status_code == 200
    
    api_response = PostsVoteResponseSchema.model_validate(res.json())

    db_posts_data = [PostResponseSchema.model_validate(post) for post in test_posts]
    res_posts_data = [item.post for item in api_response.root]

    assert len(res_posts_data) == len(db_posts_data)

    res_posts_data.sort(key=lambda x: x.id)
    db_posts_data.sort(key=lambda x: x.id)
    assert res_posts_data == db_posts_data


@pytest.mark.asyncio
async def test_unauthorized_user_get_all_posts(async_client):
    res = await async_client.get(
        "/posts/"
    )
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_unauthorized_user_get_one_posts(async_client, test_posts):
    res = await async_client.get(
        f"/posts/{test_posts[0].id}"
    )
    assert res.status_code == 401    


@pytest.mark.asyncio
async def test_get_one_post(authorized_async_client, test_posts):
    test_post = test_posts[0]
    res = await authorized_async_client.get(
        f"/posts/{test_post.id}"
    )
    assert res.status_code == 200

    db_post_data = PostResponseSchema.model_validate(test_post)
    res_post_data = PostVoteResponseSchema.model_validate(res.json()).post

    assert res_post_data == db_post_data

@pytest.mark.asyncio
async def test_get_one_post_not_exist(authorized_async_client):
    res = await authorized_async_client.get(
        "/posts/2147483647"
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_create_post(authorized_async_client, test_posts_data, new_user):
    db_post_data = test_posts_data[0]
    res = await authorized_async_client.post(
        "/posts/",
        json=db_post_data
    )
    assert res.status_code == 201
    
    res_post_data = PostResponseSchema.model_validate(res.json())

    assert res_post_data.title == db_post_data.get("title")
    assert res_post_data.content == db_post_data.get("content")
    assert res_post_data.published == db_post_data.get("published")
    assert res_post_data.user_id == new_user.get("id")

@pytest.mark.asyncio
async def test_create_post_default_published(authorized_async_client, test_posts_data, new_user):
    db_post_data = {
        "title": test_posts_data[0].get("title"),
        "content": test_posts_data[0].get("content")
    }
    res = await authorized_async_client.post(
        "/posts/",
        json=db_post_data
    )
    assert res.status_code == 201
    
    res_post_data = PostResponseSchema.model_validate(res.json())

    assert res_post_data.title == db_post_data.get("title")
    assert res_post_data.content == db_post_data.get("content")
    assert res_post_data.published == True
    assert res_post_data.user_id == new_user.get("id")

@pytest.mark.asyncio
async def test_unauthorized_user_create_post(async_client, test_posts_data):
    db_post_data = test_posts_data[0]
    res = await async_client.post(
        "/posts/",
        json=db_post_data
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_delete_post(authorized_async_client, test_posts):
    test_post = test_posts[0]
    res = await authorized_async_client.delete(
        f"/posts/{test_post.id}"
    )
    assert res.status_code == 204

@pytest.mark.asyncio
async def test_unauthorized_user_delete_post(async_client, test_posts):
    test_post = test_posts[0]
    res = await async_client.delete(
        f"/posts/{test_post.id}"
    )
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_delete_post(authorized_async_client, test_posts):
    test_post = test_posts[0]
    res = await authorized_async_client.delete(
        f"/posts/{test_post.id}"
    )
    assert res.status_code == 204

@pytest.mark.asyncio
async def test_delete_post_not_exist(authorized_async_client):
    res = await authorized_async_client.delete(
        "/posts/2147483646"
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_delete_other_user_post(
    authorized_other_user_async_client,
    test_posts
):
    post_to_delete = test_posts[0]
    
    res = await authorized_other_user_async_client.delete(
        f"/posts/{post_to_delete.id}"
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_updeate_post(authorized_async_client, test_posts, new_user):
    data = {
        "title": "updeate title",
        "content": "updeate content"
    }
    res = await authorized_async_client.put(
        f"/posts/{test_posts[0].id}",
        json=data
    )
    assert res.status_code == 201
    
    res_post_data = PostResponseSchema.model_validate(res.json())

    assert res_post_data.title == data.get("title")
    assert res_post_data.content == data.get("content")


@pytest.mark.asyncio
async def test_updeate_other_user_post(
    authorized_other_user_async_client,
    test_posts
):
    post_to_updeate = test_posts[0]
    data = {
        "title": "updeate title",
        "content": "updeate content"
    }    
    
    res = await authorized_other_user_async_client.put(
        f"/posts/{post_to_updeate.id}",
        json=data
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_unauthorized_user_updeate_post(async_client, test_posts):
    post_to_updeate = test_posts[0]
    data = {
        "title": "updeate title",
        "content": "updeate content"
    }
    res = await async_client.put(
        f"/posts/{post_to_updeate.id}",
        json=data
    )
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_updeate_post_not_exist(authorized_async_client):
    data = {
        "title": "updeate title",
        "content": "updeate content"
    }
    res = await authorized_async_client.put(
        "/posts/2147483646",
        json=data
    )
    assert res.status_code == 404