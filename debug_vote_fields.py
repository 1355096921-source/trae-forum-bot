import requests
from config import config

BASE_URL = "https://forum.trae.cn"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
})
session.cookies.update(config.discourse_cookies)

print("=== 获取帖子详情 ===")
response = session.get(f"{BASE_URL}/t/22549.json", timeout=30)
data = response.json()

print("\n=== 所有包含 vote 的字段 ===")
def find_vote_keys(obj, prefix=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            if 'vote' in key.lower():
                print(f"{new_prefix}: {value}")
            find_vote_keys(value, new_prefix)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_prefix = f"{prefix}[{i}]"
            find_vote_keys(item, new_prefix)

find_vote_keys(data)

print("\n=== 主题顶层所有字段 ===")
for key in sorted(data.keys()):
    val = data[key]
    if isinstance(val, (dict, list)):
        print(f"  {key}: {type(val).__name__} (len={len(val)})")
    else:
        print(f"  {key}: {val}")

print("\n=== 尝试查看 first_post 的所有字段 ===")
posts = data.get("post_stream", {}).get("posts", [])
if posts:
    first = posts[0]
    for key in sorted(first.keys()):
        val = first[key]
        if isinstance(val, (dict, list)):
            print(f"  posts[0].{key}: {type(val).__name__} (len={len(val)})")
        elif key in ("cooked", "raw"):
            print(f"  posts[0].{key}: {str(val)[:100]}...")
        else:
            print(f"  posts[0].{key}: {val}")

print("\n=== 尝试不同的投票端点 ===")
vote_endpoints = [
    f"/t/topic/22549/vote",
    f"/vote/22549",
    f"/votes/topic/22549",
    f"/posts/22549/vote",
    f"/topics/22549/vote.json",
]

csrf_url = f"{BASE_URL}/session/csrf.json"
csrf = session.get(csrf_url, timeout=30).json().get("csrf", "")
session.headers["X-CSRF-Token"] = csrf

for endpoint in vote_endpoints:
    url = f"{BASE_URL}{endpoint}"
    print(f"\n尝试: {endpoint}")
    try:
        response = session.post(url, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"错误: {e}")
