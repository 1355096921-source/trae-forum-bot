import requests
from config import config

BASE_URL = "https://forum.trae.cn"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
})
session.cookies.update(config.discourse_cookies)

print("=== 检查当前 Cookie ===")
print(f"Cookie 键数量: {len(config.discourse_cookies)}")
print(f"是否包含 _forum_session: {'_forum_session' in config.discourse_cookies}")
print(f"是否包含 _t: {'_t' in config.discourse_cookies}")

print("\n=== 获取用户信息 ===")
url = f"{BASE_URL}/session/current.json"
try:
    response = session.get(url, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text[:500]}")
except Exception as e:
    print(f"请求失败: {e}")

print("\n=== 获取帖子列表 ===")
url = f"{BASE_URL}/c/38-category/40-category/40/l/latest.json"
try:
    response = session.get(url, timeout=30)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        topics = data.get("topic_list", {}).get("topics", [])
        print(f"获取到 {len(topics)} 个帖子")
        if topics:
            print(f"第一个帖子: ID={topics[0]['id']}, 标题={topics[0]['title']}")
except Exception as e:
    print(f"请求失败: {e}")

print("\n=== 尝试直接用 Cookie 字符串方式 ===")
session2 = requests.Session()
session2.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": config.discourse_cookie_raw,
})
url = f"{BASE_URL}/session/current.json"
try:
    response = session2.get(url, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text[:500]}")
except Exception as e:
    print(f"请求失败: {e}")
