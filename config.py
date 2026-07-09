import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1").strip()
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip()
        self.discourse_base_url = os.getenv("DISCOURSE_BASE_URL", "https://forum.trae.cn").strip()
        self.target_category_url = os.getenv("TARGET_CATEGORY_URL", "").strip()
        self.max_comments_per_run = int(os.getenv("MAX_COMMENTS_PER_RUN", "5").strip())

        self._validate()
        self.category_slug, self.category_id = self._parse_category_url(self.target_category_url)

    def _validate(self):
        if not self.deepseek_api_key:
            raise ValueError("环境变量 DEEPSEEK_API_KEY 不能为空，请在 .env 文件中配置")
        if not self.target_category_url:
            raise ValueError("环境变量 TARGET_CATEGORY_URL 不能为空，请在 .env 文件中配置")
        if self.max_comments_per_run <= 0:
            raise ValueError("MAX_COMMENTS_PER_RUN 必须大于 0")

    @staticmethod
    def _parse_category_url(url: str):
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        if len(path_parts) < 3 or path_parts[0] != "c":
            raise ValueError(f"无法解析分类 URL: {url}")

        if len(path_parts) >= 2 and path_parts[-2] == "l":
            path_parts = path_parts[:-2]

        category_id = None
        category_slug_parts = []
        for i in range(len(path_parts) - 1, 0, -1):
            if path_parts[i].isdigit():
                category_id = path_parts[i]
                category_slug_parts = path_parts[1:i]
                break

        if category_id is None:
            raise ValueError(f"无法从 URL 中解析出分类 ID: {url}")

        category_slug = "/".join(category_slug_parts)
        return category_slug, category_id


config = Config()
