import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import config


def main():
    TEST_TOPIC_ID = 22549
    topic_url = f"https://forum.trae.cn/t/topic/{TEST_TOPIC_ID}"

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--auto-open-devtools-for-tabs")

    print("[1] 启动浏览器...")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(topic_url)

    print("[2] 设置 Cookie...")
    driver.delete_all_cookies()
    for key, value in config.discourse_cookies.items():
        driver.add_cookie({"name": key, "value": value, "domain": ".trae.cn"})

    print("[3] 刷新页面...")
    driver.get(topic_url)
    time.sleep(5)

    print("[4] 查找投票按钮信息...")
    try:
        vote_buttons = driver.find_elements(By.CSS_SELECTOR, "button, div[role='button']")
        for btn in vote_buttons:
            text = btn.text.strip()[:30]
            if text and ("投票" in text or "vote" in btn.get_attribute("class").lower()):
                print(f"\n找到按钮:")
                print(f"  文本: {text}")
                print(f"  class: {btn.get_attribute('class')}")
                print(f"  data-action: {btn.get_attribute('data-action')}")
                print(f"  onclick: {btn.get_attribute('onclick')}")
                print(f"  innerHTML: {btn.get_attribute('innerHTML')[:200]}")
    except Exception as e:
        print(f"查找失败: {e}")

    print("\n[5] 执行 JavaScript 查找投票相关代码...")
    try:
        js_result = driver.execute_script("""
            var results = [];
            document.querySelectorAll('button, div').forEach(function(el) {
                var cls = el.className || '';
                var text = el.textContent || '';
                if (cls.includes('vote') || text.includes('投票')) {
                    results.push({
                        tag: el.tagName,
                        class: cls,
                        text: text.substring(0, 50),
                        dataAction: el.getAttribute('data-action'),
                        dataController: el.getAttribute('data-controller'),
                        onclick: el.getAttribute('onclick')
                    });
                }
            });
            return JSON.stringify(results, null, 2);
        """)
        print(js_result)
    except Exception as e:
        print(f"JS执行失败: {e}")

    print("\n[6] 尝试获取页面中的投票URL...")
    try:
        js_result = driver.execute_script("""
            var urls = [];
            var scripts = document.querySelectorAll('script');
            scripts.forEach(function(script) {
                var src = script.src || '';
                if (src.includes('vote')) {
                    urls.push(src);
                }
            });
            return urls;
        """)
        print(f"投票相关脚本: {js_result}")
    except Exception as e:
        print(f"获取脚本失败: {e}")

    print("\n请手动点击投票按钮，观察开发者工具的Network标签，然后关闭浏览器")
    input("按回车退出...")
    driver.quit()


if __name__ == "__main__":
    main()
