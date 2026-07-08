import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from user_blacklist_manager import UserBlacklistManager


def get_topic_author(driver):
    try:
        author_element = driver.find_element(By.CSS_SELECTOR, ".topic-meta-data .names .username a")
        username = author_element.text.strip()
        return username
    except Exception:
        try:
            author_link = driver.find_element(By.CSS_SELECTOR, ".topic-body a[data-user-card]")
            username = author_link.get_attribute("data-user-card")
            if username:
                return username.strip()
        except Exception:
            pass
        return ""


def check_vote_status(driver):
    try:
        vote_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".vote-button"))
        )
        button_text = vote_button.text.strip()
        return button_text
    except Exception as e:
        print(f"  [投票状态] 获取失败: {e}")
        return ""


def main():
    TEST_TOPICS = [
        76750,
        77161,
        79386,
        77151,
    ]

    print("=" * 50)
    print("用户黑名单与已投票检测 - 测试脚本")
    print("=" * 50)

    user_blacklist = UserBlacklistManager()
    print(f"初始用户黑名单: {len(user_blacklist.blacklisted_usernames)} 条")
    print("-" * 50)

    edge_options = Options()
    edge_options.add_argument("--start-maximized")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")

    print("\n启动 Edge 浏览器...")
    driver = webdriver.Edge(options=edge_options)

    print("访问论坛首页...")
    driver.get("https://forum.trae.cn/")
    time.sleep(3)

    print("\n请在接下来的 60 秒内完成登录...")
    print("=" * 50)
    for i in range(60, 0, -1):
        print(f"\r剩余时间: {i} 秒", end="")
        time.sleep(1)
    print("\n" + "=" * 50)

    driver.refresh()
    time.sleep(3)

    print("\n开始测试指定帖子...")
    for idx, topic_id in enumerate(TEST_TOPICS, 1):
        print(f"\n[{idx}/{len(TEST_TOPICS)}] 测试帖子 {topic_id}")
        try:
            driver.get(f"https://forum.trae.cn/t/topic/{topic_id}")
            time.sleep(5)

            vote_status = check_vote_status(driver)
            author = get_topic_author(driver)

            print(f"  发帖人: {author or '未获取到'}")
            print(f"  投票按钮: '{vote_status}'")

            is_voted = "已投票" in vote_status
            print(f"  是否已投票: {'是' if is_voted else '否'}")

            if author:
                in_blacklist = user_blacklist.is_blacklisted(author)
                print(f"  是否在用户黑名单: {'是' if in_blacklist else '否'}")

                if is_voted and not in_blacklist:
                    user_blacklist.add(author)
                    print(f"  -> 已将 {author} 加入用户黑名单")
                elif not is_voted and in_blacklist:
                    print(f"  -> 因用户黑名单跳过")

        except Exception as e:
            print(f"  测试失败: {e}")

    print("\n" + "=" * 50)
    print("测试完成")
    print(f"最终用户黑名单: {len(user_blacklist.blacklisted_usernames)} 条")
    for name in user_blacklist.blacklisted_usernames:
        print(f"  - {name}")
    print("=" * 50)

    print("\n浏览器将在 10 秒后关闭...")
    time.sleep(10)
    driver.quit()


if __name__ == "__main__":
    main()
