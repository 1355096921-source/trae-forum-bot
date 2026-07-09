import time
import random
import urllib.request
import subprocess
import os
import shutil
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


def is_debug_port_available(port: int, timeout: float = 3.0) -> bool:
    """
    检测指定端口是否真的有 Edge DevTools 协议服务在运行。
    通过访问 /json/version 接口验证，避免 Selenium 盲目连接导致挂起。
    """
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/json/version", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def find_edge_executable():
    """
    查找 Edge 浏览器可执行文件路径。
    优先查找正式版，其次是 Dev/Canary 版。
    """
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge Dev\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge Dev\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge Canary\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge Canary\Application\msedge.exe",
    ]
    for path in edge_paths:
        if os.path.exists(path):
            return path

    edge_found = shutil.which("msedge")
    if edge_found:
        return edge_found

    return None


def start_edge_with_debug(port: int):
    """
    通过 subprocess 直接启动 Edge 浏览器（不通过 Selenium），开启 remote debugging。
    这样启动的浏览器进程独立于 Python，Python 退出后浏览器不会关闭。
    """
    edge_path = find_edge_executable()
    if not edge_path:
        raise RuntimeError("未找到 Edge 浏览器可执行文件，请确保 Edge 已安装")

    print(f"[浏览器] 通过 subprocess 启动 Edge: {edge_path}")
    subprocess.Popen(
        [
            edge_path,
            "--start-maximized",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            f"--remote-debugging-port={port}",
            "--user-data-dir=" + os.path.join(os.path.dirname(__file__), "edge_profile"),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    print(f"[浏览器] 等待 DevTools 服务启动...")
    for _ in range(30):
        if is_debug_port_available(port):
            print(f"[浏览器] DevTools 服务已启动")
            return
        time.sleep(1)
    raise RuntimeError(f"等待 DevTools 服务启动超时 (端口 {port})")


def get_or_create_driver(debug_port: int = 9222):
    """
    尝试连接已有浏览器（通过 remote debugging port）。
    如果失败，则通过 subprocess 启动新浏览器（独立进程），再连接。
    返回 (driver, is_reused)。
    """
    if is_debug_port_available(debug_port):
        try:
            reconnect_options = Options()
            reconnect_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
            driver = webdriver.Edge(options=reconnect_options)
            print(f"[浏览器] 成功复用已有浏览器 (端口 {debug_port})")
            return driver, True
        except Exception as e:
            print(f"[浏览器] 端口可用但连接失败: {e}，将启动新浏览器")

    print(f"[浏览器] 未检测到可用浏览器，启动新实例...")
    start_edge_with_debug(debug_port)

    reconnect_options = Options()
    reconnect_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    try:
        driver = webdriver.Edge(options=reconnect_options)
    except Exception as e:
        print(f"连接浏览器失败: {e}")
        from selenium.webdriver.edge.service import Service
        try:
            service = Service()
            driver = webdriver.Edge(service=service, options=reconnect_options)
        except Exception as e2:
            print(f"再次失败: {e2}")
            raise

    return driver, False


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
    selectors = [
        (".topic-meta-data .names .username a", "text"),
        (".topic-body a[data-user-card]", "data-user-card"),
        (".topic-post .username a", "text"),
        (".names .username a", "text"),
        ("a[data-user-card]", "data-user-card"),
    ]
    for selector, attr in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            if attr == "text":
                username = element.text.strip()
            else:
                username = element.get_attribute(attr)
            if username:
                return username.strip()
        except Exception:
            continue
    return ""


def check_vote_status(driver):
    try:
        # 使用 presence_of_element_located 而不是 element_to_be_clickable
        # 因为 "已投票" 状态的按钮可能是 disabled 的，element_to_be_clickable 会超时
        vote_button = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".vote-button"))
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

    print("\n[1/5] 启动 Edge 浏览器...")
    DEBUG_PORT = 9222
    try:
        driver, is_reused = get_or_create_driver(debug_port=DEBUG_PORT)
    except Exception as e:
        print(f"浏览器启动失败: {e}")
        print("请确保 Edge 浏览器已安装，且版本与 Selenium 兼容")
        return

    if not is_reused:
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
    else:
        print("[2/5] 复用已有浏览器，跳过登录步骤")
        driver.get(config.target_category_url)
        time.sleep(3)

    print("[4/5] 获取帖子列表...")
    try:
        discourse = DiscourseClient({})
        all_topics = []
        page = 0
        while True:
            topics = discourse.get_latest_topics(config.category_slug, config.category_id, page=page)
            if not topics:
                break
            all_topics.extend(topics)
            # 如果本页返回的帖子数 < 30，说明是最后一页
            if len(topics) < 30:
                break
            # 如果已获取足够多（max + 20 缓冲），停止翻页
            if len(all_topics) >= config.max_comments_per_run + 20:
                break
            page += 1

        if not all_topics:
            print("未获取到任何主题，任务结束")
            if not is_reused:
                driver.quit()
            return
        print(f"获取到 {len(all_topics)} 个主题（共 {page + 1} 页）")
    except Exception as e:
        print(f"获取帖子列表失败: {e}")
        if not is_reused:
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
    for topic in all_topics:
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

    total_pages = page + 1 if 'page' in locals() else 1
    print("\n" + "-" * 50)
    print("执行摘要:")
    print(f"  获取主题总数: {len(all_topics)}（{total_pages} 页）")
    print(f"  共处理主题: {processed}")
    print(f"  处理成功: {success_count}")
    print(f"  已评价跳过: {skip_commented_count}")
    print(f"  帖子黑名单跳过: {skip_blacklist_count}")
    print(f"  用户黑名单跳过: {skip_user_blacklist_count}")
    print(f"  已投票跳过: {skip_already_voted_count}")
    print("=" * 50)

    print("\n任务完成！")
    if is_reused:
        print("浏览器继续保留，您可以再次运行脚本复用。")
    else:
        print("浏览器已保留（请勿关闭窗口，以便下次复用）。")
        print("如需关闭，请手动关闭浏览器窗口。")


if __name__ == "__main__":
    main()
