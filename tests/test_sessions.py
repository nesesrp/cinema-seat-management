def _create_hall(client, name="Hall A"):
    return client.post("/halls/", json={"name": name}).json()


def _create_session(client, hall_id, movie_name="Movie", start_time="2026-09-14T18:00:00"):
    return client.post(
        "/sessions/",
        json={"movie_name": movie_name, "start_time": start_time, "hall_id": hall_id},
    ).json()


def test_get_session_by_id(client):
    hall = _create_hall(client)
    session = _create_session(client, hall["id"])

    response = client.get(f"/sessions/{session['id']}")

    assert response.status_code == 200
    assert response.json()["movie_name"] == "Movie"


def test_get_missing_session_returns_404(client):
    assert client.get("/sessions/999").status_code == 404


def test_update_session(client):
    hall = _create_hall(client)
    session = _create_session(client, hall["id"])

    response = client.put(
        f"/sessions/{session['id']}",
        json={"movie_name": "Other", "start_time": "2026-09-15T20:30:00"},
    )

    assert response.status_code == 200
    body = client.get(f"/sessions/{session['id']}").json()
    assert body["movie_name"] == "Other"
    assert body["start_time"] == "2026-09-15T20:30:00"
    assert body["hall_id"] == hall["id"]


def test_update_missing_session_returns_404(client):
    response = client.put(
        "/sessions/999", json={"movie_name": "Other", "start_time": "2026-09-15T20:30:00"}
    )

    assert response.status_code == 404


def test_delete_session(client):
    hall = _create_hall(client)
    session = _create_session(client, hall["id"])

    assert client.delete(f"/sessions/{session['id']}").status_code == 204
    assert client.get(f"/sessions/{session['id']}").status_code == 404


def test_delete_session_with_reservations_is_rejected(client):
    hall = _create_hall(client)
    seat = client.post(f"/halls/{hall['id']}/seats/", json={"row": 1, "number": 1}).json()
    session = _create_session(client, hall["id"])
    client.post("/reservations/", json={"session_id": session["id"], "seat_id": seat["id"]})

    assert client.delete(f"/sessions/{session['id']}").status_code == 409


def test_filter_sessions_by_hall(client):
    hall_a = _create_hall(client, name="Hall A")
    hall_b = _create_hall(client, name="Hall B")
    _create_session(client, hall_a["id"])
    session_b = _create_session(client, hall_b["id"])

    response = client.get("/sessions/", params={"hall_id": hall_b["id"]})

    assert [s["id"] for s in response.json()] == [session_b["id"]]


def test_filter_sessions_by_date(client):
    hall = _create_hall(client)
    _create_session(client, hall["id"], start_time="2026-09-13T23:59:00")
    morning = _create_session(client, hall["id"], start_time="2026-09-14T00:00:00")
    evening = _create_session(client, hall["id"], start_time="2026-09-14T23:59:00")
    _create_session(client, hall["id"], start_time="2026-09-15T00:00:00")

    response = client.get("/sessions/", params={"date": "2026-09-14"})

    assert sorted(s["id"] for s in response.json()) == sorted([morning["id"], evening["id"]])


def test_filter_sessions_by_hall_and_date(client):
    hall_a = _create_hall(client, name="Hall A")
    hall_b = _create_hall(client, name="Hall B")
    match = _create_session(client, hall_a["id"], start_time="2026-09-14T18:00:00")
    _create_session(client, hall_b["id"], start_time="2026-09-14T18:00:00")
    _create_session(client, hall_a["id"], start_time="2026-09-15T18:00:00")

    response = client.get("/sessions/", params={"hall_id": hall_a["id"], "date": "2026-09-14"})

    assert [s["id"] for s in response.json()] == [match["id"]]
