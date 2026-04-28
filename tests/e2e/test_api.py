import pytest

pytestmark = pytest.mark.integration


async def test_health_is_open(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_missing_api_key_returns_401(client):
    resp = await client.post("/projects/", json={"name": "P"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Invalid or missing API key"}


async def test_wrong_api_key_returns_401(client):
    resp = await client.post("/projects/", json={"name": "P"}, headers={"X-API-Key": "nope"})
    assert resp.status_code == 401


async def test_create_project_validation_error(client, auth_headers):
    resp = await client.post("/projects/", json={"name": ""}, headers=auth_headers)
    assert resp.status_code == 422


async def test_project_crud_round_trip(client, auth_headers):
    create = await client.post(
        "/projects/",
        json={"name": "Apollo", "description": "moon"},
        headers=auth_headers,
    )
    assert create.status_code == 201
    pid = create.json()["id"]

    got = await client.get(f"/projects/{pid}", headers=auth_headers)
    assert got.status_code == 200
    assert got.json()["name"] == "Apollo"

    upd = await client.put(
        f"/projects/{pid}",
        json={"description": "to the moon"},
        headers=auth_headers,
    )
    assert upd.status_code == 200
    body = upd.json()
    assert body["name"] == "Apollo"
    assert body["description"] == "to the moon"

    delete = await client.delete(f"/projects/{pid}", headers=auth_headers)
    assert delete.status_code == 204

    missing = await client.get(f"/projects/{pid}", headers=auth_headers)
    assert missing.status_code == 404
    assert "not found" in missing.json()["detail"].lower()


async def test_get_missing_project_returns_404_with_handler_body(client, auth_headers):
    resp = await client.get("/projects/999999", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Project 999999 not found"}


async def test_create_task_under_missing_project_returns_404(client, auth_headers):
    resp = await client.post(
        "/projects/999999/tasks/",
        json={"title": "x", "priority": 1},
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Project 999999 not found"}


async def test_list_tasks_priority_desc_and_pagination(client, auth_headers):
    project = await client.post("/projects/", json={"name": "P"}, headers=auth_headers)
    pid = project.json()["id"]

    for title, priority in [("low", 1), ("high", 10), ("mid", 5)]:
        await client.post(
            f"/projects/{pid}/tasks/",
            json={"title": title, "priority": priority},
            headers=auth_headers,
        )

    full = await client.get(f"/projects/{pid}/tasks/", headers=auth_headers)
    assert full.status_code == 200
    assert [t["priority"] for t in full.json()] == [10, 5, 1]

    page = await client.get(f"/projects/{pid}/tasks/?limit=1&offset=1", headers=auth_headers)
    assert page.status_code == 200
    body = page.json()
    assert len(body) == 1
    assert body[0]["priority"] == 5


async def test_update_task_partial(client, auth_headers):
    project = await client.post("/projects/", json={"name": "P"}, headers=auth_headers)
    pid = project.json()["id"]
    task = await client.post(
        f"/projects/{pid}/tasks/",
        json={"title": "t", "priority": 1},
        headers=auth_headers,
    )
    tid = task.json()["id"]

    upd = await client.put(f"/tasks/{tid}", json={"completed": True}, headers=auth_headers)
    assert upd.status_code == 200
    body = upd.json()
    assert body["completed"] is True
    assert body["title"] == "t"
    assert body["priority"] == 1


async def test_delete_project_cascades_tasks(client, auth_headers):
    project = await client.post("/projects/", json={"name": "P"}, headers=auth_headers)
    pid = project.json()["id"]
    for i in range(3):
        await client.post(
            f"/projects/{pid}/tasks/",
            json={"title": f"t{i}", "priority": i},
            headers=auth_headers,
        )

    delete = await client.delete(f"/projects/{pid}", headers=auth_headers)
    assert delete.status_code == 204

    listed = await client.get(f"/projects/{pid}/tasks/", headers=auth_headers)
    assert listed.status_code == 404
