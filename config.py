"""
MS Color Generator - 設定・定数（統合版）
"""

import os
import re
from typing import Dict, Any, List, Tuple

# ======================= 環境判定（新規追加） =======================
# アプリケーション起動時に一度だけ判定
IS_HUGGING_FACE_SPACES = os.getenv("SPACE_ID") is not None

# デバッグ出力
if IS_HUGGING_FACE_SPACES:
    print("🌐 [ENV] Hugging Face Spaces 環境で実行中")
else:
    print("💻 [ENV] ローカル開発環境で実行中")

# ======================= アプリケーション基本設定 =======================
VERSION = "v1.4.2 beta"
MAX_LAYERS = 50  # 読み込み可能な最大レイヤー数

# ======================= 色設定 =======================
TARGET_COLOR = (255, 0, 255)  # マゼンタ色をターゲット色として指定（RGB値）
DEFAULT_GROUP_COLOR = "#aacf53"  # ヨモギ色（デフォルトのグループ色）

# ======================= パフォーマンス設定 =======================
MAX_RETRY_ATTEMPTS = 100  # 色生成の最大試行回数
DEFAULT_SLEEP_TIME = 1.0  # デフォルト待機時間（秒）
IMAGE_CACHE_SIZE = 50     # 画像キャッシュの最大サイズ
MEMORY_CLEANUP_INTERVAL = 10  # メモリクリーンアップ間隔（分）

# ======================= UI基本設定 =======================
GALLERY_COLUMNS = 4       # ギャラリーの列数
GALLERY_ROWS = 1         # ギャラリーの行数
MAIN_IMAGE_HEIGHT = 480  # メイン画像の高さ（ピクセル）
PATTERN_GALLERY_HEIGHT = 250  # パターンギャラリーの高さ（ピクセル）

# ======================= ファイル・フォルダ設定 =======================
FILE_PREFIX = "composite"
SAVE_DIR = "./output"      # 保存フォルダ
LAYER_DIR = "./layer"      # レイヤー読み込みフォルダ
CONFIG_FILE = "grouping.txt"  # 設定ファイル名
BACKUP_DIR = "./oldpy"     # バックアップフォルダ

# ======================= エラーメッセージ =======================
ERROR_MESSAGES = {
    "FILE_NOT_FOUND": "ファイルが見つかりません",
    "INVALID_COLOR": "無効な色形式です",
    "MEMORY_ERROR": "メモリエラーが発生しました",
    "CONFIG_ERROR": "設定ファイルエラー",
    "RESTART_ERROR": "再起動に失敗しました"
}

# ======================= Phase 1: HSV変化パターン設定 =======================
# HSV色相・彩度・明度の変化パターン定義
HSV_VARIATION_PATTERNS = {
    # 等間隔モードでの変化量（度 or %）
    "hue_equal_steps": [-45, -15, 15, 45],           # 色相の等間隔変化量（度）
    "saturation_equal_steps": [-30, -10, 10, 30],    # 彩度の等間隔変化量（%）
    "brightness_equal_steps": [-30, -10, 10, 30],    # 明度の等間隔変化量（%）
    
    # ランダムモードでの変化範囲
    "hue_random_range": (-180, 180),        # 色相ランダム変化範囲（度）
    "saturation_random_range": (-50, 50),   # 彩度ランダム変化範囲（%）
    "brightness_random_range": (-50, 50),   # 明度ランダム変化範囲（%）
    
    # パターン生成設定
    "pattern_count": 4,                      # 生成するパターン数
    "pattern_variation_retry": 10            # パターン生成時の重複回避試行回数
}

# ======================= Phase 1: UIレイアウト設定 =======================
# Gradio UIのレイアウト・寸法設定
UI_LAYOUT = {
    # カラム幅比率設定（Gradio scale値）
    "main_content_scale": 5,      # メイン画像エリアの幅比率
    "picker_control_scale": 5,    # カラーピッカー・制御エリアの幅比率
    "gallery_scale": 6,           # パターンギャラリーエリアの幅比率
    "button_control_scale": 2,    # 操作ボタンエリアの幅比率
    "margin_scale": 1,            # 左右余白エリアの幅比率
    
    # 画像表示サイズ
    "main_image_height": 480,     # メイン画像表示高さ（ピクセル）
    "pattern_gallery_height": 250, # パターンギャラリー高さ（ピクセル）
    
    # ギャラリー設定
    "gallery_columns": 4,         # ギャラリー表示列数
    "gallery_rows": 1,            # ギャラリー表示行数
    "gallery_object_fit": "contain", # 画像フィット方式
    
    # ボタンサイズ
    "small_button_size": "sm",    # 小ボタンサイズ
    "large_button_size": "lg"     # 大ボタンサイズ
}

# ======================= Phase 1: スライダー設定 =======================
# 各スライダーの初期値・範囲・ステップ設定
SLIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
    # 彩度関連スライダー
    "saturation_base": {
        "min": 0, "max": 100, "value": 50, "step": 1,
        "label": "彩度基準 (%)",
        "description": "生成色の彩度中心値"
    },
    "saturation_range": {
        "min": 0, "max": 50, "value": 15, "step": 1,
        "label": "彩度誤差範囲 (%)",
        "description": "彩度基準値からの誤差範囲（±この値）"
    },
    
    # 明度関連スライダー
    "brightness_base": {
        "min": 0, "max": 100, "value": 60, "step": 1,
        "label": "明度基準 (%)",
        "description": "生成色の明度中心値"
    },
    "brightness_range": {
        "min": 0, "max": 50, "value": 15, "step": 1,
        "label": "明度誤差範囲 (%)",
        "description": "明度基準値からの誤差範囲（±この値）"
    },
    
    # 色相関連スライダー
    "hue_center": {
        "min": 0, "max": 360, "value": 180, "step": 5,
        "label": "中心色相 (度)",
        "description": "生成色の色相中心値（0-360度）"
    },
    "hue_range": {
        "min": 1, "max": 180, "value": 60, "step": 5,
        "label": "色相誤差範囲 (度)",
        "description": "色相中心値からの誤差範囲（±この値）"
    },
    
    # 色数・距離設定
    "color_count": {
        "min": 2, "max": 10, "value": 4, "step": 1,
        "label": "生成色数",
        "description": "一度に生成する色の数"
    },
    "min_hue_distance": {
        "min": 0, "max": 180, "value": 30, "step": 5,
        "label": "最小色相距離 (度)",
        "description": "生成色同士の最小色相距離"
    },
    
    # HSVシフトスライダー（リアルタイム色調整用）
    "hue_shift": {
        "min": -180, "max": 180, "value": 0, "step": 5,
        "label": "色相シフト (度)",
        "description": "全色の色相を一括シフト"
    },
    "saturation_shift": {
        "min": -100, "max": 100, "value": 0, "step": 5,
        "label": "彩度シフト (%)",
        "description": "全色の彩度を一括シフト"
    },
    "brightness_shift": {
        "min": -100, "max": 100, "value": 0, "step": 5,
        "label": "明度シフト (%)",
        "description": "全色の明度を一括シフト"
    }
}

# ======================= Phase 2: 色関連設定 =======================
# 色処理・表示に関する設定
COLOR_SETTINGS = {
    # 特殊色定義
    "hot_pink": "#ff69b4",              # ピンク色（新グループ追加時のオプション色）
    "black_fallback": "#000000",        # HSV変換エラー時のフォールバック色
    
    # 透明度・表示設定
    "overlay_alpha": 0.5,               # レイヤークリック時のオーバーレイ透明度（0.0-1.0）
    "default_rgb_fallback": (170, 207, 83),  # RGB変換エラー時のフォールバック値
    
    # エラー時フォールバック色セット
    "error_fallback_colors": ["#ff0000", "#00ff00", "#0000ff", "#ffff00"],  # 赤、緑、青、黄
    
    # HSV表示精度
    "hue_display_precision": 0,         # 色相表示小数点桁数
    "saturation_display_precision": 0,  # 彩度表示小数点桁数
    "brightness_display_precision": 0   # 明度表示小数点桁数
}

# ======================= Phase 2: 画像処理設定 =======================
# 画像読み込み・処理に関する設定
IMAGE_SETTINGS = {
    # ダミー画像設定（レイヤーファイルが見つからない場合）
    "dummy_image_size": (512, 512),     # ダミー画像サイズ（width, height）
    "dummy_image_color": (0, 0, 0, 0),  # ダミー画像色（RGBA）
    "default_image_mode": "RGBA",       # デフォルト画像モード
    
    # ファイル処理設定
    "file_encoding": "utf-8",           # 設定ファイル読み込みエンコーディング
    "layer_file_pattern": r"layer(\d+)\.png",  # レイヤーファイル名正規表現パターン
    "layer_file_flags": re.IGNORECASE,  # レイヤーファイル検索フラグ
    
    # 画像キャッシュ設定
    "enable_image_cache": True,         # 画像キャッシュ有効化
    "cache_cleanup_threshold": 50       # キャッシュクリーンアップ閾値
}

# ======================= Phase 2: システム設定 =======================
# アプリケーション動作に関するシステム設定
SYSTEM_SETTINGS = {
    # 色生成・処理設定
    "max_color_generation_attempts": 100,  # 色生成最大試行回数
    "flag_reset_delay": 1.0,               # プログラム的更新フラグリセット遅延時間（秒）
    
    # ファイル・フォーマット設定
    "timestamp_format": "%Y%m%d_%H%M%S",   # ファイル保存時のタイムスタンプフォーマット
    "group_name_format": "GROUP{i}",       # グループ名フォーマット（{i}は番号）
    "default_group_name": "GROUP0",        # デフォルトグループ名
    
    # スレッド・並行処理設定
    "thread_daemon_mode": True,            # バックグラウンドスレッドのデーモンモード
    "memory_cleanup_enabled": True         # メモリクリーンアップ有効化
}

# ======================= Phase 3: 再起動・復旧設定 =======================
# アプリケーション再起動・復旧処理の設定
RESTART_SETTINGS = {
    # 再起動処理タイミング
    "restart_wait_ms": 2500,              # 再起動開始待機時間（ミリ秒）
    "recovery_check_interval_ms": 1000,   # サーバー復旧確認間隔（ミリ秒）
    "max_recovery_attempts": 30,          # サーバー復旧確認最大試行回数
    
    # 環境変数設定
    "restart_flag_env": "MS_COLOR_RESTART",  # 再起動フラグ環境変数名
    "restart_flag_value": "True"            # 再起動フラグ値
}

# ======================= Phase 3: バックアップ設定 =======================
# コードバックアップ機能の設定
BACKUP_SETTINGS = {
    # バックアップ対象ファイル一覧
    "target_files": [
        "config.py", "models.py", "presets.py", "color_utils.py",
        "layer_manager.py", "ui.py", "ui_handlers.py", "ui_state.py", 
        "ui_utils.py", "ui_generators.py", "main.py", "grouping.txt"
    ],
    
    # バックアップフォルダ設定
    "backup_folder_format": "backup_{timestamp}",  # バックアップフォルダ名フォーマット
    "backup_timestamp_format": "%Y%m%d_%H%M%S",    # バックアップ用タイムスタンプフォーマット
    
    # バックアップ動作設定
    "preserve_permissions": True,                   # ファイル権限保持
    "create_backup_log": True                       # バックアップログ出力
}

# ======================= UIコンポーネント選択肢 =======================
# ラジオボタン・選択肢の定義
UI_CHOICES = {
    # 新グループ色選択肢
    "new_group_colors": ["ヨモギ色", "ピンク色"],
    
    # HSV変化モード選択肢
    "variation_modes": ["等間隔", "ランダム"],
    
    # プリセット名一覧（presets.pyと同期）
    "preset_names": ["ダル", "ライト グレイッシュ", "ペール", "ビビッド", "アース カラー", "モノクロ"]
}

# ======================= 開発・デバッグ設定 =======================
# 開発時のデバッグ・ログ設定
DEBUG_SETTINGS = {
    # デバッグ出力制御
    "enable_debug_prints": True,          # デバッグプリント出力有効化
    "debug_emoji_enabled": True,          # デバッグ絵文字表示有効化
    
    # ログレベル設定
    "log_level": "DEBUG",                 # ログレベル（DEBUG/INFO/WARNING/ERROR）
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    
    # パフォーマンス監視
    "measure_performance": False,         # パフォーマンス測定有効化
    "profile_memory_usage": False         # メモリ使用量プロファイリング
}

# ======================= 設定値アクセス用ヘルパー関数 =======================

def get_slider_config(slider_name: str) -> Dict[str, Any]:
    """スライダー設定を取得
    
    Args:
        slider_name: スライダー名
        
    Returns:
        スライダー設定辞書
    """
    return SLIDER_CONFIGS.get(slider_name, {})

def get_hsv_variation_steps(variation_type: str) -> List[int]:
    """HSV変化ステップを取得
    
    Args:
        variation_type: 変化タイプ（hue/saturation/brightness）
        
    Returns:
        変化ステップのリスト
    """
    key_map = {
        "hue": "hue_equal_steps",
        "saturation": "saturation_equal_steps", 
        "brightness": "brightness_equal_steps"
    }
    key = key_map.get(variation_type, "hue_equal_steps")
    return HSV_VARIATION_PATTERNS.get(key, [-45, -15, 15, 45])

def get_hsv_random_range(variation_type: str) -> Tuple[int, int]:
    """HSVランダム変化範囲を取得
    
    Args:
        variation_type: 変化タイプ（hue/saturation/brightness）
        
    Returns:
        変化範囲のタプル（min, max）
    """
    key_map = {
        "hue": "hue_random_range",
        "saturation": "saturation_random_range",
        "brightness": "brightness_random_range"
    }
    key = key_map.get(variation_type, "hue_random_range")
    return HSV_VARIATION_PATTERNS.get(key, (-180, 180))