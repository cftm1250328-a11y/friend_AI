"""
memory_manager.py
記憶ファイル（.txt）の読み書き・プロファイル管理を担う。
"""

import os
import re
from datetime import datetime
from pathlib import Path


SECTIONS = ["personality", "rules", "knowledge"]


class MemoryManager:
    def __init__(self, memories_dir: str = "memories"):
        self.memories_dir = Path(memories_dir)
        self.memories_dir.mkdir(exist_ok=True)

    # ─────────────────────────────────────────
    # プロファイル一覧
    # ─────────────────────────────────────────

    def list_profiles(self) -> list[str]:
        """利用可能なプロファイル名を返す（拡張子なし）。"""
        return [p.stem for p in self.memories_dir.glob("*.txt")]

    def profile_path(self, profile: str) -> Path:
        return self.memories_dir / f"{profile}.txt"

    def profile_exists(self, profile: str) -> bool:
        return self.profile_path(profile).exists()

    def create_profile(self, profile: str) -> None:
        """空のプロファイルファイルを新規作成する。"""
        path = self.profile_path(profile)
        if path.exists():
            raise FileExistsError(f"プロファイル '{profile}' は既に存在します。")
        template = "\n".join(
            [f"[{s}]\n# {s}の設定\n" for s in SECTIONS]
        )
        path.write_text(template, encoding="utf-8")

    def delete_profile(self, profile: str) -> None:
        path = self.profile_path(profile)
        if not path.exists():
            raise FileNotFoundError(f"プロファイル '{profile}' が見つかりません。")
        path.unlink()

    # ─────────────────────────────────────────
    # 読み込み
    # ─────────────────────────────────────────

    def load(self, profile: str) -> dict[str, str]:
        """
        プロファイルを読み込み、セクションごとの dict を返す。
        例: {"personality": "...", "rules": "...", "knowledge": "..."}
        """
        path = self.profile_path(profile)
        if not path.exists():
            return {s: "" for s in SECTIONS}

        raw = path.read_text(encoding="utf-8")
        return self._parse(raw)

    def _parse(self, raw: str) -> dict[str, str]:
        result = {s: "" for s in SECTIONS}
        current = None
        lines_buf: list[str] = []

        for line in raw.splitlines():
            m = re.match(r"^\[(\w+)\]$", line.strip())
            if m:
                if current is not None:
                    result[current] = self._clean_lines(lines_buf)
                current = m.group(1)
                lines_buf = []
            elif current is not None:
                lines_buf.append(line)

        if current is not None:
            result[current] = self._clean_lines(lines_buf)

        return result

    def _clean_lines(self, lines: list[str]) -> str:
        """コメント行（#）を除いて結合する。"""
        cleaned = [l for l in lines if not l.strip().startswith("#")]
        return "\n".join(cleaned).strip()

    # ─────────────────────────────────────────
    # 書き込み
    # ─────────────────────────────────────────

    def append_knowledge(self, profile: str, content: str) -> None:
        """
        [knowledge] セクションに内容を追記する。
        「覚えておいて」などで自動保存される際に使用。
        """
        path = self.profile_path(profile)
        if not path.exists():
            self.create_profile(profile)

        raw = path.read_text(encoding="utf-8")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"# [{timestamp}] 自動保存\n{content}"

        if "[knowledge]" in raw:
            # [knowledge] セクションの末尾に追加
            raw = raw.rstrip() + f"\n{entry}\n"
        else:
            raw += f"\n[knowledge]\n{entry}\n"

        path.write_text(raw, encoding="utf-8")

    def update_section(self, profile: str, section: str, content: str) -> None:
        """指定セクションの内容を丸ごと書き換える。"""
        if section not in SECTIONS:
            raise ValueError(f"不明なセクション: {section}")

        path = self.profile_path(profile)
        if not path.exists():
            self.create_profile(profile)

        raw = path.read_text(encoding="utf-8")
        pattern = rf"(\[{section}\])(.*?)(?=\[|\Z)"
        replacement = f"[{section}]\n{content}\n\n"

        if re.search(pattern, raw, flags=re.DOTALL):
            raw = re.sub(pattern, replacement, raw, flags=re.DOTALL)
        else:
            raw += f"\n[{section}]\n{content}\n"

        path.write_text(raw, encoding="utf-8")

    def read_raw(self, profile: str) -> str:
        """生テキストをそのまま返す（エディタ表示用）。"""
        path = self.profile_path(profile)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def write_raw(self, profile: str, raw: str) -> None:
        """生テキストをそのまま書き込む（エディタ保存用）。"""
        self.profile_path(profile).write_text(raw, encoding="utf-8")
