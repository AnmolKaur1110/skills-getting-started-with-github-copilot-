import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# keep initial data snapshot for clean state between tests
INITIAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))
    yield
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))


client = TestClient(app)


def test_get_activities():
    # Arrange: reset fixture spun up automatically

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_new_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]

    # verify side effect in get_activities
    activities_state = client.get("/activities").json()
    assert email in activities_state[activity_name]["participants"]


def test_signup_duplicate_participant():
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": existing_email})

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_activity_full():
    # Arrange
    activity_name = "Tennis Club"
    # fill to max
    for i in range(10, 10 + activities[activity_name]["max_participants"] - len(activities[activity_name]["participants"])):
        email = f"temp{i}@mergington.edu"
        r = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        assert r.status_code == 200

    # Act: one more signup should fail
    response = client.post(f"/activities/{activity_name}/signup", params={"email": "overflow@mergington.edu"})

    # Assert
    assert response.status_code == 400
    assert "full" in response.json()["detail"]


def test_remove_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "daniel@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert "Removed" in response.json()["message"]
    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_remove_missing_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "nobody@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert "Participant not found" in response.json()["detail"]
