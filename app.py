"""
app.py
CLI・GUI 両方から使われる中央アプリケーションクラス。
Gemini クライアントと記憶管理を束ねる。
"""

import json
import os
from pathlib import Path

from core.gemini_client import GeminiClient
from core.memory_manager import MemoryManager
from core.context_builder import build_system_prompt


CONFIG_PATH = Path(__file__).parent / "config.json"


class CompanionApp:
    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config = self._load_config(config_path)
        self.config_path = config_path

        # 記憶マネージャー
        memories_dir = Path(__file__).parent / self.config["memories_dir"]
        self.memory = MemoryManager(memories_dir)

        # API キーを環境変数から取得
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "環境変数 GEMINI_API_KEY が設定されていません。\n"
                "export GEMINI_API_KEY='your_api_key' を実行してください。"
            )

        # アクティブプロファイルでクライアント初期化
        profile = self.config["active_profile"]
        system_prompt = self._build_prompt(profile)

        self.client = GeminiClient(
            api_key=api_key,
            model_name=self.config["gemini_model"],
            system_prompt=system_prompt,
            max_history=self.config["max_history"],
        )
        self._active_profile = profile

    # ─────────────────────────────────────────
    # 設定
    # ─────────────────────────────────────────

    def _load_config(self, path: Path) -> dict:
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _save_config(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def _build_prompt(self, profile: str) -> str:
        mem = self.memory.load(profile)
        return build_system_prompt(mem, profile)

    # ─────────────────────────────────────────
    # プロファイル操作
    # ─────────────────────────────────────────

    @property
    def active_profile(self) -> str:
        return self._active_profile

    def switch_profile(self, profile: str) -> None:
        """プロファイルを切り替え、システムプロンプトを更新する。"""
        if not self.memory.profile_exists(profile):
            raise FileNotFoundError(f"プロファイル '{profile}' が見つかりません。")

        self._active_profile = profile
        self.config["active_profile"] = profile
        self._save_config()

        new_prompt = self._build_prompt(profile)
        self.client.update_system_prompt(new_prompt)

    def list_profiles(self) -> list[str]:
        return self.memory.list_profiles()

    def create_profile(self, name: str) -> None:
        self.memory.create_profile(name)

    # ─────────────────────────────────────────
    # チャット
    # ─────────────────────────────────────────

    def send(self, message: str) -> str:
        """
        メッセージを送信し、応答を返す。
        自動記憶保存キーワードが含まれていれば記憶を更新する。
        """
        response = self.client.chat(message)

        # 自動記憶保存チェック
        if self._should_extract(message):
            self._auto_save(message, response)

        return response

    def _should_extract(self, message: str) -> bool:
        keywords = self.config.get("auto_save_keywords", [])
        return any(kw in message for kw in keywords)

    def _auto_save(self, user_msg: str, ai_response: str) -> None:
        result = self.client.extract_memory(user_msg, ai_response)
        if result and result.get("should_save") and result.get("content"):
            section = result.get("section", "knowledge")
            content = result["content"]
            self.memory.append_knowledge(self._active_profile, content) \
                if section == "knowledge" \
                else self.memory.update_section(self._active_profile, section, content)

            # システムプロンプトを再構築してクライアントに反映
            self.client.update_system_prompt(self._build_prompt(self._active_profile))

    def clear_history(self) -> None:
        self.client.clear_history()

    # ─────────────────────────────────────────
    # ワンショット（CLI 用）
    # ─────────────────────────────────────────

    def ask_once(self, message: str, profile: str | None = None) -> str:
        """
        履歴なしの1回限りの問い合わせ。
        エディタ連携 CLI から使用する。
        """
        p = profile or self._active_profile
        system_prompt = self._build_prompt(p)
        return self.client.chat_one_shot(message, system_prompt)
