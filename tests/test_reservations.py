def _create_hall(client, name="Hall A"):
    return client.post("/halls/", json={"name": name}).json()


def _create_seat(client, hall_id, row=1, number=1):
    return client.post(f"/halls/{hall_id}/seats/", json={"row": row, "number": number}).json()


def _create_session(client, hall_id, movie_name="Test Movie"):
    return client.post(
        "/sessions/",
        json={"movie_name": movie_name, "start_time": "2026-09-14T18:00:00", "hall_id": hall_id},
    ).json()


def test_seats_are_available_before_any_reservation(client):
    hall = _create_hall(client)
    _create_seat(client, hall["id"], row=1, number=1)
    _create_seat(client, hall["id"], row=1, number=2)
    session = _create_session(client, hall["id"])

    response = client.get(f"/sessions/{session['id']}/seats")

    assert response.status_code == 200
    assert [seat["status"] for seat in response.json()] == ["available", "available"]


def test_reservation_marks_seat_as_occupied(client):
    hall = _create_hall(client)
    seat = _create_seat(client, hall["id"])
    session = _create_session(client, hall["id"])

    response = client.post("/reservations/", json={"session_id": session["id"], "seat_id": seat["id"]})
    assert response.status_code == 200

    statuses = client.get(f"/sessions/{session['id']}/seats").json()
    assert statuses[0]["status"] == "occupied"


def test_duplicate_reservation_is_rejected(client):
    hall = _create_hall(client)
    seat = _create_seat(client, hall["id"])
    session = _create_session(client, hall["id"])
    client.post("/reservations/", json={"session_id": session["id"], "seat_id": seat["id"]})

    response = client.post("/reservations/", json={"session_id": session["id"], "seat_id": seat["id"]})

    assert response.status_code == 409


def test_reservation_for_seat_in_different_hall_is_rejected(client):
    hall_a = _create_hall(client, name="Hall A")
    hall_b = _create_hall(client, name="Hall B")
    seat_in_b = _create_seat(client, hall_b["id"])
    session_in_a = _create_session(client, hall_a["id"])

    response = client.post(
        "/reservations/", json={"session_id": session_in_a["id"], "seat_id": seat_in_b["id"]}
    )

    assert response.status_code == 400


def test_reservation_for_unknown_seat_is_404(client):
    hall = _create_hall(client)
    session = _create_session(client, hall["id"])

    response = client.post("/reservations/", json={"session_id": session["id"], "seat_id": 999})

    assert response.status_code == 404


def test_seats_for_unknown_session_is_404(client):
    response = client.get("/sessions/999/seats")

    assert response.status_code == 404


def test_seat_for_unknown_hall_is_404(client):
    response = client.post("/halls/999/seats/", json={"row": 1, "number": 1})

    assert response.status_code == 404


def test_cancel_reservation_frees_the_seat(client):
    hall = _create_hall(client)
    seat = _create_seat(client, hall["id"])
    session = _create_session(client, hall["id"])
    reservation = client.post(
        "/reservations/", json={"session_id": session["id"], "seat_id": seat["id"]}
    ).json()

    response = client.delete(f"/reservations/{reservation['id']}")
    assert response.status_code == 204

    statuses = client.get(f"/sessions/{session['id']}/seats").json()
    assert statuses[0]["status"] == "available"


def test_cancel_unknown_reservation_is_404(client):
    response = client.delete("/reservations/999")

    assert response.status_code == 404


def test_seat_can_be_reserved_again_after_cancellation(client):
    hall = _create_hall(client)
    seat = _create_seat(client, hall["id"])
    session = _create_session(client, hall["id"])
    reservation = client.post(
        "/reservations/", json={"session_id": session["id"], "seat_id": seat["id"]}
    ).json()
    client.delete(f"/reservations/{reservation['id']}")

    response = client.post(
        "/reservations/", json={"session_id": session["id"], "seat_id": seat["id"]}
    )

    assert response.status_code == 200


def test_filter_reservations_by_session_and_seat(client):
    hall = _create_hall(client)
    seat_1 = _create_seat(client, hall["id"], row=1, number=1)
    seat_2 = _create_seat(client, hall["id"], row=1, number=2)
    session_1 = _create_session(client, hall["id"], movie_name="Movie 1")
    session_2 = _create_session(client, hall["id"], movie_name="Movie 2")
    r1 = client.post("/reservations/", json={"session_id": session_1["id"], "seat_id": seat_1["id"]}).json()
    r2 = client.post("/reservations/", json={"session_id": session_1["id"], "seat_id": seat_2["id"]}).json()
    r3 = client.post("/reservations/", json={"session_id": session_2["id"], "seat_id": seat_1["id"]}).json()

    by_session = client.get("/reservations/", params={"session_id": session_1["id"]}).json()
    by_seat = client.get("/reservations/", params={"seat_id": seat_1["id"]}).json()
    by_both = client.get(
        "/reservations/", params={"session_id": session_1["id"], "seat_id": seat_1["id"]}
    ).json()

    assert sorted(r["id"] for r in by_session) == sorted([r1["id"], r2["id"]])
    assert sorted(r["id"] for r in by_seat) == sorted([r1["id"], r3["id"]])
    assert [r["id"] for r in by_both] == [r1["id"]]
    assert len(client.get("/reservations/").json()) == 3
