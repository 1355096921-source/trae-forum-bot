import time
import random
import html
from config import config
from discourse_client import DiscourseClient, extract_topic_body
from deepseek_client import DeepSeekClient
from comment_generator import CommentGenerator
from state_manager import StateManager
from skip_list_manager import SkipListManager


def main():
    print("=" * 50)
    print("论坛自动化评论任务启动")
    print("=" * 50)

    discourse = DiscourseClient(config.discourse_cookies)
    deepseek = DeepSeekClient(config.deepseek_api_key, config.deepseek_base_url, config.deepseek_model)
    generator = CommentGenerator(deepseek)
    state = StateManager()
    skip_list = SkipListManager()

    print(f"目标分类: {config.target_category_url}")
    print(f"最大评论数: {config.max_comments_per_run}")
    print(f"已评价记录: {len(state._commented_ids)} 条")
    print(f"黑名单记录: {len(skip_list.skip_ids)} 条")
    print("-" * 50)

    topics = discourse.get_latest_topics(config.category_slug, config.category_id)
    if not topics:
        print("未获取到任何主题，任务结束")
        return

    success_count = 0
    skip_commented_count = 0
    skip_blacklist_count = 0
    processed = 0

    for topic in topics:
        if success_count >= config.max_comments_per_run:
            print(f"\n已达本次最大评论数上限 ({config.max_comments_per_run})，任务终止")
            break

        topic_id = topic.get("id")
        title = topic.get("title", "")
        if not topic_id:
            continue

        processed += 1

        if skip_list.is_skipped(topic_id):
            print(f"[{processed}] 主题 {topic_id} - 黑名单跳过")
            skip_blacklist_count += 1
            continue

        if state.has_commented(topic_id):
            print(f"[{processed}] 主题 {topic_id} - 已评价跳过")
            skip_commented_count += 1
            continue

        try:
            detail = discourse.get_topic_detail(topic_id)
        except Exception as e:
            print(f"[{processed}] 主题 {topic_id} - 获取详情失败: {e}")
            continue

        body = extract_topic_body(detail)
        body_text = html.unescape(body)
        body_text = body_text.replace("<br>", "\n").replace("<br/>", "\n")
        import re
        body_text = re.sub(r"<[^>]+>", "", body_text)

        print(f"[{processed}] 主题 {topic_id} - 正在生成评论...")
        try:
            comment = generator.generate(title, body_text)
        except Exception as e:
            print(f"[{processed}] 主题 {topic_id} - 生成评论失败: {e}")
            continue

        print(f"[{processed}] 主题 {topic_id} - 生成评论: {comment[:50]}...")

        try:
            discourse.create_reply(topic_id, comment)
            state.record_comment(topic_id)
            success_count += 1
            print(f"[{processed}] 主题 {topic_id} - 评论发表成功")
        except Exception as e:
            print(f"[{processed}] 主题 {topic_id} - 评论发表失败: {e}")
            continue

        delay = random.uniform(3, 5)
        print(f"等待 {delay:.1f} 秒...")
        time.sleep(delay)

    print("-" * 50)
    print("执行摘要:")
    print(f"  共处理主题: {processed}")
    print(f"  评论成功: {success_count}")
    print(f"  已评价跳过: {skip_commented_count}")
    print(f"  黑名单跳过: {skip_blacklist_count}")
    print("=" * 50)


if __name__ == "__main__":
    main()
