#!/usr/bin/env python3
"""
companion_cli.py
エディタ連携・ターミナルから使う CLI インターフェース。

使い方:
  # 対話モード（チャット）
  python companion_cli.py

  # ワンショット質問
  python companion_cli.py ask "Pythonのリスト内包表記を説明して"

  # コンテキスト（コード等）を渡す
  python companion_cli.py ask "このコードの問題点は？" --context "$(cat main.py)"

  # プロファイル指定
  python companion_cli.py ask "命名を改善して" --profile coding

  # プロファイル一覧
  python companion_cli.py profiles

  # プロファイル切替（設定を保存）
  python companion_cli.py switch coding

  # 記憶ファイルを表示
  python companion_cli.py memory show
  python companion_cli.py memory show --profile coding
"""

import argparse
import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import CompanionApp


def cmd_ask(app: CompanionApp, args: argparse.Namespace) -> None:
    """ワンショット質問（履歴なし）。エディタ連携向け。"""
    message = args.message
    if args.context:
        message = f"{message}\n\n```\n{args.context}\n```"

    response = app.ask_once(message, profile=args.profile)
    print(response)


def cmd_chat(app: CompanionApp, _args: argparse.Namespace) -> None:
    """対話モード（履歴あり）。"""
    profile = app.active_profile
    print(f"🤖 相棒AI起動 | プロファイル: [{profile}]")
    print("  終了: exit / quit / Ctrl+C")
    print("  履歴クリア: /clear")
    print("  プロファイル切替: /switch <name>")
    print("  プロファイル一覧: /profiles")
    print("-" * 40)

    while True:
        try:
            user_input = input("あなた: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 終了します。")
            break

        if not user_input:
            continue

        if user_input in ("exit", "quit"):
            print("👋 終了します。")
            break

        # スラッシュコマンド
        if user_input == "/clear":
            app.clear_history()
            print("✅ 会話履歴をクリアしました。")
            continue

        if user_input == "/profiles":
            profiles = app.list_profiles()
            print(f"📁 プロファイル一覧: {', '.join(profiles)}")
            print(f"   現在: [{app.active_profile}]")
            continue

        if user_input.startswith("/switch "):
            name = user_input.split(" ", 1)[1].strip()
            try:
                app.switch_profile(name)
                print(f"✅ プロファイルを [{name}] に切り替えました。")
            except FileNotFoundError as e:
                print(f"❌ {e}")
            continue

        # 通常のメッセージ送信
        try:
            response = app.send(user_input)
            print(f"\nAI: {response}\n")
        except Exception as e:
            print(f"❌ エラー: {e}")


def cmd_profiles(app: CompanionApp, _args: argparse.Namespace) -> None:
    profiles = app.list_profiles()
    current = app.active_profile
    for p in profiles:
        marker = "▶" if p == current else " "
        print(f"  {marker} {p}")


def cmd_switch(app: CompanionApp, args: argparse.Namespace) -> None:
    try:
        app.switch_profile(args.profile)
        print(f"✅ プロファイルを [{args.profile}] に切り替えました。")
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)


def cmd_memory(app: CompanionApp, args: argparse.Namespace) -> None:
    profile = args.profile or app.active_profile
    if args.action == "show":
        raw = app.memory.read_raw(profile)
        print(f"── [{profile}] ──────────────────")
        print(raw)
    else:
        print(f"不明なアクション: {args.action}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="companion",
        description="相棒AI CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # ask
    p_ask = subparsers.add_parser("ask", help="ワンショット質問（エディタ連携向け）")
    p_ask.add_argument("message", help="質問・指示テキスト")
    p_ask.add_argument("--context", "-c", default="", help="コードなどのコンテキスト")
    p_ask.add_argument("--profile", "-p", default=None, help="使用するプロファイル")

    # profiles
    subparsers.add_parser("profiles", help="プロファイル一覧を表示")

    # switch
    p_switch = subparsers.add_parser("switch", help="プロファイルを切り替える")
    p_switch.add_argument("profile", help="切り替え先のプロファイル名")

    # memory
    p_mem = subparsers.add_parser("memory", help="記憶ファイルの操作")
    p_mem.add_argument("action", choices=["show"], help="操作: show")
    p_mem.add_argument("--profile", "-p", default=None, help="対象プロファイル")

    args = parser.parse_args()

    try:
        app = CompanionApp()
    except EnvironmentError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    if args.command == "ask":
        cmd_ask(app, args)
    elif args.command == "profiles":
        cmd_profiles(app, args)
    elif args.command == "switch":
        cmd_switch(app, args)
    elif args.command == "memory":
        cmd_memory(app, args)
    else:
        # コマンド未指定 → 対話モード
        cmd_chat(app, args)


if __name__ == "__main__":
    main()
