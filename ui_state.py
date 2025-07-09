"""
MS Color Generator - UI状態管理
"""

from typing import List, Dict
from PIL import Image
from config import DEFAULT_GROUP_COLOR


class UIState:
    """UI状態管理クラス"""
    
    def __init__(self):
        # グローバル変数
        self.selected_layer_indices: List[int] = []  # 選択中のレイヤーインデックス
        self.updating_from_click: bool = False  # 画像クリック由来の更新フラグ
        self.updating_programmatically: bool = False  # プログラム的更新中フラグ（旧：updating_from_random）
        self.current_main_image: Image.Image = None  # 現在メイン表示されている画像
        self.pattern_images: List[Image.Image] = []  # 生成された4パターンの画像リスト
        self.pattern_compositions: List[List[str]] = []  # 各パターンの色配列
        self.used_groups_list: List[str] = []  # 使用中グループのリスト
        self.base_colors: Dict[str, str] = {}  # HSVシフトのベース色を保持

    def save_base_colors(self, colorizer):
        """現在の色をベース色として保存"""
        self.base_colors = {}
        used_groups = set(group for group in colorizer.layers if group != "GROUP0")
        for group_name in used_groups:
            self.base_colors[group_name] = colorizer.group_colors.get(group_name, DEFAULT_GROUP_COLOR)
        print(f"🔍 [DEBUG] ベース色保存: {self.base_colors}")

    def reset_patterns(self):
        """パターン関連の状態をリセット"""
        self.pattern_images = []
        self.pattern_compositions = []
        self.used_groups_list = []
        print(f"🔄 [DEBUG] パターン状態リセット")

    def clear_old_patterns(self):
        """古いパターン画像をメモリから解放"""
        try:
            if self.pattern_images:
                # PIL画像オブジェクトを明示的に閉じる
                for img in self.pattern_images:
                    if hasattr(img, 'close'):
                        img.close()
                
            self.pattern_images.clear()
            self.pattern_compositions.clear()
            print("🧹 [MEMORY] 古いパターンをクリアしました")
            
        except Exception as e:
            print(f"❌ [MEMORY ERROR] パターンクリアエラー: {e}")

    def update_pattern_images(self, new_images: List):
        """パターン画像を安全に更新"""
        try:
            # 古い画像を解放
            self.clear_old_patterns()
            
            # 新しい画像を設定
            self.pattern_images = new_images.copy() if new_images else []
            print(f"✅ [MEMORY] パターン画像更新: {len(self.pattern_images)}個")
            
        except Exception as e:
            print(f"❌ [MEMORY ERROR] パターン更新エラー: {e}")
            self.pattern_images = []

    def cleanup_memory(self):
        """メモリクリーンアップ"""
        try:
            self.clear_old_patterns()
            
            if self.current_main_image and hasattr(self.current_main_image, 'close'):
                # メイン画像は閉じない（使用中のため）
                pass
                
            # その他の状態をリセット
            self.base_colors.clear()
            print("🧹 [MEMORY] メモリクリーンアップ完了")
            
        except Exception as e:
            print(f"❌ [MEMORY ERROR] クリーンアップエラー: {e}")

    def set_initial_state(self, colorizer):
        """初期状態を設定（メモリ管理強化版）"""
        try:
            # 古いデータをクリア
            self.clear_old_patterns()
            
            # 現在の色設定で合成
            colorizer.current_composite = colorizer.compose_layers()
            
            # 初期画像を設定
            self.current_main_image = colorizer.current_composite
            
            # 初期パターン情報も設定
            used_groups = set(group for group in colorizer.layers if group != "GROUP0")
            self.used_groups_list = sorted(used_groups)
            
            # 現在の色を各パターンで同じにして初期化
            current_colors = [colorizer.group_colors.get(group, DEFAULT_GROUP_COLOR) for group in self.used_groups_list]
            self.pattern_compositions = [current_colors] * 4
            
            # 初期パターン画像（同じ画像を4回コピー）
            if self.current_main_image:
                self.pattern_images = [self.current_main_image] * 4
            
            # ベース色も保存
            self.save_base_colors(colorizer)
            
            print(f"🔄 [DEBUG] 初期状態設定完了")
            
        except Exception as e:
            print(f"❌ [ERROR] 初期状態設定エラー: {e}")
            # エラー時は最低限の状態を設定
            self.pattern_images = []
            self.pattern_compositions = []
            self.used_groups_list = []