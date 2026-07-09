import requests
from typing import List, Dict, Any

BASE_URL = "https://forum.trae.cn"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}


class DiscourseClient:
    def __init__(self, cookies: Dict[str, str]):
        self.cookies = cookies
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.cookies.update(cookies)

    def get_latest_topics(self, category_slug: str, category_id: str, page: int = 0) -> List[Dict[str, Any]]:
        url = f"{BASE_URL}/c/{category_slug}/{category_id}/l/latest.json?page={page}"
        response = self.session.get(url, timeout=30)
        self._check_response(response)
        data = response.json()
        topic_list = data.get("topic_list", {})
        topics = topic_list.get("topics", [])
        return topics

    def get_topic_detail(self, topic_id: int) -> Dict[str, Any]:
        url = f"{BASE_URL}/t/{topic_id}.json"
        response = self.session.get(url, timeout=30)
        self._check_response(response)
        return response.json()

    def create_reply(self, topic_id: int, raw_content: str) -> Dict[str, Any]:
        self._ensure_csrf_token()
        url = f"{BASE_URL}/posts"
        payload = {
            "topic_id": topic_id,
            "raw": raw_content,
        }
        response = self.session.post(url, json=payload, timeout=30)
        self._check_response(response)
        return response.json()

    def vote_topic(self, topic_id: int) -> Dict[str, Any]:
        self._ensure_csrf_token()
        url = f"{BASE_URL}/t/{topic_id}/vote"
        response = self.session.post(url, timeout=30)
        self._check_response(response)
        return response.json()

    def _ensure_csrf_token(self):
        if "X-CSRF-Token" in self.session.headers:
            return
        csrf_url = f"{BASE_URL}/session/csrf.json"
        response = self.session.get(csrf_url, timeout=30)
        self._check_response(response)
        data = response.json()
        csrf_token = data.get("csrf") or data.get("csrf_token", "")
        if csrf_token:
            self.session.headers["X-CSRF-Token"] = csrf_token

    @staticmethod
    def _check_response(response: requests.Response):
        if response.status_code == 403:
            raise PermissionError("请求被禁止 (403)，Cookie 可能已失效，请重新登录并更新 DISCOURSE_COOKIE")
        if response.status_code == 401:
            raise PermissionError("未授权 (401)，Cookie 可能已失效，请重新登录并更新 DISCOURSE_COOKIE")
        response.raise_for_status()


def extract_topic_body(topic_detail: Dict[str, Any]) -> str:
    posts = topic_detail.get("post_stream", {}).get("posts", [])
    if not posts:
        return ""
    first_post = posts[0]
    cooked = first_post.get("cooked", "")
    return cooked
