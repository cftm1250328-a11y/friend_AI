"""
context_builder.py
記憶ファイルの内容をシステムプロンプトに組み立てる。
"""


def build_system_prompt(memory: dict[str, str], profile: str) -> str:
    """
    memory: MemoryManager.load() の戻り値
    profile: プロファイル名（ログ・デバッグ用）
    """
    parts = [
        f"あなたはユーザーの相棒AIです。プロファイル: [{profile}]",
        "",
    ]

    if memory.get("personality"):
        parts += [
            "## あなたの話し方・口調",
            memory["personality"],
            "",
        ]

    if memory.get("rules"):
        parts += [
            "## 応答ルール",
            memory["rules"],
            "",
        ]

    if memory.get("knowledge"):
        parts += [
            "## ユーザーについて覚えていること",
            memory["knowledge"],
            "",
        ]

    parts += [
        "以上の設定を常に守り、ユーザーの質問や依頼に答えてください。",
    ]

    return "\n".join(parts)


def build_memory_extract_prompt(user_message: str, ai_response: str) -> str:
    """
    会話から「記憶すべき内容」を抽出するプロンプトを生成する。
    Geminiに渡し、JSON形式で返させる。
    """
    return f"""以下の会話から、将来の会話でも参照すべき情報を抽出してください。

ユーザー発言:
{user_message}

AI応答:
{ai_response}

抽出ルール:
- ユーザーの個人情報・好み・環境情報
- 「今後は〜して」「覚えておいて」などの明示的な指示
- 話し方・口調の変更指示

以下のJSONのみを返してください（他のテキスト不要）:
{{
  "should_save": true または false,
  "section": "personality" または "rules" または "knowledge",
  "content": "保存する内容（なければ空文字）"
}}"""
