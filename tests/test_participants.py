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
        email = "michael@mergington.edu"
        before = deepcopy(activities)
        response = self.client.delete(
            "/activities/Chess%20Club/participants", params={"email": email}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": f"Unregistered {email} from Chess Club"},
        )
        expected = deepcopy(before)
        expected["Chess Club"]["participants"].remove(email)
        self.assertEqual(self.client.get("/activities").json(), expected)

    def test_unregister_unknown_activity_does_not_change_data(self):
        before = deepcopy(activities)
        response = self.client.delete(
            "/activities/Unknown/participants",
            params={"email": "michael@mergington.edu"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})
        self.assertEqual(activities, before)

    def test_unregister_unknown_participant_does_not_change_data(self):
        before = deepcopy(activities)
        response = self.client.delete(
            "/activities/Chess%20Club/participants",
            params={"email": "missing@mergington.edu"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Participant not found"})
        self.assertEqual(activities, before)

    def test_signup_unregister_and_signup_again(self):
        email = "student+test@mergington.edu"
        signup = "/activities/Chess%20Club/signup"
        unregister = "/activities/Chess%20Club/participants"
        params = {"email": email}
        self.assertEqual(self.client.post(signup, params=params).status_code, 200)
        self.assertEqual(self.client.post(signup, params=params).status_code, 400)
        self.assertEqual(self.client.delete(unregister, params=params).status_code, 200)
        self.assertEqual(self.client.delete(unregister, params=params).status_code, 404)
        self.assertEqual(self.client.post(signup, params=params).status_code, 200)

    def test_unregister_last_participant(self):
        activities["Chess Club"]["participants"] = ["only@mergington.edu"]
        response = self.client.delete(
            "/activities/Chess%20Club/participants",
            params={"email": "only@mergington.edu"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get("/activities").json()["Chess Club"]["participants"], []
        )

    def test_unregister_requires_email(self):
        before = deepcopy(activities)
        response = self.client.delete("/activities/Chess%20Club/participants")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(activities, before)
