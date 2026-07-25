"""API smoke tests that run without external services."""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import app


class APISmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        cls.email = f"reader-{uuid4().hex[:10]}@example.com"
        response = cls.client.post(
            "/api/auth/register",
            json={
                "first_name": "Test",
                "last_name": "Reader",
                "email": cls.email,
                "password": "SafeTestPassword1!",
                "country": "Malaysia",
                "language": "English",
            },
        )
        if response.status_code != 201:
            raise AssertionError(response.text)
        cls.token = response.json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    def test_health_and_frontend(self) -> None:
        self.assertEqual(self.client.get("/api/health").status_code, 200)
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_authentication(self) -> None:
        login = self.client.post(
            "/api/auth/login",
            json={"email": self.email, "password": "SafeTestPassword1!"},
        )
        self.assertEqual(login.status_code, 200)
        profile = self.client.get("/api/auth/me", headers=self.headers)
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["email"], self.email)

    def test_news_and_bookmarks(self) -> None:
        news = self.client.get("/api/news/articles")
        self.assertEqual(news.status_code, 200)
        article_id = news.json()[0]["id"]
        saved = self.client.post(
            f"/api/news/bookmarks/{article_id}",
            headers=self.headers,
        )
        self.assertEqual(saved.status_code, 200)
        bookmarks = self.client.get("/api/news/bookmarks", headers=self.headers)
        self.assertIn(article_id, {article["id"] for article in bookmarks.json()})
        removed = self.client.delete(
            f"/api/news/bookmarks/{article_id}",
            headers=self.headers,
        )
        self.assertEqual(removed.status_code, 200)

    def test_chat_fallback(self) -> None:
        response = self.client.post(
            "/api/chat/ask",
            json={"question": "What are the leading technology stories?", "scope": "technology"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["answer"])
        self.assertTrue(payload["sources"])


if __name__ == "__main__":
    unittest.main()
