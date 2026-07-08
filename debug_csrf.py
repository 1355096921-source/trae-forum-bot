import requests
from config import config

BASE_URL = "https://forum.trae.cn"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
})
session.cookies.update(config.discourse_cookies)

print("=== 测试 CSRF Token 获取 ===")
csrf_url = f"{BASE_URL}/session/csrf.json"
try:
    response = session.get(csrf_url, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    if response.status_code == 200:
        data = response.json()
        csrf = data.get("csrf") or data.get("csrf_token")
        print(f"获取到 CSRF Token: {csrf}")
        session.headers["X-CSRF-Token"] = csrf
except Exception as e:
    print(f"获取失败: {e}")

print("\n=== 测试带 CSRF 的评论请求 ===")
test_comment = "测试评论，已投票！"
post_url = f"{BASE_URL}/posts"
payload = {"topic_id": 22549, "raw": test_comment}
try:
    response = session.post(post_url, json=payload, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text[:500]}")
except Exception as e:
    print(f"请求失败: {e}")

print("\n=== 测试不带 JSON 的评论请求 ===")
try:
    response = session.post(post_url, data=payload, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text[:500]}")
except Exception as e:
    print(f"请求失败: {e}")
