"""
gemini_client.py
Gemini API との通信・会話履歴管理を担う。
"""

import json
import os
import re

import google.generativeai as genai


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-1.5-flash",
        system_prompt: str = "",
        max_history: int = 20,
    ):
        genai.configure(api_key=api_key)

        self.model_name = model_name
        self.max_history = max_history
        self._history: list[dict] = []

        # システムプロンプトを設定してモデルを初期化
        self._model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
        )
        self._chat = self._model.start_chat(history=[])

    def update_system_prompt(self, system_prompt: str) -> None:
        """
        プロファイル切替時にシステムプロンプトを更新し、
        チャットセッションを再作成する。
        """
        self._model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
        )
        # 履歴を引き継いでセッション再構築
        self._chat = self._model.start_chat(history=self._history)

    def chat(self, message: str) -> str:
        """
        メッセージを送信し、応答テキストを返す。
        内部で履歴を自動管理する。
        """
        response = self._chat.send_message(message)
        text = response.text

        # 履歴の長さを制限
        if len(self._history) >= self.max_history * 2:
            # 古い履歴を先頭から削除（2件ずつ = user+model のペア）
            self._history = self._history[2:]

        return text

    def chat_one_shot(self, message: str, system_prompt: str = "") -> str:
        """
        履歴を持たない1回限りの送信（CLI のワンショット呼び出し用）。
        """
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
        )
        response = model.generate_content(message)
        return response.text

    def extract_memory(self, user_message: str, ai_response: str) -> dict | None:
        """
        会話から記憶すべき内容を抽出する。
        戻り値: {"should_save": bool, "section": str, "content": str}
        失敗時は None を返す。
        """
        from .context_builder import build_memory_extract_prompt

        prompt = build_memory_extract_prompt(user_message, ai_response)
        try:
            model = genai.GenerativeModel(model_name=self.model_name)
            response = model.generate_content(prompt)
            raw = response.text.strip()

            # JSONブロックを取り出す
            raw = re.sub(r"```json|```", "", raw).strip()
            return json.loads(raw)
        except Exception:
            return None

    def clear_history(self) -> None:
        """会話履歴をリセットする。"""
        self._history = []
        self._chat = self._model.start_chat(history=[])

    @property
    def history(self) -> list[dict]:
        return list(self._history)
