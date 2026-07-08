import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
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
    print(f"Edge 浏览器自动化模式 - 帖子 {TEST_TOPIC_ID}")
    print("=" * 50)

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
    driver.get(topic_url)
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

    print("[4/4] 执行投票和评论...")
    try:
        vote_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".vote-button"))
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
        print(f"投票失败: {e}")

    try:
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )
        title = title_element.text.strip()
        print(f"帖子标题: {title}")

        body_element = driver.find_element(By.CSS_SELECTOR, ".topic-body .cooked")
        body_text = body_element.text.strip()[:500]

        deepseek = DeepSeekClient(config.deepseek_api_key, config.deepseek_base_url, config.deepseek_model)
        generator = CommentGenerator(deepseek)
        comment = generator.generate(title, body_text)
        print(f"生成评论: {comment}")

        print("[1/5] 点击回复按钮（绿色铃铛左侧灰色箭头）...")
        reply_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".reply"))
        )
        reply_button.click()
        print("点击回复按钮成功")

        time.sleep(3)

        print("[2/5] 在编辑器中输入评论内容...")
        driver.execute_script(f"document.querySelector('.ProseMirror').innerHTML = '<p>{comment}</p>';")
        print("输入评论内容成功")

        time.sleep(1)

        print("[3/5] 点击绿色'回复'按钮...")
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-primary.create:not(.topic-footer-button)"))
        )
        submit_button.click()
        print("点击回复按钮成功")

        time.sleep(3)

        print("[4/5] 等待审批弹窗...")
        try:
            confirm_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".modal button.btn-primary"))
            )
            confirm_btn.click()
            print("[5/5] 点击'确定'按钮成功")
        except Exception as e:
            print(f"未找到审批弹窗或点击失败: {e}")

        print("评论提交完成!")
    except Exception as e:
        print(f"发表评论失败: {e}")

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
