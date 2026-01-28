from __future__ import annotations


def test_full_flow_register_login_org_project_task_refresh_logout(client):
    # register
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "tomas@example.com", "password": "Secret123!", "full_name": "Tomas"},
    )
    assert r.status_code == 201, r.text

    # login
    r = client.post("/api/v1/auth/login", json={"email": "tomas@example.com", "password": "Secret123!"})
    assert r.status_code == 200, r.text
    tokens = r.json()
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    # create org
    r = client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {access}"},
        json={"name": "Operant Org", "slug": "operant-org"},
    )
    assert r.status_code == 201, r.text
    org_id = r.json()["id"]

    # create project
    r = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {access}", "X-Organization-Id": org_id},
        json={"name": "Projeto 1", "description": "Desc"},
    )
    assert r.status_code == 201, r.text
    project_id = r.json()["id"]

    # create task
    r = client.post(
        "/api/v1/tasks",
        params={"project_id": project_id},
        headers={"Authorization": f"Bearer {access}", "X-Organization-Id": org_id},
        json={"title": "Tarefa 1", "description": "A", "status": "TODO"},
    )
    assert r.status_code == 201, r.text

    # list tasks
    r = client.get(
        "/api/v1/tasks",
        params={"project_id": project_id, "status": "TODO"},
        headers={"Authorization": f"Bearer {access}", "X-Organization-Id": org_id},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["total"] == 1

    # refresh (rotation)
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200, r.text
    new_refresh = r.json()["refresh_token"]
    assert new_refresh != refresh

    # old refresh should now fail
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 401, r.text

    # logout should invalidate current refresh
    r = client.post("/api/v1/auth/logout", json={"refresh_token": new_refresh})
    assert r.status_code == 204, r.text
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert r.status_code == 401, r.text


