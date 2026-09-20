def _create_hall(client, name="Hall A"):
    return client.post("/halls/", json={"name": name}).json()


def _create_seat(client, hall_id, row=1, number=1):
    return client.post(f"/halls/{hall_id}/seats/", json={"row": row, "number": number}).json()


def test_bulk_create_seats(client):
    hall = _create_hall(client)

    response = client.post(f"/halls/{hall['id']}/seats/bulk", json={"rows": 3, "seats_per_row": 4})

    assert response.status_code == 200
    seats = response.json()
    assert len(seats) == 12
    assert {(s["row"], s["number"]) for s in seats} == {
        (r, n) for r in range(1, 4) for n in range(1, 5)
    }
    assert len(client.get(f"/halls/{hall['id']}/seats/").json()) == 12


def test_bulk_create_conflicting_seats_creates_nothing(client):
    hall = _create_hall(client)
    _create_seat(client, hall["id"], row=2, number=2)

    response = client.post(f"/halls/{hall['id']}/seats/bulk", json={"rows": 3, "seats_per_row": 3})

    assert response.status_code == 409
    assert len(client.get(f"/halls/{hall['id']}/seats/").json()) == 1


def test_bulk_create_validates_size(client):
    hall = _create_hall(client)

    assert client.post(f"/halls/{hall['id']}/seats/bulk", json={"rows": 0, "seats_per_row": 5}).status_code == 422
    assert client.post(f"/halls/{hall['id']}/seats/bulk", json={"rows": 5, "seats_per_row": 500}).status_code == 422


def test_bulk_create_in_missing_hall_returns_404(client):
    response = client.post("/halls/999/seats/bulk", json={"rows": 1, "seats_per_row": 1})

    assert response.status_code == 404


def test_update_seat(client):
    hall = _create_hall(client)
    seat = _create_seat(client, hall["id"])

    response = client.put(f"/halls/{hall['id']}/seats/{seat['id']}", json={"row": 5, "number": 7})

    assert response.status_code == 200
    assert (response.json()["row"], response.json()["number"]) == (5, 7)


def test_update_seat_to_taken_position_is_rejected(client):
    hall = _create_hall(client)
    _create_seat(client, hall["id"], row=1, number=1)
    seat = _create_seat(client, hall["id"], row=1, number=2)

    response = client.put(f"/halls/{hall['id']}/seats/{seat['id']}", json={"row": 1, "number": 1})

    assert response.status_code == 409


def test_seat_from_other_hall_is_not_found(client):
    hall_a = _create_hall(client, name="Hall A")
    hall_b = _create_hall(client, name="Hall B")
    seat = _create_seat(client, hall_a["id"])

    assert client.delete(f"/halls/{hall_b['id']}/seats/{seat['id']}").status_code == 404
    assert client.put(f"/halls/{hall_b['id']}/seats/{seat['id']}", json={"row": 1, "number": 1}).status_code == 404


def test_delete_seat(client):
    hall = _create_hall(client)
    seat = _create_seat(client, hall["id"])

    assert client.delete(f"/halls/{hall['id']}/seats/{seat['id']}").status_code == 204
    assert client.get(f"/halls/{hall['id']}/seats/").json() == []


def test_delete_reserved_seat_is_rejected(client):
    hall = _create_hall(client)
    seat = _create_seat(client, hall["id"])
    session = client.post(
        "/sessions/",
        json={"movie_name": "Movie", "start_time": "2099-09-14T18:00:00", "hall_id": hall["id"]},
    ).json()
    client.post("/reservations/", json={"session_id": session["id"], "seat_id": seat["id"]})

    assert client.delete(f"/halls/{hall['id']}/seats/{seat['id']}").status_code == 409


def test_create_seat_at_taken_position_is_rejected(client):
    hall = _create_hall(client)
    _create_seat(client, hall["id"], row=1, number=1)

    response = client.post(f"/halls/{hall['id']}/seats/", json={"row": 1, "number": 1})

    assert response.status_code == 409


def test_same_seat_position_in_different_halls_is_allowed(client):
    hall_a = _create_hall(client, name="Hall A")
    hall_b = _create_hall(client, name="Hall B")
    _create_seat(client, hall_a["id"], row=1, number=1)

    response = client.post(f"/halls/{hall_b['id']}/seats/", json={"row": 1, "number": 1})

    assert response.status_code == 200
