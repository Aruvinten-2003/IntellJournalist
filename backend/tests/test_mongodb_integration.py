"""Optional MongoDB integration test.

Run with ``RUN_MONGODB_TESTS=1`` while MongoDB is available.
"""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from pymongo import MongoClient

from backend.config import settings
from backend.main import app


@unittest.skipUnless(
    os.getenv("RUN_MONGODB_TESTS") == "1",
    "Set RUN_MONGODB_TESTS=1 to exercise MongoDB",
)
class MongoDBIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.email = f"mongodb-test-{uuid4().hex[:10]}@example.com"
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)
        client = MongoClient(settings.mongodb_url)
        database = client[settings.mongodb_database]
        user = database.users.find_one({"email": cls.email})
        if user:
            user_id = str(user["_id"])
            conversations = list(database.conversations.find({"user_id": user_id}))
            conversation_ids = [str(row["_id"]) for row in conversations]
            database.messages.delete_many({"conversation_id": {"$in": conversation_ids}})
            database.conversations.delete_many({"user_id": user_id})
            database.bookmarks.delete_many({"user_id": user_id})
            database.users.delete_one({"_id": user["_id"]})
        client.close()

    def test_mongodb_user_bookmark_and_conversation_flow(self) -> None:
        health = self.client.get("/api/health")
        self.assertEqual(health.json()["database"]["status"], "connected")

        registration = self.client.post(
            "/api/auth/register",
            json={
                "first_name": "MongoDB",
                "last_name": "Test",
                "email": self.email,
                "password": "SafeTestPassword1!",
                "country": "Malaysia",
                "language": "English",
            },
        )
        self.assertEqual(registration.status_code, 201, registration.text)
        headers = {
            "Authorization": f"Bearer {registration.json()['access_token']}"
        }

        article_id = self.client.get("/api/news/articles").json()[0]["id"]
        bookmarked = self.client.post(
            f"/api/news/bookmarks/{article_id}",
            headers=headers,
        )
        self.assertEqual(bookmarked.status_code, 200, bookmarked.text)

        chat = self.client.post(
            "/api/chat/ask",
            headers=headers,
            json={"question": "Summarise the leading world report.", "scope": "world"},
        )
        self.assertEqual(chat.status_code, 200, chat.text)
        self.assertTrue(chat.json()["conversation_id"])

        conversations = self.client.get("/api/chat/conversations", headers=headers)
        self.assertEqual(conversations.status_code, 200, conversations.text)
        self.assertTrue(conversations.json())
