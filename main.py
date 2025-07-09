"""
MS Color Generator - メインエントリポイント
"""

import os
from config import VERSION, LAYER_DIR, SAVE_DIR


def check_restart_flag() -> bool:
    """再起動フラグをチェック
    
    Returns:
        再起動モードかどうかの真偽値
    """
    is_restart = os.environ.get('MS_COLOR_RESTART', 'False') == 'True'
    
    if is_restart:
        print("🔄 [RESTART] 再起動モードで開始（自動リロード有効）")
        # 再起動フラグをクリア
        if 'MS_COLOR_RESTART' in os.environ:
            del os.environ['MS_COLOR_RESTART']
    else:
        print("🚀 [STARTUP] 通常起動モード（ブラウザを自動起動します）")
    
    return is_restart


def display_startup_info(colorizer):
    """起動時の情報を表示
    
    Args:
        colorizer: LayerColorizerインスタンス
    """
    print(f"MS Color Generator {VERSION}")
    print(f"レイヤー読み込みフォルダ: {LAYER_DIR}")
    print(f"{colorizer.num_layers}個のレイヤーファイルを読み込みました")
    print(f"保存フォルダ: {SAVE_DIR}")
    print(f"レイヤー設定: {colorizer.layers}")
    print(f"グループ色: {colorizer.group_colors}")
    print("-" * 50)
    print("NEW: 画像をクリックしてレイヤーを直接選択・編集！")
    print("NEW: プリセットでパラメータ設定 → ランダム生成で色生成！")
    print("NEW: 彩度・明度が100分率表記で直感的！")
    print("NEW: 色相等間隔生成モードと最小色相距離設定追加！")
    print("NEW: カラーピッカーにカラーコード+HSV値表示！")
    print("NEW: 4枚横並びギャラリー表示＋メイン選択表示！")


def main():
    """メイン実行関数"""
    try:
        # 再起動フラグをチェック
        is_restart = check_restart_flag()
        
        # 遅延インポート（起動時間短縮のため）
        from ui import colorizer, create_ui
        
        # 起動情報表示
        display_startup_info(colorizer)
        
        # UI作成・起動
        demo = create_ui()
        
        # 初回起動時のみブラウザを自動起動
        demo.launch(inbrowser=not is_restart)
        
    except ImportError as e:
        print(f"❌ [IMPORT ERROR] モジュールのインポートに失敗: {e}")
        print("必要なライブラリがインストールされていない可能性があります。")
        print("pip install -r requirements.txt を実行してください。")
    except Exception as e:
        print(f"❌ [FATAL ERROR] アプリケーションの起動に失敗: {e}")
        print("設定ファイルやレイヤーファイルを確認してください。")


if __name__ == "__main__":
    main()