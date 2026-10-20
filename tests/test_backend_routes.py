from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activities():
    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    return TestClient(app)


class TestBackendRoutes:
    def test_root_redirects_to_static_page(self, client):
        # Arrange
        expected_location = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_location

    def test_get_activities_returns_all_activity_data(self, client):
        # Arrange
        expected = deepcopy(activities)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        assert response.json() == expected

    def test_signup_adds_new_participant(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "new.student@mergington.edu"

        # Act
        response = client.post(
            "/activities/Chess%20Club/signup", params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {
            "message": f"Signed up {email} for {activity_name}"
        }
        assert email in activities[activity_name]["participants"]

    def test_signup_rejects_duplicate_participant_without_mutation(self, client):
        # Arrange
        email = "michael@mergington.edu"
        before = deepcopy(activities)

        # Act
        response = client.post(
            "/activities/Chess%20Club/signup", params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert response.json() == {
            "detail": "Student already signed up for this activity"
        }
        assert activities == before

    def test_signup_rejects_unknown_activity_without_mutation(self, client):
        # Arrange
        before = deepcopy(activities)
        email = "student@mergington.edu"

        # Act
        response = client.post(
            "/activities/Unknown%20Club/signup", params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json() == {"detail": "Activity not found"}
        assert activities == before

    def test_signup_requires_email_without_mutation(self, client):
        # Arrange
        before = deepcopy(activities)

        # Act
        response = client.post("/activities/Chess%20Club/signup")

        # Assert
        assert response.status_code == 422
        assert activities == before
