import json
from config import config
from discourse_client import DiscourseClient

TEST_TOPIC_ID = 22549

discourse = DiscourseClient(config.discourse_cookies)
detail = discourse.get_topic_detail(TEST_TOPIC_ID)

print("标题:", detail.get("title"))
print()
print("=== 顶层所有 key ===")
for key in sorted(detail.keys()):
    val = detail[key]
    if isinstance(val, (dict, list)):
        print(f"  {key}: {type(val).__name__} (len={len(val)})")
    else:
        print(f"  {key}: {val}")

print()
print("=== post_stream.posts[0] 所有 key ===")
posts = detail.get("post_stream", {}).get("posts", [])
if posts:
    first = posts[0]
    for key in sorted(first.keys()):
        val = first[key]
        if isinstance(val, (dict, list)):
            print(f"  {key}: {type(val).__name__} (len={len(val)})")
        elif key in ("cooked", "raw"):
            print(f"  {key}: {str(val)[:100]}...")
        else:
            print(f"  {key}: {val}")

print()
print("=== polls 相关字段 ===")
for key in detail.keys():
    if "poll" in key.lower():
        print(f"  {key}: {detail[key]}")

if posts:
    first = posts[0]
    for key in first.keys():
        if "poll" in key.lower():
            print(f"  posts[0].{key}: {first[key]}")
