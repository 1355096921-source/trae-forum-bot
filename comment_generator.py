import re
import random
from deepseek_client import DeepSeekClient

SYSTEM_PROMPT = (
    "你是一位热心、专业的社区用户，擅长对技术/创意类帖子给出简短、真诚、有建设性的中文评论。"
)

USER_PROMPT_TEMPLATE = (
    "请根据以下帖子内容生成一条中文评论，要求：\n"
    "1. 必须以'已投票'开头\n"
    "2. 总字数在 15-50 字之间\n"
    "3. 内容简短、真诚、有互动感\n\n"
    "帖子标题：{title}\n"
    "帖子正文：{body}\n\n"
    "请直接输出评论内容。"
)

AI_WORDS = [
    "作为 AI",
    "作为人工智能",
    "我是 AI",
    "我是人工智能",
    "AI 认为",
    "本 AI",
]


class CommentGenerator:
    def __init__(self, client: DeepSeekClient):
        self.client = client

    def generate(self, title: str, body: str) -> str:
        truncated_body = body[:2000] if len(body) > 2000 else body
        user_prompt = USER_PROMPT_TEMPLATE.format(title=title, body=truncated_body)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        raw_comment = self.client.chat_completion(messages, temperature=0.7, max_tokens=100)
        cleaned = self._clean(raw_comment)
        cleaned = self._truncate_smart(cleaned, 50)
        if len(cleaned) < 15:
            suffixes = [
                "，创意很棒，期待后续更新！",
                "，很有意思，支持一下！",
                "，做得不错，继续加油！",
                "，期待看到更多细节！",
                "，这个想法很有潜力！",
            ]
            cleaned += random.choice(suffixes)
            cleaned = self._truncate_smart(cleaned, 50)
        if not cleaned.startswith("已投票"):
            cleaned = "已投票" + cleaned[3:] if len(cleaned) > 3 else "已投票，很棒！"
        if "相互支持" not in cleaned:
            cleaned += "，相互支持"
            cleaned = self._truncate_smart(cleaned, 50)
        return cleaned

    @staticmethod
    def _truncate_smart(text: str, max_len: int) -> str:
        """智能截断：优先在标点符号处截断，避免在句子中间切断"""
        if len(text) <= max_len:
            return text
        truncated = text[:max_len]
        # 从截断位置往前找标点符号
        for i in range(len(truncated) - 1, max(len(truncated) - 10, 0), -1):
            if truncated[i] in "。，！？；、":
                return truncated[:i + 1]
        # 找不到标点就截断后补句号
        if not truncated.endswith("。"):
            truncated += "。"
        return truncated

    @staticmethod
    def _clean(text: str) -> str:
        text = text.strip()
        text = re.sub(r'^[\s"\']+|[\s"\']+$', '', text)
        for word in AI_WORDS:
            if text.startswith(word):
                text = text[len(word):].strip()
                text = re.sub(r'^[，,、\.\!\?\s]+', '', text)
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
