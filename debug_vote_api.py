import requests
from config import config

BASE_URL = "https://forum.trae.cn"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
})
session.cookies.update(config.discourse_cookies)

csrf_url = f"{BASE_URL}/session/csrf.json"
response = session.get(csrf_url, timeout=30)
data = response.json()
csrf = data.get("csrf") or data.get("csrf_token", "")
session.headers["X-CSRF-Token"] = csrf
print(f"CSRF Token: {csrf}")

topic_id = 22549
vote_endpoints = [
    f"/t/{topic_id}/vote",
    f"/topics/{topic_id}/vote",
    f"/t/topic/{topic_id}/vote",
    f"/posts/{topic_id}/vote",
]

print(f"\n=== 测试投票 API 端点 ===")
for endpoint in vote_endpoints:
    url = f"{BASE_URL}{endpoint}"
    try:
        response = session.post(url, timeout=30)
        print(f"{endpoint}: 状态码 {response.status_code}")
        if response.status_code == 200:
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"{endpoint}: 错误 {e}")

print(f"\n=== 测试 GET 请求查看投票信息 ===")
get_endpoints = [
    f"/t/{topic_id}.json",
    f"/topics/{topic_id}.json",
]
for endpoint in get_endpoints:
    url = f"{BASE_URL}{endpoint}"
    try:
        response = session.get(url, timeout=30)
        print(f"{endpoint}: 状态码 {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            vote_keys = [k for k in data.keys() if 'vote' in k.lower()]
            print(f"  投票相关字段: {vote_keys}")
            for k in vote_keys:
                print(f"    {k}: {data[k]}")
    except Exception as e:
        print(f"{endpoint}: 错误 {e}")
