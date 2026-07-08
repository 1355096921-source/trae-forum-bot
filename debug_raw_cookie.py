import requests
from config import config

BASE_URL = "https://forum.trae.cn"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": config.discourse_cookie_raw,
})

print("=== 用原始 Cookie 字符串方式 ===")

print("\n[1] 获取 CSRF Token")
csrf_url = f"{BASE_URL}/session/csrf.json"
response = session.get(csrf_url, timeout=30)
data = response.json()
csrf = data.get("csrf") or data.get("csrf_token", "")
print(f"CSRF Token: {csrf}")
session.headers["X-CSRF-Token"] = csrf

print("\n[2] 获取帖子详情")
response = session.get(f"{BASE_URL}/t/22549.json", timeout=30)
data = response.json()
print(f"标题: {data.get('title')}")
print(f"can_vote: {data.get('can_vote')}")
print(f"user_voted: {data.get('user_voted')}")

POST_ID = data.get("post_stream", {}).get("posts", [{}])[0].get("id", 0)
print(f"首帖 ID: {POST_ID}")

print("\n[3] 尝试投票")
url = f"{BASE_URL}/post_actions"
payload = {"id": POST_ID, "action_type": "vote"}
print(f"POST {url}")
print(f"参数: {payload}")
response = session.post(url, json=payload, timeout=10)
print(f"状态码: {response.status_code}")
print(f"响应: {response.text[:500]}")

print("\n[4] 尝试评论")
url = f"{BASE_URL}/posts"
payload = {"topic_id": 22549, "raw": "已投票，测试评论！"}
print(f"POST {url}")
print(f"参数: {payload}")
response = session.post(url, json=payload, timeout=10)
print(f"状态码: {response.status_code}")
print(f"响应: {response.text[:500]}")

print("\n[5] 尝试发送表单数据而不是 JSON")
url = f"{BASE_URL}/posts"
response = session.post(url, data={"topic_id": 22549, "raw": "已投票，测试评论！"}, timeout=10)
print(f"状态码: {response.status_code}")
print(f"响应: {response.text[:500]}")
