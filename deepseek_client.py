import requests
from typing import List, Dict, Any


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 300) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise PermissionError("DeepSeek API Key 无效或已过期 (401)，请检查 DEEPSEEK_API_KEY") from e
            if response.status_code == 429:
                raise RuntimeError("DeepSeek API 请求过于频繁 (429)，请稍后再试") from e
            raise RuntimeError(f"DeepSeek API 请求失败: {response.status_code} {response.text}") from e
        except requests.exceptions.Timeout:
            raise RuntimeError("DeepSeek API 请求超时，请检查网络连接")

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("DeepSeek API 返回结果为空，无法获取评论内容")
        content = choices[0].get("message", {}).get("content", "")
        return content.strip()
