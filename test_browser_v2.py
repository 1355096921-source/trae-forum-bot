import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from config import config
from deepseek_client import DeepSeekClient
from comment_generator import CommentGenerator


def main():
    TEST_TOPIC_ID = 22549
    topic_url = f"https://forum.trae.cn/t/topic/{TEST_TOPIC_ID}"

    print("=" * 50)
    print(f"浏览器自动化模式 - 帖子 {TEST_TOPIC_ID}")
    print("=" * 50)

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    print("\n[1/6] 启动浏览器...")
    driver = webdriver.Chrome(options=chrome_options)

    print("[2/6] 访问帖子页面...")
    driver.get(topic_url)
    time.sleep(5)

    print("[3/6] 设置登录状态...")
    driver.delete_all_cookies()
    for key, value in config.discourse_cookies.items():
        try:
            driver.add_cookie({
                "name": key,
                "value": value,
                "domain": ".trae.cn",
                "path": "/"
            })
        except Exception as e:
            print(f"  跳过 Cookie {key}: {e}")

    print("[4/6] 刷新页面...")
    driver.get(topic_url)
    time.sleep(5)

    print("[5/6] 查找并点击投票按钮...")
    try:
        vote_button = None
        selectors = [
            "button.widget-button",
            ".widget-button",
            ".vote-button",
            "button[data-action='vote']",
            "div[data-action='vote']",
            "button:contains('投票')",
        ]

        for selector in selectors:
            try:
                vote_button = driver.find_element(By.CSS_SELECTOR, selector)
                if vote_button.is_displayed():
                    break
            except:
                continue

        if vote_button:
            button_text = vote_button.text.strip()
            print(f"找到投票按钮: '{button_text}'")

            if "已投票" not in button_text:
                try:
                    vote_button.click()
                    print("点击投票按钮")
                    time.sleep(2)

                    try:
                        new_text = vote_button.text.strip()
                        print(f"投票后状态: '{new_text}'")
                    except:
                        print("投票成功")
                except ElementClickInterceptedException:
                    print("按钮被遮挡，尝试滚动后点击")
                    driver.execute_script("arguments[0].scrollIntoView(true);", vote_button)
                    time.sleep(1)
                    vote_button.click()
                    print("点击投票按钮")
            else:
                print("已投票，跳过")
        else:
            print("未找到投票按钮")
    except Exception as e:
        print(f"投票失败: {e}")

    print("\n[6/6] 生成并发表评论...")
    try:
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1, .fancy-title, .topic-title"))
        )
        title = title_element.text.strip()
        print(f"帖子标题: {title}")

        body_element = driver.find_element(By.CSS_SELECTOR, ".post .cooked, .topic-body")
        body_text = body_element.text.strip()

        deepseek = DeepSeekClient(config.deepseek_api_key, config.deepseek_base_url, config.deepseek_model)
        generator = CommentGenerator(deepseek)
        comment = generator.generate(title, body_text)
        print(f"生成评论: {comment}")

        reply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".reply-button, button[data-action='reply'], .create-topic"))
        )
        reply_button.click()
        print("点击回复按钮")
        time.sleep(3)

        textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".d-editor-textarea, textarea"))
        )
        textarea.clear()
        textarea.send_keys(comment)
        print("输入评论内容")
        time.sleep(1)

        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-primary, button[data-action='create']"))
        )
        submit_button.click()
        print("点击提交按钮")
        time.sleep(5)

        print("评论发表成功!")
    except (TimeoutException, NoSuchElementException) as e:
        print(f"发表评论失败: {e}")

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
