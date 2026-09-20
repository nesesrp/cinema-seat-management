def _create_hall(client, name="Hall A"):
    return client.post("/halls/", json={"name": name}).json()


def _create_session(client, hall_id, movie_name="Movie", start_time="2099-09-14T18:00:00"):
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
        json={"movie_name": "Other", "start_time": "2099-09-15T20:30:00"},
    )

    assert response.status_code == 200
    body = client.get(f"/sessions/{session['id']}").json()
    assert body["movie_name"] == "Other"
    assert body["start_time"] == "2099-09-15T20:30:00"
    assert body["hall_id"] == hall["id"]


def test_update_missing_session_returns_404(client):
    response = client.put(
        "/sessions/999", json={"movie_name": "Other", "start_time": "2099-09-15T20:30:00"}
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
    _create_session(client, hall["id"], start_time="2099-09-13T20:00:00")
    morning = _create_session(client, hall["id"], start_time="2099-09-14T00:00:00")
    evening = _create_session(client, hall["id"], start_time="2099-09-14T23:00:00")
    _create_session(client, hall["id"], start_time="2099-09-15T03:00:00")

    response = client.get("/sessions/", params={"date": "2099-09-14"})

    assert sorted(s["id"] for s in response.json()) == sorted([morning["id"], evening["id"]])


def test_filter_sessions_by_hall_and_date(client):
    hall_a = _create_hall(client, name="Hall A")
    hall_b = _create_hall(client, name="Hall B")
    match = _create_session(client, hall_a["id"], start_time="2099-09-14T18:00:00")
    _create_session(client, hall_b["id"], start_time="2099-09-14T18:00:00")
    _create_session(client, hall_a["id"], start_time="2099-09-15T18:00:00")

    response = client.get("/sessions/", params={"hall_id": hall_a["id"], "date": "2099-09-14"})

    assert [s["id"] for s in response.json()] == [match["id"]]


def test_session_in_the_past_is_rejected(client):
    hall = _create_hall(client)

    response = client.post(
        "/sessions/",
        json={"movie_name": "Old", "start_time": "2000-01-01T18:00:00", "hall_id": hall["id"]},
    )

    assert response.status_code == 400


def test_overlapping_session_in_same_hall_is_rejected(client):
    hall = _create_hall(client)
    _create_session(client, hall["id"], start_time="2099-09-14T18:00:00")

    for start_time in ("2099-09-14T18:00:00", "2099-09-14T20:59:00", "2099-09-14T15:01:00"):
        response = client.post(
            "/sessions/",
            json={"movie_name": "Clash", "start_time": start_time, "hall_id": hall["id"]},
        )
        assert response.status_code == 409, start_time


def test_sessions_a_full_slot_apart_are_allowed(client):
    hall = _create_hall(client)
    _create_session(client, hall["id"], start_time="2099-09-14T18:00:00")

    for start_time in ("2099-09-14T21:00:00", "2099-09-14T15:00:00"):
        response = client.post(
            "/sessions/",
            json={"movie_name": "Next", "start_time": start_time, "hall_id": hall["id"]},
        )
        assert response.status_code == 200, start_time


def test_same_time_in_different_halls_is_allowed(client):
    hall_a = _create_hall(client, name="Hall A")
    hall_b = _create_hall(client, name="Hall B")
    _create_session(client, hall_a["id"])

    response = client.post(
        "/sessions/",
        json={"movie_name": "Movie", "start_time": "2099-09-14T18:00:00", "hall_id": hall_b["id"]},
    )

    assert response.status_code == 200


def test_update_session_time_to_conflict_or_past_is_rejected(client):
    hall = _create_hall(client)
    _create_session(client, hall["id"], start_time="2099-09-14T18:00:00")
    session = _create_session(client, hall["id"], start_time="2099-09-14T22:00:00")

    conflict = client.put(
        f"/sessions/{session['id']}",
        json={"movie_name": "Movie", "start_time": "2099-09-14T19:00:00"},
    )
    past = client.put(
        f"/sessions/{session['id']}",
        json={"movie_name": "Movie", "start_time": "2000-01-01T18:00:00"},
    )

    assert conflict.status_code == 409
    assert past.status_code == 400


def test_update_session_does_not_conflict_with_itself(client):
    hall = _create_hall(client)
    session = _create_session(client, hall["id"], start_time="2099-09-14T18:00:00")

    same_time = client.put(
        f"/sessions/{session['id']}",
        json={"movie_name": "Renamed", "start_time": "2099-09-14T18:00:00"},
    )
    nudged = client.put(
        f"/sessions/{session['id']}",
        json={"movie_name": "Renamed", "start_time": "2099-09-14T19:00:00"},
    )

    assert same_time.status_code == 200
    assert nudged.status_code == 200
