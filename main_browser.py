import time
import random
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from config import config
from deepseek_client import DeepSeekClient
from comment_generator import CommentGenerator
from state_manager import StateManager
from skip_list_manager import SkipListManager
from user_blacklist_manager import UserBlacklistManager
from discourse_client import DiscourseClient


def perform_vote(driver, topic_id):
    try:
        vote_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".vote-button"))
        )
        button_text = vote_button.text.strip()
        print(f"  [投票] 找到投票按钮: '{button_text}'")

        if "已投票" not in button_text:
            vote_button.click()
            print("  [投票] 点击投票按钮")
            time.sleep(2)
            return True
        else:
            print("  [投票] 已投票，跳过")
            return True
    except Exception as e:
        print(f"  [投票] 失败: {e}")
        return False


def perform_comment(driver, comment):
    try:
        reply_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".reply"))
        )
        reply_button.click()
        print("  [评论] 点击回复按钮成功")

        time.sleep(3)

        driver.execute_script(f"document.querySelector('.ProseMirror').innerHTML = '<p>{comment}</p>';")
        print(f"  [评论] 输入评论内容: {comment[:30]}...")

        time.sleep(1)

        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-primary.create:not(.topic-footer-button)"))
        )
        submit_button.click()
        print("  [评论] 点击回复按钮提交")

        time.sleep(3)

        try:
            confirm_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".modal button.btn-primary"))
            )
            confirm_btn.click()
            print("  [评论] 点击审批弹窗确定按钮")
        except Exception:
            print("  [评论] 未出现审批弹窗")

        return True
    except Exception as e:
        print(f"  [评论] 失败: {e}")
        return False


def get_topic_content(driver):
    try:
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )
        title = title_element.text.strip()

        body_element = driver.find_element(By.CSS_SELECTOR, ".topic-body .cooked")
        body_text = body_element.text.strip()[:500]

        return title, body_text
    except Exception as e:
        print(f"  [获取内容] 失败: {e}")
        return "", ""


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
    print("=" * 50)
    print("论坛自动化评论任务 - 浏览器模式")
    print("=" * 50)
    print(f"目标分类: {config.target_category_url}")
    print(f"最大评论数: {config.max_comments_per_run}")

    state = StateManager()
    skip_list = SkipListManager()
    user_blacklist = UserBlacklistManager()
    print(f"已评价记录: {len(state._commented_ids)} 条")
    print(f"帖子黑名单: {len(skip_list.skip_ids)} 条")
    print(f"用户黑名单: {len(user_blacklist.blacklisted_usernames)} 条")
    print("-" * 50)

    edge_options = Options()
    edge_options.add_argument("--start-maximized")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")

    print("\n[1/5] 启动 Edge 浏览器...")
    try:
        driver = webdriver.Edge(options=edge_options)
    except Exception as e:
        print(f"启动失败: {e}")
        print("尝试使用 Edge 驱动服务...")
        from selenium.webdriver.edge.service import Service
        try:
            service = Service()
            driver = webdriver.Edge(service=service, options=edge_options)
        except Exception as e2:
            print(f"再次失败: {e2}")
            print("请确保 Edge 浏览器已安装，且版本与 Selenium 兼容")
            return

    print("[2/5] 访问帖子页面...")
    driver.get(config.target_category_url)
    time.sleep(3)

    print("[3/5] 请在接下来的 60 秒内完成登录...")
    print("=" * 50)
    print("倒计时开始，请在浏览器中登录您的账号")
    print("=" * 50)
    for i in range(60, 0, -1):
        print(f"\r剩余时间: {i} 秒", end="")
        time.sleep(1)
    print("\n" + "=" * 50)
    print("登录时间结束，继续执行...")
    print("=" * 50)

    driver.refresh()
    time.sleep(3)

    print("[4/5] 获取帖子列表...")
    try:
        discourse = DiscourseClient({})
        topics = discourse.get_latest_topics(config.category_slug, config.category_id)
        if not topics:
            print("未获取到任何主题，任务结束")
            driver.quit()
            return
        print(f"获取到 {len(topics)} 个主题")
    except Exception as e:
        print(f"获取帖子列表失败: {e}")
        driver.quit()
        return

    deepseek = DeepSeekClient(config.deepseek_api_key, config.deepseek_base_url, config.deepseek_model)
    generator = CommentGenerator(deepseek)

    success_count = 0
    skip_commented_count = 0
    skip_blacklist_count = 0
    skip_user_blacklist_count = 0
    skip_already_voted_count = 0
    processed = 0

    print("[5/5] 开始处理帖子...")
    for topic in topics:
        if success_count >= config.max_comments_per_run:
            print(f"\n已达本次最大评论数上限 ({config.max_comments_per_run})，任务终止")
            break

        topic_id = topic.get("id")
        title = topic.get("title", "")
        topic_poster = topic.get("posters", [{}])[0].get("username", "") if topic.get("posters") else ""
        if not topic_id:
            continue

        processed += 1

        if skip_list.is_skipped(topic_id):
            print(f"[{processed}] 主题 {topic_id} - 帖子黑名单跳过")
            skip_blacklist_count += 1
            continue

        if state.has_commented(topic_id):
            print(f"[{processed}] 主题 {topic_id} - 已评价跳过")
            skip_commented_count += 1
            continue

        if topic_poster and user_blacklist.is_blacklisted(topic_poster):
            print(f"[{processed}] 主题 {topic_id} - 用户黑名单跳过 ({topic_poster})")
            skip_user_blacklist_count += 1
            continue

        print(f"\n[{processed}] 主题 {topic_id} - {title[:30]}...")

        try:
            topic_url = f"https://forum.trae.cn/t/topic/{topic_id}"
            driver.get(topic_url)
            time.sleep(5)

            vote_status = check_vote_status(driver)
            author = get_topic_author(driver)
            if not author:
                author = topic_poster

            print(f"  [用户] 发帖人: {author}")

            if "已投票" in vote_status or "已投票" in vote_status:
                print(f"  [投票] 已投票 ({vote_status})，跳过整个帖子")
                skip_already_voted_count += 1
                if author:
                    user_blacklist.add(author)
                    print(f"  [用户] 已将 {author} 加入用户黑名单")
                continue

            vote_success = perform_vote(driver, topic_id)

            page_title, body_text = get_topic_content(driver)
            if not page_title:
                page_title = title

            print(f"  [内容] 标题: {page_title[:30]}...")

            comment = generator.generate(page_title, body_text)
            print(f"  [内容] 生成评论: {comment}")

            comment_success = perform_comment(driver, comment)

            if vote_success and comment_success:
                state.record_comment(topic_id)
                success_count += 1
                if author:
                    user_blacklist.add(author)
                    print(f"  [用户] 已将 {author} 加入用户黑名单")
                print(f"  [结果] 处理成功")
            else:
                print(f"  [结果] 处理失败")

        except Exception as e:
            print(f"[{processed}] 主题 {topic_id} - 处理异常: {e}")
            continue

        delay = random.uniform(3, 5)
        print(f"  [等待] 等待 {delay:.1f} 秒...")
        time.sleep(delay)

    print("\n" + "-" * 50)
    print("执行摘要:")
    print(f"  共处理主题: {processed}")
    print(f"  处理成功: {success_count}")
    print(f"  已评价跳过: {skip_commented_count}")
    print(f"  帖子黑名单跳过: {skip_blacklist_count}")
    print(f"  用户黑名单跳过: {skip_user_blacklist_count}")
    print(f"  已投票跳过: {skip_already_voted_count}")
    print("=" * 50)

    print("\n任务完成！浏览器已保留，您可以继续使用。")
    print("按回车键关闭浏览器并退出...")
    input()
    driver.quit()


if __name__ == "__main__":
    main()
