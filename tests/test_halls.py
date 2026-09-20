def test_create_and_list_hall(client):
    create_response = client.post("/halls/", json={"name": "Hall A"})
    assert create_response.status_code == 200
    assert create_response.json()["name"] == "Hall A"

    list_response = client.get("/halls/")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_duplicate_hall_name_is_rejected(client):
    client.post("/halls/", json={"name": "Hall A"})

    response = client.post("/halls/", json={"name": "Hall A"})

    assert response.status_code == 409


def test_get_hall_by_id(client):
    hall = client.post("/halls/", json={"name": "Hall A"}).json()

    response = client.get(f"/halls/{hall['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Hall A"


def test_get_missing_hall_returns_404(client):
    assert client.get("/halls/999").status_code == 404


def test_update_hall(client):
    hall = client.post("/halls/", json={"name": "Hall A"}).json()

    response = client.put(f"/halls/{hall['id']}", json={"name": "Hall B"})

    assert response.status_code == 200
    assert client.get(f"/halls/{hall['id']}").json()["name"] == "Hall B"


def test_update_hall_to_existing_name_is_rejected(client):
    client.post("/halls/", json={"name": "Hall A"})
    hall_b = client.post("/halls/", json={"name": "Hall B"}).json()

    response = client.put(f"/halls/{hall_b['id']}", json={"name": "Hall A"})

    assert response.status_code == 409


def test_delete_empty_hall(client):
    hall = client.post("/halls/", json={"name": "Hall A"}).json()

    assert client.delete(f"/halls/{hall['id']}").status_code == 204
    assert client.get(f"/halls/{hall['id']}").status_code == 404


def test_delete_hall_with_seats_is_rejected(client):
    hall = client.post("/halls/", json={"name": "Hall A"}).json()
    client.post(f"/halls/{hall['id']}/seats/", json={"row": 1, "number": 1})

    assert client.delete(f"/halls/{hall['id']}").status_code == 409
