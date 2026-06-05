import json

import httpx

from app.schemas import LLMSettings


class LLMClient:
    """OpenAI 兼容 Chat Completions 客户端，可切换厂商或本地模型。"""

    def __init__(self, cfg: LLMSettings):
        self.cfg = cfg

    @property
    def configured(self) -> bool:
        return bool(self.cfg.apiKey and self.cfg.baseUrl and self.cfg.model)

    async def chat(self, system: str, user: str, json_mode: bool = False) -> str:
        if not self.configured:
            raise RuntimeError("LLM 未配置，请在「设置」中填写 base_url / api_key / model")

        payload: dict = {
            "model": self.cfg.model,
            "temperature": self.cfg.temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        url = self.cfg.baseUrl.rstrip("/") + "/chat/completions"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {self.cfg.apiKey}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def chat_json(self, system: str, user: str) -> dict:
        raw = await self.chat(system, user, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start, end = raw.find("{"), raw.rfind("}")
            if start >= 0 and end > start:
                return json.loads(raw[start : end + 1])
            raise

    async def test(self) -> tuple[bool, str]:
        if not self.configured:
            return False, "LLM 未配置"
        try:
            await self.chat("You are a health check.", "ping", json_mode=False)
            return True, "连接成功"
        except Exception as exc:  # noqa: BLE001
            return False, f"连接失败：{exc}"
