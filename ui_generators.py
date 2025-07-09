"""
MS Color Generator - パターン生成関連（config統合版）
"""

import random
import threading
import time
from typing import List, Union, TYPE_CHECKING

import gradio as gr

from config import (
    DEFAULT_GROUP_COLOR, HSV_VARIATION_PATTERNS, SYSTEM_SETTINGS,
    get_hsv_variation_steps, get_hsv_random_range
)
from models import ColorGenerationParams
from color_utils import hex_to_hsv, hsv_to_hex, generate_four_patterns
from ui_utils import update_pickers_only

# 循環インポート回避
if TYPE_CHECKING:
    from layer_manager import LayerColorizer
    from ui_state import UIState


class PatternGenerator:
    """パターン生成管理クラス"""
    
    def __init__(self, colorizer: 'LayerColorizer', state: 'UIState'):
        """初期化
        
        Args:
            colorizer: LayerColorizerインスタンス
            state: UIStateインスタンス
        """
        self.colorizer = colorizer
        self.state = state

    def reset_flag_delayed(self):
        """フラグを遅延してリセット"""
        def reset_after_delay():
            delay = SYSTEM_SETTINGS["flag_reset_delay"]
            time.sleep(delay)
            self.state.updating_programmatically = False
            print(f"🔍 [DEBUG] 遅延フラグリセット: updating_programmatically={self.state.updating_programmatically}")
        
        # 別スレッドで実行
        thread = threading.Thread(target=reset_after_delay)
        thread.daemon = SYSTEM_SETTINGS["thread_daemon_mode"]
        thread.start()

    def _adjust_color_count(self, colors: List[str], target_count: int) -> List[str]:
        """色数をグループ数に合わせて調整
        
        Args:
            colors: 色のリスト
            target_count: 目標色数
            
        Returns:
            調整された色のリスト
        """
        print(f"🔍 [DEBUG] 色数調整: {len(colors)}色 → {target_count}色")
        
        if len(colors) > target_count:
            # 色が多い場合：余分な色を切り捨て
            adjusted = colors[:target_count]
            print(f"🔍 [DEBUG] 色数削減: {colors} → {adjusted}")
            return adjusted
        elif len(colors) < target_count:
            # 色が少ない場合：色を繰り返して補完
            adjusted = colors.copy()
            while len(adjusted) < target_count:
                adjusted.extend(colors)
            adjusted = adjusted[:target_count]
            print(f"🔍 [DEBUG] 色数補完: {colors} → {adjusted}")
            return adjusted
        else:
            print(f"🔍 [DEBUG] 色数一致: {colors}")
            return colors

    def apply_selected_colors_patterns(self, selected_colors: List[str]) -> List[Union[gr.update, float]]:
        """選択された色で4パターンを生成（apply_current_colors_patternsの流れを活用）
        
        Args:
            selected_colors: 選択された色のリスト（HEX形式）
            
        Returns:
            [メイン画像, ギャラリー] + [ピッカー更新リスト] + [HSVスライダーリセット]
        """
        print(f"🎨 [DEBUG] === 選択色で4パターン生成開始 ===")
        
        # プログラム的更新フラグを立てる
        self.state.updating_programmatically = True
        
        try:
            # 使用中のグループを取得（GROUP0を除外）
            default_group = SYSTEM_SETTINGS["default_group_name"]
            used_groups = set(group for group in self.colorizer.layers if group != default_group)
            self.state.used_groups_list = sorted(used_groups)
            
            if not self.state.used_groups_list:
                print(f"❌ 使用中のグループがありません")
                self.state.updating_programmatically = False
                return [gr.update(), []] + [gr.update() for _ in range(self.colorizer.num_layers)] + [0, 0, 0]
            
            # 色数とグループ数を一致させる
            adjusted_colors = self._adjust_color_count(selected_colors, len(self.state.used_groups_list))
            
            print(f"🎨 [DEBUG] 使用グループ: {self.state.used_groups_list}")
            print(f"🎨 [DEBUG] 調整後の色: {adjusted_colors}")
            
            # ★ここから既存のapply_current_colors_patternsと同じ流れ ★
            
            # 4パターン生成（既存のgenerate_four_patterns関数を使用）
            self.state.pattern_compositions = generate_four_patterns(adjusted_colors, self.state.used_groups_list)
            
            # 4つの合成画像を生成
            new_pattern_images = []
            for pattern in self.state.pattern_compositions:
                image = self.colorizer.compose_layers_with_colors(pattern)
                new_pattern_images.append(image)
            
            # グローバル変数を更新
            self.state.pattern_images = new_pattern_images
            
            # 最初のパターンをメイン画像として設定
            self.state.current_main_image = self.state.pattern_images[0]
            
            # 最初のパターンの色を現在の色として設定
            first_pattern = self.state.pattern_compositions[0]
            for group_name, color in zip(self.state.used_groups_list, first_pattern):
                self.colorizer.group_colors[group_name] = color
            
            # カラーピッカーにも反映
            self.colorizer.current_composite = self.state.current_main_image
            
            # ベース色をリセット（新しいパターンが設定されたため）
            self.state.save_base_colors(self.colorizer)
            
            print(f"🎨 [DEBUG] 選択色で4パターン画像生成完了")
            print(f"🎨 [DEBUG] パターン色配列保存: {len(self.state.pattern_compositions)}個")
            
            # ピッカー更新
            picker_updates = update_pickers_only(self.colorizer)
            
            # 結果: [メイン画像, ギャラリー] + [ピッカー更新] + [HSVスライダーリセット]
            result = [self.state.current_main_image, self.state.pattern_images] + picker_updates + [0, 0, 0]
            print(f"🎨 [DEBUG] apply_selected_colors_patterns関数完了: 戻り値数={len(result)}")
            
            # 遅延フラグリセットを開始
            self.reset_flag_delayed()
            print(f"🎨 [DEBUG] 遅延フラグリセット開始")
            
            return result
            
        except Exception as e:
            # エラー時は即座にフラグをリセット
            self.state.updating_programmatically = False
            print(f"🎨 [DEBUG] エラー時フラグリセット: {e}")
            raise

    def apply_random_colors(self, preset_name: str) -> List[Union[gr.update, float]]:
        """プリセットベースでランダムカラーを適用
        
        Args:
            preset_name: プリセット名
            
        Returns:
            [メイン画像] + [ピッカー更新リスト]
        """
        print(f"🔍 [DEBUG] === ランダムカラー開始 ===")
        print(f"🔍 [DEBUG] apply_random_colors関数開始: preset_name={preset_name}")
        print(f"🔍 [DEBUG] フラグ設定前: updating_programmatically={self.state.updating_programmatically}")
        
        # プログラム的更新フラグを立てる
        self.state.updating_programmatically = True
        print(f"🔍 [DEBUG] フラグ設定後: updating_programmatically={self.state.updating_programmatically}")
        
        try:
            self.colorizer.apply_random_colors(preset_name)
            
            print(f"🔍 [DEBUG] update_pickers_only開始")
            picker_updates = update_pickers_only(self.colorizer)
            print(f"🔍 [DEBUG] update_pickers_only完了: {len(picker_updates)}個のピッカー更新")
            
            result = [self.colorizer.current_composite] + picker_updates
            print(f"🔍 [DEBUG] apply_random_colors関数完了: 戻り値数={len(result)}")
            
            # 遅延フラグリセットを開始
            self.reset_flag_delayed()
            print(f"🔍 [DEBUG] 遅延フラグリセット開始")
            
            return result
            
        except Exception as e:
            # エラー時は即座にフラグをリセット
            self.state.updating_programmatically = False
            print(f"🔍 [DEBUG] エラー時フラグリセット: {e}")
            raise

    def generate_hsv_variation_patterns(self, variation_type: str, is_random: bool) -> List[Union[gr.update, float]]:
        """HSV変化パターンを生成
        
        Args:
            variation_type: 変化タイプ（"hue", "saturation", "value"）
            is_random: ランダムモードかどうか
            
        Returns:
            [メイン画像, ギャラリー] + [ピッカー更新リスト] + [HSVスライダーリセット]
        """
        print(f"🎨 [DEBUG] === HSV変化パターン生成開始 ===")
        print(f"🎨 [DEBUG] 変化タイプ: {variation_type}, ランダム: {is_random}")
        
        # プログラム的更新フラグを立てる
        self.state.updating_programmatically = True
        
        try:
            # 使用中のグループを取得
            used_groups = set(group for group in self.colorizer.layers if group != SYSTEM_SETTINGS["default_group_name"])
            self.state.used_groups_list = sorted(used_groups)
            
            if not self.state.used_groups_list:
                print(f"❌ [generate_hsv_variation_patterns] 使用中のグループがありません")
                self.state.updating_programmatically = False
                return [gr.update(), []] + [gr.update() for _ in range(self.colorizer.num_layers)] + [0, 0, 0]
            
            # 現在の色を取得
            current_colors = []
            for group_name in self.state.used_groups_list:
                color = self.colorizer.group_colors.get(group_name, DEFAULT_GROUP_COLOR)
                current_colors.append(color)
            
            print(f"🎨 [DEBUG] 現在の色: {current_colors}")
            
            # 変化量を設定（config から取得）
            pattern_count = HSV_VARIATION_PATTERNS["pattern_count"]
            
            if is_random:
                # ランダムモード
                min_val, max_val = get_hsv_random_range(variation_type)
                variations = []
                retry_count = HSV_VARIATION_PATTERNS["pattern_variation_retry"]
                
                attempt = 0
                while len(variations) < pattern_count and attempt < retry_count:
                    var = random.randint(min_val, max_val)
                    if var not in variations:  # 重複防止
                        variations.append(var)
                    attempt += 1
                
                # 足りない場合は重複を許可して補完
                while len(variations) < pattern_count:
                    variations.append(random.randint(min_val, max_val))
                    
                print(f"🎲 [DEBUG] ランダム変化量: {variations}")
            else:
                # 等間隔モード（config から取得）
                variations = get_hsv_variation_steps(variation_type)
                print(f"📏 [DEBUG] 等間隔変化量: {variations}")
            
            # パターン数に合わせて調整
            if len(variations) > pattern_count:
                variations = variations[:pattern_count]
            elif len(variations) < pattern_count:
                # 不足分は最後の値で補完
                last_val = variations[-1] if variations else 0
                variations.extend([last_val] * (pattern_count - len(variations)))
            
            # 4つのパターン色配列を生成
            self.state.pattern_compositions = []
            for variation in variations:
                pattern_colors = []
                for color in current_colors:
                    # 現在の色をHSVに変換
                    h, s, v = hex_to_hsv(color)
                    
                    # 指定されたパラメータのみ変化
                    if variation_type == "hue":
                        new_h = (h + variation) % 360
                        new_s = s
                        new_v = v
                    elif variation_type == "saturation":
                        new_h = h
                        new_s = max(0, min(100, s + variation))
                        new_v = v
                    elif variation_type in ["value", "brightness"]:
                        new_h = h
                        new_s = s
                        new_v = max(0, min(100, v + variation))
                    else:
                        # デフォルトは色相変化
                        new_h = (h + variation) % 360
                        new_s = s
                        new_v = v
                    
                    # HSVから16進数に変換
                    new_color = hsv_to_hex(new_h, new_s / 100.0, new_v / 100.0)
                    pattern_colors.append(new_color)
                
                self.state.pattern_compositions.append(pattern_colors)
                print(f"🎨 [DEBUG] パターン{len(self.state.pattern_compositions)} ({variation:+}): {pattern_colors}")
            
            # 4つの合成画像を生成
            new_pattern_images = []
            for pattern in self.state.pattern_compositions:
                image = self.colorizer.compose_layers_with_colors(pattern)
                new_pattern_images.append(image)
            
            # グローバル変数を更新
            self.state.pattern_images = new_pattern_images
            
            # 最初のパターンをメイン画像として設定
            self.state.current_main_image = self.state.pattern_images[0]
            
            # 最初のパターンの色を現在の色として設定
            first_pattern = self.state.pattern_compositions[0]
            for group_name, color in zip(self.state.used_groups_list, first_pattern):
                self.colorizer.group_colors[group_name] = color
            
            # カラーピッカーにも反映
            self.colorizer.current_composite = self.state.current_main_image
            
            # ベース色をリセット
            self.state.save_base_colors(self.colorizer)
            
            print(f"🎨 [DEBUG] HSV変化パターン生成完了")
            
            # ピッカー更新
            picker_updates = update_pickers_only(self.colorizer)
            
            # 結果: [メイン画像, ギャラリー] + [ピッカー更新] + [HSVスライダーリセット]
            result = [self.state.current_main_image, self.state.pattern_images] + picker_updates + [0, 0, 0]
            print(f"🎨 [DEBUG] generate_hsv_variation_patterns関数完了: 戻り値数={len(result)}")
            
            # 遅延フラグリセットを開始
            self.reset_flag_delayed()
            print(f"🎨 [DEBUG] 遅延フラグリセット開始")
            
            return result
            
        except Exception as e:
            # エラー時は即座にフラグをリセット
            self.state.updating_programmatically = False
            print(f"🎨 [DEBUG] エラー時フラグリセット: {e}")
            raise

    def apply_current_colors_patterns(self) -> List[Union[gr.update, float]]:
        """現在のピッカーの色で4パターンを生成
        
        Returns:
            [メイン画像, ギャラリー] + [ピッカー更新リスト] + [HSVスライダーリセット]
        """
        print(f"🚨 [DEBUG] === apply_current_colors_patterns メソッド実行中！ ===")
        print(f"🔍 [DEBUG] === 現在の色で4パターン生成開始 ===")
        
        # プログラム的更新フラグを立てる
        self.state.updating_programmatically = True
        print(f"🔍 [DEBUG] プログラム的更新フラグ設定: {self.state.updating_programmatically}")
        
        try:
            # 使用中のグループを取得（GROUP0を除外）
            default_group = SYSTEM_SETTINGS["default_group_name"]
            used_groups = set(group for group in self.colorizer.layers if group != default_group)
            self.state.used_groups_list = sorted(used_groups)
            
            if not self.state.used_groups_list:
                print(f"❌ [apply_current_colors_patterns] 使用中のグループがありません")
                self.state.updating_programmatically = False
                return [gr.update(), []] + [gr.update() for _ in range(self.colorizer.num_layers)] + [0, 0, 0]
            
            # 現在のピッカーの色を取得
            current_colors = []
            for group_name in self.state.used_groups_list:
                color = self.colorizer.group_colors.get(group_name, DEFAULT_GROUP_COLOR)
                current_colors.append(color)
            
            print(f"🔍 [DEBUG] 現在の色: {current_colors}")
            print(f"🔍 [DEBUG] 使用グループ: {self.state.used_groups_list}")
            
            # 4パターン生成（現在の色を使用）
            self.state.pattern_compositions = generate_four_patterns(current_colors, self.state.used_groups_list)
            print(f"🔍 [DEBUG] 生成されたパターン数: {len(self.state.pattern_compositions)}")
            
            # デバッグ: 各パターンをログ出力
            for i, pattern in enumerate(self.state.pattern_compositions):
                assignments = [f"{group}={color}" for group, color in zip(self.state.used_groups_list, pattern)]
                print(f"🎨 [DEBUG] パターン{i+1}: {', '.join(assignments)}")
            
            # 4つの合成画像を生成
            new_pattern_images = []
            for pattern in self.state.pattern_compositions:
                image = self.colorizer.compose_layers_with_colors(pattern)
                new_pattern_images.append(image)
            
            # グローバル変数を更新
            self.state.pattern_images = new_pattern_images
            
            # 最初のパターンをメイン画像として設定
            self.state.current_main_image = self.state.pattern_images[0]
            
            # ★★★ 重要: 最初のパターンの色を現在の色として設定 ★★★
            first_pattern = self.state.pattern_compositions[0]
            print(f"🔍 [DEBUG] 最初のパターン適用開始: {first_pattern}")
            print(f"🔍 [DEBUG] 使用グループリスト: {self.state.used_groups_list}")
            print(f"🔍 [DEBUG] 適用前のgroup_colors: {dict(self.colorizer.group_colors)}")
            
            for i, (group_name, color) in enumerate(zip(self.state.used_groups_list, first_pattern)):
                old_color = self.colorizer.group_colors.get(group_name, DEFAULT_GROUP_COLOR)
                self.colorizer.group_colors[group_name] = color
                print(f"🎨 [DEBUG] {group_name}: {old_color} → {color}")
            
            print(f"🔍 [DEBUG] 適用後のgroup_colors: {dict(self.colorizer.group_colors)}")
            
            # カラーピッカーにも反映（compose_layers実行前）
            self.colorizer.current_composite = self.state.current_main_image
            
            # ベース色をリセット（新しいパターンが設定されたため）
            print(f"🔍 [DEBUG] ベース色保存前のgroup_colors: {dict(self.colorizer.group_colors)}")
            self.state.save_base_colors(self.colorizer)
            print(f"🔍 [DEBUG] ベース色保存後: {self.state.base_colors}")
            
            print(f"🔍 [DEBUG] 現在の色で4パターン画像生成完了")
            print(f"🔍 [DEBUG] パターン色配列保存: {len(self.state.pattern_compositions)}個")
            
            # ピッカー更新
            print(f"🔍 [DEBUG] ピッカー更新開始...")
            picker_updates = update_pickers_only(self.colorizer)
            print(f"🔍 [DEBUG] ピッカー更新完了: {len(picker_updates)}個")
            
            # 結果: [メイン画像, ギャラリー] + [ピッカー更新] + [HSVスライダーリセット]
            result = [self.state.current_main_image, self.state.pattern_images] + picker_updates + [0, 0, 0]
            print(f"🔍 [DEBUG] apply_current_colors_patterns関数完了: 戻り値数={len(result)}")
            
            # 遅延フラグリセットを開始
            self.reset_flag_delayed()
            print(f"🔍 [DEBUG] 遅延フラグリセット開始")
            
            return result
            
        except Exception as e:
            # エラー時は即座にフラグをリセット
            self.state.updating_programmatically = False
            print(f"🔍 [DEBUG] エラー時フラグリセット: {e}")
            import traceback
            traceback.print_exc()
            raise

    def apply_custom_colors(self, sat_base: float, sat_range: float, bright_base: float, 
                          bright_range: float, hue_center: float, hue_range: float, 
                          color_count: int, equal_spacing: bool, min_distance: float) -> List[Union[gr.update, float]]:
        """カスタムパラメータでランダムカラーを適用
        
        Args:
            sat_base: 彩度基準値
            sat_range: 彩度範囲
            bright_base: 明度基準値
            bright_range: 明度範囲
            hue_center: 色相中心値
            hue_range: 色相範囲
            color_count: 色数
            equal_spacing: 等間隔モード
            min_distance: 最小色相距離
            
        Returns:
            [メイン画像, ギャラリー] + [ピッカー更新リスト] + [HSVスライダーリセット]
        """
        print(f"🔍 [DEBUG] === カスタムカラー開始 ===")
        print(f"🔍 [DEBUG] パラメータ: S({sat_base}±{sat_range}%), B({bright_base}±{bright_range}%), H({hue_center}±{hue_range}°), Count({color_count})")
        print(f"🔍 [DEBUG] 等間隔モード: {equal_spacing}, 最小色相距離: {min_distance}°")
        
        # プログラム的更新フラグを立てる
        self.state.updating_programmatically = True
        
        try:
            # カスタムパラメータを作成
            custom_params = ColorGenerationParams(
                saturation_base=sat_base,
                saturation_range=sat_range,
                brightness_base=bright_base,
                brightness_range=bright_range,
                hue_center=hue_center,
                hue_range=hue_range,
                color_count=color_count,
                equal_hue_spacing=equal_spacing,
                min_hue_distance=min_distance
            )
            
            # 4パターン生成（色配列とグループリストも取得）
            self.state.pattern_compositions = self.colorizer.apply_random_colors_with_params(custom_params)
            
            # 使用中グループリストも保存
            default_group = SYSTEM_SETTINGS["default_group_name"]
            used_groups = set(group for group in self.colorizer.layers if group != default_group)
            self.state.used_groups_list = sorted(used_groups)
            
            # 4つの合成画像を生成
            new_pattern_images = []
            for pattern in self.state.pattern_compositions:
                image = self.colorizer.compose_layers_with_colors(pattern)
                new_pattern_images.append(image)
            
            # グローバル変数を更新
            self.state.pattern_images = new_pattern_images
            
            # 最初のパターンをメイン画像として設定
            self.state.current_main_image = self.state.pattern_images[0]
            
            # カラーピッカーにも1枚目のパターンの色を反映
            self.colorizer.current_composite = self.state.current_main_image
            
            # ベース色をリセット（新しい色が設定されたため）
            self.state.save_base_colors(self.colorizer)
            
            print(f"🔍 [DEBUG] 4パターン画像生成完了")
            print(f"🔍 [DEBUG] パターン色配列保存: {len(self.state.pattern_compositions)}個")
            print(f"🔍 [DEBUG] 使用グループ保存: {self.state.used_groups_list}")
            
            # ピッカー更新
            picker_updates = update_pickers_only(self.colorizer)
            
            # 結果: [メイン画像, ギャラリー] + [ピッカー更新] + [HSVスライダーリセット]
            result = [self.state.current_main_image, self.state.pattern_images] + picker_updates + [0, 0, 0]  # HSVスライダーを0にリセット
            print(f"🔍 [DEBUG] apply_custom_colors関数完了: 戻り値数={len(result)}")
            
            # 遅延フラグリセットを開始
            self.reset_flag_delayed()
            print(f"🔍 [DEBUG] 遅延フラグリセット開始")
            
            return result
            
        except Exception as e:
            # エラー時は即座にフラグをリセット
            self.state.updating_programmatically = False
            print(f"🔍 [DEBUG] エラー時フラグリセット: {e}")
            raise