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
