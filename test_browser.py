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

    print("\n[1/6] 启动浏览器...")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(topic_url)

    print("[2/6] 设置 Cookie...")
    driver.delete_all_cookies()
    for key, value in config.discourse_cookies.items():
        driver.add_cookie({"name": key, "value": value, "domain": ".trae.cn"})

    print("[3/6] 刷新页面...")
    driver.get(topic_url)
    time.sleep(3)

    print("[4/6] 查找并点击投票按钮...")
    try:
        vote_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".vote-button, .btn-vote, button[data-action='vote'], .widget-button"))
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
    except (TimeoutException, NoSuchElementException) as e:
        print(f"未找到投票按钮或点击失败: {e}")

    print("\n[5/6] 生成评论...")
    try:
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".fancy-title, .topic-title, h1, h2"))
        )
        title = title_element.text.strip()

        body_element = driver.find_element(By.CSS_SELECTOR, ".post .cooked, .topic-body, .post-content")
        body_text = body_element.text.strip()

        deepseek = DeepSeekClient(config.deepseek_api_key, config.deepseek_base_url, config.deepseek_model)
        generator = CommentGenerator(deepseek)
        comment = generator.generate(title, body_text)
        print(f"生成评论: {comment}")
    except Exception as e:
        print(f"生成评论失败: {e}")
        comment = "已投票，很棒的分享！"

    print("\n[6/6] 发表评论...")
    try:
        reply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".reply-button, button[data-action='reply'], .create-topic, .add-reply"))
        )
        reply_button.click()
        print("点击回复按钮")
        time.sleep(2)

        textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[name='reply'], textarea[data-post-id], .d-editor-textarea"))
        )
        textarea.clear()
        textarea.send_keys(comment)
        print(f"输入评论内容")

        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-primary, button[data-action='create'], .submit-btn"))
        )
        submit_button.click()
        print("点击提交按钮")
        time.sleep(3)

        print("评论发表成功!")
    except (TimeoutException, NoSuchElementException) as e:
        print(f"发表评论失败: {e}")

    print("\n" + "=" * 50)
    print("测试完成 - 请手动关闭浏览器")
    print("=" * 50)


if __name__ == "__main__":
    main()
