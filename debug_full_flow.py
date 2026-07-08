import requests
from config import config

BASE_URL = "https://forum.trae.cn"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://forum.trae.cn/",
})
session.cookies.update(config.discourse_cookies)

print("=== 步骤1: 获取 CSRF Token ===")
csrf_url = f"{BASE_URL}/session/csrf.json"
response = session.get(csrf_url, timeout=30)
data = response.json()
csrf = data.get("csrf") or data.get("csrf_token", "")
print(f"CSRF Token: {csrf}")
session.headers["X-CSRF-Token"] = csrf

print("\n=== 步骤2: 获取帖子详情 ===")
topic_url = f"{BASE_URL}/t/22549.json"
response = session.get(topic_url, timeout=30)
print(f"状态码: {response.status_code}")
data = response.json()
print(f"标题: {data.get('title')}")
print(f"can_vote: {data.get('can_vote')}")
print(f"user_voted: {data.get('user_voted')}")

print("\n=== 步骤3: 尝试投票 ===")
vote_endpoints = [
    f"/t/22549/vote",
    f"/topics/22549/vote",
    f"/vote/topic/22549",
]
for endpoint in vote_endpoints:
    url = f"{BASE_URL}{endpoint}"
    print(f"\n尝试: {endpoint}")
    try:
        response = session.post(url, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:300]}")
    except Exception as e:
        print(f"错误: {e}")

print("\n=== 步骤4: 尝试评论 ===")
post_url = f"{BASE_URL}/posts"
payload = {"topic_id": 22549, "raw": "已投票，测试评论！"}
print(f"\n尝试发表评论...")
try:
    response = session.post(post_url, json=payload, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
except Exception as e:
    print(f"错误: {e}")

print("\n=== 步骤5: 尝试带更多头的评论 ===")
session2 = requests.Session()
session2.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": f"{BASE_URL}/t/topic/22549",
    "Origin": "https://forum.trae.cn",
    "X-CSRF-Token": csrf,
    "Content-Type": "application/json;charset=UTF-8",
})
session2.cookies.update(config.discourse_cookies)
try:
    response = session2.post(post_url, json=payload, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
except Exception as e:
    print(f"错误: {e}")
