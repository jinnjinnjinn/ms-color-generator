"""
MS Color Generator - Hugging Face Spaces版
"""

import os
import sys

# main.pyをインポートして実行
if __name__ == "__main__":
    # 現在のディレクトリをPythonパスに追加
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # main.pyから必要なモジュールをインポート
    try:
        from main import main
        
        # メイン関数を実行（ブラウザ自動起動なし）
        print("🚀 MS Color Generator - Hugging Face Spaces で起動中...")
        
        # 遅延インポートでUIを作成
        from ui import colorizer, create_ui
        
        # UI作成
        demo = create_ui()
        
        # Hugging Face Spaces用に調整
        demo.launch(
            server_name="0.0.0.0",  # 外部アクセス許可
            server_port=7860,       # デフォルトポート
            share=False,            # Sharingは不要（Spaces環境）
            inbrowser=False,        # ブラウザ自動起動なし
            show_error=True         # エラー表示
        )
        
    except Exception as e:
        print(f"❌ アプリケーション起動エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)