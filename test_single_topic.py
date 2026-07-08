import html
import re
from config import config
from discourse_client import DiscourseClient, extract_topic_body
from deepseek_client import DeepSeekClient
from comment_generator import CommentGenerator


def main():
    TEST_TOPIC_ID = 22549

    print("=" * 50)
    print(f"测试模式 - 只对帖子 {TEST_TOPIC_ID} 执行操作")
    print("=" * 50)

    discourse = DiscourseClient(config.discourse_cookies)
    deepseek = DeepSeekClient(config.deepseek_api_key, config.deepseek_base_url, config.deepseek_model)
    generator = CommentGenerator(deepseek)

    print(f"\n[1/4] 获取帖子 {TEST_TOPIC_ID} 详情...")
    try:
        detail = discourse.get_topic_detail(TEST_TOPIC_ID)
    except Exception as e:
        print(f"获取详情失败: {e}")
        return

    title = detail.get("title", "")
    print(f"帖子标题: {title}")

    can_vote = detail.get("can_vote", False)
    already_voted = detail.get("user_voted", False)
    vote_count = detail.get("vote_count", 0)
    print(f"可投票: {'是' if can_vote else '否'}")
    print(f"已投票: {'是' if already_voted else '否'}")
    print(f"当前票数: {vote_count}")

    print(f"\n[2/4] 执行投票...")
    if can_vote and not already_voted:
        try:
            result = discourse.vote_topic(TEST_TOPIC_ID)
            print(f"投票成功")
        except Exception as e:
            print(f"投票失败: {e}")
            print("继续执行评论...")
    else:
        print("跳过投票（无投票功能或已投票）")

    print(f"\n[3/4] 生成评论...")
    body = extract_topic_body(detail)
    body_text = html.unescape(body)
    body_text = body_text.replace("<br>", "\n").replace("<br/>", "\n")
    body_text = re.sub(r"<[^>]+>", "", body_text)

    try:
        comment = generator.generate(title, body_text)
        print(f"生成评论: {comment}")
        print(f"评论字数: {len(comment)}")
    except Exception as e:
        print(f"生成评论失败: {e}")
        return

    print(f"\n[4/4] 发表评论...")
    try:
        result = discourse.create_reply(TEST_TOPIC_ID, comment)
        print(f"评论发表成功!")
        print(f"评论链接: https://forum.trae.cn/t/topic/{TEST_TOPIC_ID}")
    except Exception as e:
        print(f"评论发表失败: {e}")

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
