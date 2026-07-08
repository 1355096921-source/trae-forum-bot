import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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

    print("\n[1/4] 启动浏览器...")
    driver = webdriver.Chrome(options=chrome_options)

    print("[2/4] 访问帖子页面...")
    driver.get(topic_url)
    time.sleep(5)

    print("[3/4] 查找投票按钮并点击...")
    try:
        vote_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".widget-button"))
        )
        button_text = vote_button.text.strip()
        print(f"找到投票按钮: '{button_text}'")

        if "已投票" not in button_text:
            vote_button.click()
            print("点击投票按钮")
            time.sleep(2)
            new_text = vote_button.text.strip()
            print(f"投票后状态: '{new_text}'")
        else:
            print("已投票，跳过")
    except Exception as e:
        print(f"投票失败或未找到按钮: {e}")

    print("\n[4/4] 生成并发表评论...")
    try:
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )
        title = title_element.text.strip()

        body_element = driver.find_element(By.CSS_SELECTOR, ".post .cooked")
        body_text = body_element.text.strip()

        deepseek = DeepSeekClient(config.deepseek_api_key, config.deepseek_base_url, config.deepseek_model)
        generator = CommentGenerator(deepseek)
        comment = generator.generate(title, body_text)
        print(f"生成评论: {comment}")

        reply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".reply-button"))
        )
        reply_button.click()
        time.sleep(3)

        textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".d-editor-textarea"))
        )
        textarea.clear()
        textarea.send_keys(comment)
        time.sleep(1)

        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-primary"))
        )
        submit_button.click()
        time.sleep(5)

        print("评论发表成功!")
    except Exception as e:
        print(f"发表评论失败: {e}")

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
