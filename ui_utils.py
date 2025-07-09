"""
MS Color Generator - UIユーティリティ関数（Hugging Face Spaces対応版）
"""

import os
import sys
import shutil
import threading
import time
import tempfile
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

import gradio as gr

from config import (
    DEFAULT_GROUP_COLOR, FILE_PREFIX, BACKUP_SETTINGS, 
    SYSTEM_SETTINGS, RESTART_SETTINGS, COLOR_SETTINGS, IS_HUGGING_FACE_SPACES
)
from color_utils import hex_to_hsv

# 循環インポート回避のための型チェック
if TYPE_CHECKING:
    from layer_manager import LayerColorizer


def format_color_display(color: str) -> str:
    """色の表示を整数形式で整える
    
    Args:
        color: 色の文字列（16進数、RGB形式など）
        
    Returns:
        正規化された16進数カラーコード
    """
    if not color or not isinstance(color, str):
        return DEFAULT_GROUP_COLOR
        
    # 16進数カラーコードの場合はそのまま返す
    if color.startswith("#") and len(color) == 7:
        try:
            # 有効な16進数かチェック
            int(color[1:], 16)
            return color
        except ValueError:
            return DEFAULT_GROUP_COLOR
    
    # RGBA形式などの場合は16進数に変換
    try:
        if color.startswith("rgb"):
            # rgb(r, g, b) 形式をパース
            inside = color[color.find("(")+1:-1]
            parts = [int(float(v.strip())) for v in inside.split(",")[:3]]
            if len(parts) >= 3:
                r, g, b = parts[:3]
                # RGB値の範囲チェック
                if all(0 <= val <= 255 for val in [r, g, b]):
                    return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, IndexError, AttributeError):
        pass
    
    return DEFAULT_GROUP_COLOR


def update_pickers_only(colorizer: 'LayerColorizer') -> List[gr.update]:
    """カラーピッカーのみを更新
    
    Args:
        colorizer: LayerColorizerインスタンス
        
    Returns:
        カラーピッカー更新データのリスト
    """
    print(f"🔍 [DEBUG] update_pickers_only開始")
    
    try:
        sorted_group_data = colorizer.get_sorted_group_data(colorizer.layers)
        picker_updates = []
        
        print(f"🔍 [DEBUG] ソート済みグループデータ: {len(sorted_group_data)}個")
        
        for group_name, layer_indices in sorted_group_data:
            try:
                layer_numbers = [str(idx + 1) for idx in sorted(layer_indices)]
                
                # 色とHSV値を計算
                color = colorizer.group_colors.get(group_name, DEFAULT_GROUP_COLOR)
                display_color = format_color_display(color)
                h, s, v = hex_to_hsv(display_color)
                
                # レイヤー番号を整理して表示
                layer_list = ", ".join(layer_numbers)
                
                # configから精度設定を取得してフォーマット
                hue_precision = COLOR_SETTINGS["hue_display_precision"]
                sat_precision = COLOR_SETTINGS["saturation_display_precision"]
                bright_precision = COLOR_SETTINGS["brightness_display_precision"]
                
                label = f"{display_color} (H:{h:.{hue_precision}f}° S:{s:.{sat_precision}f}% V:{v:.{bright_precision}f}%)\n{group_name} ({len(layer_numbers)}個): {layer_list}"
                
                picker_update = gr.update(visible=True, label=label, value=display_color)
                picker_updates.append(picker_update)
                print(f"🔍 [DEBUG] ピッカー更新: {group_name} → {display_color}")
                
            except Exception as e:
                print(f"❌ [ERROR] ピッカー更新エラー {group_name}: {e}")
                # エラー時はデフォルト表示
                picker_updates.append(gr.update(visible=True, label=f"{group_name} (エラー)", value=DEFAULT_GROUP_COLOR))
        
        # 残りを非表示に
        while len(picker_updates) < colorizer.num_layers:
            picker_updates.append(gr.update(visible=False))
        
        print(f"🔍 [DEBUG] update_pickers_only完了: {len(picker_updates)}個")
        return picker_updates
        
    except Exception as e:
        print(f"❌ [ERROR] update_pickers_only 致命的エラー: {e}")
        # 全て非表示で返す
        return [gr.update(visible=False) for _ in range(colorizer.num_layers)]


def create_initial_pickers(colorizer: 'LayerColorizer') -> List[gr.ColorPicker]:
    """初期カラーピッカーを作成
    
    Args:
        colorizer: LayerColorizerインスタンス
        
    Returns:
        カラーピッカーコンポーネントのリスト
    """
    pickers = []
    
    try:
        sorted_group_data = colorizer.get_sorted_group_data(colorizer.layers)
        
        for i, (group_name, layer_indices) in enumerate(sorted_group_data):
            try:
                layer_numbers = [str(idx + 1) for idx in sorted(layer_indices)]
                
                # 色とHSV値を計算
                default_color = colorizer.group_colors.get(group_name, DEFAULT_GROUP_COLOR)
                display_color = format_color_display(default_color)
                h, s, v = hex_to_hsv(display_color)
                
                # レイヤー番号を整理して表示
                layer_list = ", ".join(layer_numbers)
                
                # configから精度設定を取得してフォーマット
                hue_precision = COLOR_SETTINGS["hue_display_precision"]
                sat_precision = COLOR_SETTINGS["saturation_display_precision"]
                bright_precision = COLOR_SETTINGS["brightness_display_precision"]
                
                label = f"{display_color} (H:{h:.{hue_precision}f}° S:{s:.{sat_precision}f}% V:{v:.{bright_precision}f}%)\n{group_name} ({len(layer_numbers)}レイヤー): {layer_list}"
                
                picker = gr.ColorPicker(
                    label=label, 
                    value=display_color, 
                    interactive=True
                )
                pickers.append(picker)
                
            except Exception as e:
                print(f"❌ [ERROR] ピッカー作成エラー {group_name}: {e}")
                # エラー時はデフォルトピッカー
                picker = gr.ColorPicker(
                    label=f"{group_name} (エラー)", 
                    value=DEFAULT_GROUP_COLOR, 
                    interactive=True
                )
                pickers.append(picker)
        
        # 残りのレイヤー用に非表示のピッカーを追加
        while len(pickers) < colorizer.num_layers:
            picker = gr.ColorPicker(
                label="", 
                value=DEFAULT_GROUP_COLOR, 
                interactive=True,
                visible=False
            )
            pickers.append(picker)
            
    except Exception as e:
        print(f"❌ [ERROR] create_initial_pickers 致命的エラー: {e}")
        # 最低限のピッカーを作成
        for i in range(max(4, colorizer.num_layers)):
            picker = gr.ColorPicker(
                label=f"グループ{i+1} (エラー)", 
                value=DEFAULT_GROUP_COLOR, 
                interactive=True,
                visible=(i < 4)
            )
            pickers.append(picker)
    
    return pickers


def restart_server() -> str:
    """自動リロード付き再起動機能（AUTOMATIC1111方式）
    
    Returns:
        再起動状況メッセージ
    """
    def delayed_restart():
        """遅延再起動処理"""
        try:
            # configから待機時間を取得
            wait_time = SYSTEM_SETTINGS["flag_reset_delay"]
            time.sleep(wait_time)
            print("🔄 [RESTART] サーバーを再起動します（自動リロード有効）...")
            
            # configから再起動フラグ設定を取得
            restart_env = RESTART_SETTINGS["restart_flag_env"]
            restart_value = RESTART_SETTINGS["restart_flag_value"]
            os.environ[restart_env] = restart_value
            
            # 現在のプロセスを終了して新しいプロセスを開始
            os.execv(sys.executable, ['python'] + sys.argv)
            
        except Exception as e:
            print(f"❌ [RESTART ERROR] 再起動に失敗: {e}")
            # 緊急時は通常の終了
            sys.exit(1)
    
    try:
        # 別スレッドで遅延再起動を実行
        restart_thread = threading.Thread(target=delayed_restart)
        restart_thread.daemon = SYSTEM_SETTINGS["thread_daemon_mode"]
        restart_thread.start()
        
        return "🔄 再起動中... 自動でリロードします"
        
    except Exception as e:
        print(f"❌ [RESTART ERROR] スレッド作成に失敗: {e}")
        return "❌ 再起動に失敗しました"


def do_save(current_main_image) -> Optional[str]:
    """画像保存処理（Hugging Face Spaces対応）
    
    Args:
        current_main_image: 保存する画像（PIL Image）
        
    Returns:
        保存されたファイルパス（失敗時はNone）
    """
    try:
        if current_main_image is None:
            print("❌ [SAVE] 保存する画像がありません")
            return None
        
        # タイムスタンプ付きファイル名生成
        timestamp_format = SYSTEM_SETTINGS["timestamp_format"]
        ts = datetime.now().strftime(timestamp_format)
        filename = f"{FILE_PREFIX}_{ts}.png"
        
        if IS_HUGGING_FACE_SPACES:
            # Hugging Face Spaces: 一時ディレクトリを使用
            temp_dir = tempfile.gettempdir()
            fname = os.path.join(temp_dir, filename)
            print(f"💫 [SAVE] Hugging Face Spaces環境: 一時保存 {fname}")
        else:
            # ローカル環境: 通常の保存
            from config import SAVE_DIR
            os.makedirs(SAVE_DIR, exist_ok=True)
            fname = os.path.join(SAVE_DIR, filename)
            print(f"💾 [SAVE] ローカル環境: 通常保存 {fname}")
        
        current_main_image.save(fname)
        print(f"✅ [SAVE] 画像保存完了: {fname}")
        return fname
        
    except Exception as e:
        print(f"❌ [SAVE ERROR] 画像保存に失敗: {e}")
        return None

def backup_files() -> gr.update:
    """ファイルバックアップ処理
    
    Returns:
        ボタン更新用のGradio update
    """
    try:
        # Hugging Face Spaces環境ではバックアップ機能を無効化
        if IS_HUGGING_FACE_SPACES:
            print("⚠️ [BACKUP] Hugging Face Spaces環境ではバックアップ機能は利用できません")
            return gr.update(value="Spaces環境では無効")
        
        from config import BACKUP_DIR
        # configから設定を取得
        backup_config = BACKUP_SETTINGS
        timestamp_format = backup_config["backup_timestamp_format"]
        folder_format = backup_config["backup_folder_format"]
        
        timestamp = datetime.now().strftime(timestamp_format)
        backup_dir = os.path.join(BACKUP_DIR, folder_format.format(timestamp=timestamp))
        os.makedirs(backup_dir, exist_ok=True)
        
        # configからバックアップ対象ファイルを取得
        files_to_backup = backup_config["target_files"]
        
        backed_up_files = []
        for filename in files_to_backup:
            if os.path.exists(filename):
                dest_path = os.path.join(backup_dir, filename)
                # configから権限保持設定を取得
                if backup_config["preserve_permissions"]:
                    shutil.copy2(filename, dest_path)
                else:
                    shutil.copy(filename, dest_path)
                backed_up_files.append(filename)
                print(f"✅ [BACKUP] {filename} → {dest_path}")
        
        print(f"🎉 [BACKUP] バックアップ完了: {len(backed_up_files)}個のファイルを保存")
        print(f"📂 [BACKUP] 保存先: {backup_dir}")
        
        return gr.update(value="バックアップ完了")
        
    except Exception as e:
        print(f"❌ [BACKUP] エラー: {e}")
        return gr.update(value="バックアップエラー")