from copy import deepcopy
import unittest

from fastapi.testclient import TestClient

from src.app import activities, app


class ParticipantTests(unittest.TestCase):
    def setUp(self):
        original = deepcopy(activities)
        self.addCleanup(self.restore_activities, original)
        self.client = TestClient(app)

    @staticmethod
    def restore_activities(original):
        activities.clear()
        activities.update(original)

    def test_unregister_removes_only_selected_participant(self):
        # Arrange
        email = "michael@mergington.edu"
        before = deepcopy(activities)

        # Act
        response = self.client.delete(
            "/activities/Chess%20Club/participants", params={"email": email}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": f"Unregistered {email} from Chess Club"},
        )
        expected = deepcopy(before)
        expected["Chess Club"]["participants"].remove(email)
        self.assertEqual(self.client.get("/activities").json(), expected)

    def test_unregister_unknown_activity_does_not_change_data(self):
        # Arrange
        before = deepcopy(activities)

        # Act
        response = self.client.delete(
            "/activities/Unknown/participants",
            params={"email": "michael@mergington.edu"},
        )

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})
        self.assertEqual(activities, before)

    def test_unregister_unknown_participant_does_not_change_data(self):
        # Arrange
        before = deepcopy(activities)

        # Act
        response = self.client.delete(
            "/activities/Chess%20Club/participants",
            params={"email": "missing@mergington.edu"},
        )

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Participant not found"})
        self.assertEqual(activities, before)

    def test_signup_unregister_and_signup_again(self):
        # Arrange
        email = "student+test@mergington.edu"
        signup = "/activities/Chess%20Club/signup"
        unregister = "/activities/Chess%20Club/participants"
        params = {"email": email}

        # Act
        signup_response = self.client.post(signup, params=params)
        duplicate_response = self.client.post(signup, params=params)
        unregister_response = self.client.delete(unregister, params=params)
        missing_response = self.client.delete(unregister, params=params)
        signup_again_response = self.client.post(signup, params=params)

        # Assert
        self.assertEqual(signup_response.status_code, 200)
        self.assertEqual(duplicate_response.status_code, 400)
        self.assertEqual(unregister_response.status_code, 200)
        self.assertEqual(missing_response.status_code, 404)
        self.assertEqual(signup_again_response.status_code, 200)

    def test_unregister_last_participant(self):
        # Arrange
        activities["Chess Club"]["participants"] = ["only@mergington.edu"]

        # Act
        response = self.client.delete(
            "/activities/Chess%20Club/participants",
            params={"email": "only@mergington.edu"},
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get("/activities").json()["Chess Club"]["participants"], []
        )

    def test_unregister_requires_email(self):
        # Arrange
        before = deepcopy(activities)

        # Act
        response = self.client.delete("/activities/Chess%20Club/participants")

        # Assert
        self.assertEqual(response.status_code, 422)
        self.assertEqual(activities, before)
