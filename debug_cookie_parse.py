from config import config

print("=== Cookie 解析检查 ===")
print(f"原始 Cookie 长度: {len(config.discourse_cookie_raw)}")
print()

print("解析后的 Cookie 键值对:")
for key, value in config.discourse_cookies.items():
    print(f"  {key}: {value[:50]}... (长度: {len(value)})")

print()
print("=== 关键字段检查 ===")
print(f"_forum_session: {'_forum_session' in config.discourse_cookies}")
if '_forum_session' in config.discourse_cookies:
    print(f"  值长度: {len(config.discourse_cookies['_forum_session'])}")
    print(f"  值前50字符: {config.discourse_cookies['_forum_session'][:50]}")

print(f"_t: {'_t' in config.discourse_cookies}")
if '_t' in config.discourse_cookies:
    print(f"  值长度: {len(config.discourse_cookies['_t'])}")
    print(f"  值前50字符: {config.discourse_cookies['_t'][:50]}")

print()
print("=== 原始字符串中的位置 ===")
print(f"_forum_session 在原始字符串中的位置: {config.discourse_cookie_raw.find('_forum_session')}")
print(f"_t 在原始字符串中的位置: {config.discourse_cookie_raw.find('_t=')}")

print()
print("=== 检查是否有双引号包裹 ===")
if '"' in config.discourse_cookie_raw or "'" in config.discourse_cookie_raw:
    print("警告：Cookie 字符串中包含引号，可能导致解析错误！")
else:
    print("未发现引号问题")

print()
print("=== 检查等号处理 ===")
test_str = "_forum_session=abc=def"
parts = test_str.split("=")
print(f"简单等号分割: {parts}")
key, value = test_str.split("=", 1)
print(f"split('=', 1): key={key}, value={value}")
