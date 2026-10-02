import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fastapi import HTTPException

from src.app import activities, signup_for_activity


class SignupCapacityTests(unittest.TestCase):
    def test_full_activity_rejects_signup_without_mutating_roster(self):
        activity = {
            "max_participants": 2,
            "participants": ["one@example.com", "two@example.com"],
        }

        with patch.dict(activities, {"Chess Club": activity}):
            with self.assertRaises(HTTPException) as raised:
                signup_for_activity("Chess Club", "three@example.com")

        self.assertEqual(409, raised.exception.status_code)
        self.assertEqual(2, len(activity["participants"]))

    def test_signup_for_last_spot_succeeds_but_next_signup_is_rejected(self):
        activity = {
            "max_participants": 2,
            "participants": ["one@example.com"],
        }

        with patch.dict(activities, {"Chess Club": activity}):
            response = signup_for_activity("Chess Club", "two@example.com")
            with self.assertRaises(HTTPException) as raised:
                signup_for_activity("Chess Club", "three@example.com")

        self.assertEqual("Signed up two@example.com for Chess Club", response["message"])
        self.assertEqual(409, raised.exception.status_code)
        self.assertEqual(["one@example.com", "two@example.com"], activity["participants"])

    def test_concurrent_signups_do_not_exceed_capacity(self):
        activity = {
            "max_participants": 1,
            "participants": [],
        }

        def signup(index):
            try:
                signup_for_activity("Chess Club", f"student{index}@example.com")
                return True
            except HTTPException:
                return False

        with patch.dict(activities, {"Chess Club": activity}):
            with ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(signup, range(8)))

        self.assertEqual(1, sum(results))
        self.assertEqual(1, len(activity["participants"]))


if __name__ == "__main__":
    unittest.main()