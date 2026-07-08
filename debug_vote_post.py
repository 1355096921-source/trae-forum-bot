import requests
from config import config

BASE_URL = "https://forum.trae.cn"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
})
session.cookies.update(config.discourse_cookies)

csrf_url = f"{BASE_URL}/session/csrf.json"
csrf = session.get(csrf_url, timeout=30).json().get("csrf", "")
session.headers["X-CSRF-Token"] = csrf

print(f"CSRF Token: {csrf}")

POST_ID = 107759
TOPIC_ID = 22549

print(f"\n=== 尝试对帖子 {POST_ID} 投票 ===")
vote_endpoints = [
    f"/posts/{POST_ID}/vote",
    f"/posts/{POST_ID}/vote.json",
    f"/post_actions/{POST_ID}",
    f"/post_actions/{POST_ID}/vote",
]

for endpoint in vote_endpoints:
    url = f"{BASE_URL}{endpoint}"
    print(f"\n尝试: {endpoint}")
    try:
        response = session.post(url, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:300]}")
    except Exception as e:
        print(f"错误: {e}")

print(f"\n=== 尝试 POST 请求到 /post_actions ===")
url = f"{BASE_URL}/post_actions"
payload = {"id": POST_ID, "action_type": "vote"}
print(f"请求: POST {url}")
print(f"参数: {payload}")
try:
    response = session.post(url, json=payload, timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:300]}")
except Exception as e:
    print(f"错误: {e}")

print(f"\n=== 尝试带 action_type 的投票 ===")
url = f"{BASE_URL}/posts/{POST_ID}/actions"
payload = {"id": POST_ID, "action_type": "vote"}
print(f"请求: POST {url}")
print(f"参数: {payload}")
try:
    response = session.post(url, json=payload, timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:300]}")
except Exception as e:
    print(f"错误: {e}")
