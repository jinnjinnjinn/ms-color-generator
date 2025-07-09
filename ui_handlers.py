"""
MS Color Generator - UIイベントハンドラー（config統合版）
"""

from typing import List, Tuple, Union, TYPE_CHECKING

import gradio as gr
from PIL import Image

from config import (
    TARGET_COLOR, DEFAULT_GROUP_COLOR, COLOR_SETTINGS, 
    SYSTEM_SETTINGS, UI_CHOICES
)
from color_utils import hex_to_hsv, hsv_to_hex
from presets import COLOR_PRESETS
from ui_utils import update_pickers_only

# 循環インポート回避
if TYPE_CHECKING:
    from layer_manager import LayerColorizer
    from ui_state import UIState


class UIHandlers:
    """UIイベントハンドラークラス"""
    
    def __init__(self, colorizer: 'LayerColorizer', state_manager: 'UIState'):
        """初期化
        
        Args:
            colorizer: LayerColorizerインスタンス
            state_manager: UIStateインスタンス
        """
        self.colorizer = colorizer
        self.state = state_manager
        
    def on_click(self, evt: gr.SelectData) -> Tuple[gr.update, gr.update]:
        """画像クリック時のイベントハンドラ - レイヤー検出とラジオボタン更新
        
        Args:
            evt: Gradioクリックイベント
            
        Returns:
            (メイン画像更新, ラジオボタン更新)のタプル
        """
        print(f"🖱️ [on_click] 開始 - フラグを True に設定")
        # フラグを立てる（次のapply_group_change 1回だけスキップ）
        self.state.updating_from_click = True
        
        if self.state.current_main_image is None:
            print(f"❌ [on_click] メイン画像なし")
            return self.state.current_main_image, gr.update(value=None)
        
        x, y = evt.index
        hit_layers = []
        
        # クリック位置のレイヤーを検出
        for i, img in enumerate(self.colorizer.orig_images):
            if x < img.width and y < img.height and img.getpixel((x, y))[:3] == TARGET_COLOR:
                hit_layers.append(i)
        
        self.state.selected_layer_indices = hit_layers
        
        if not hit_layers:
            # レイヤーなし
            print(f"📍 [on_click] 座標({x}, {y}) レイヤーなし")
            info_text = f"座標 ({x}, {y}) → レイヤーなし"
            main_image_update = gr.update(label=f"**メイン表示** {info_text}")
            return main_image_update, gr.update(value=None)
        
        # オーバーレイ作成（透明度はconfigから取得）
        overlay = self.state.current_main_image.copy().convert("RGBA")
        overlay_alpha = COLOR_SETTINGS["overlay_alpha"]
        
        for layer_idx in hit_layers:
            layer = self.colorizer.replace_color(
                self.colorizer.orig_images[layer_idx].copy(), 
                self.colorizer.hex_to_rgb(self.colorizer.get_layer_color(layer_idx))
            )
            alpha = layer.split()[-1].point(lambda a: int(a * overlay_alpha))
            layer.putalpha(alpha)
            overlay = Image.alpha_composite(overlay, layer)
        
        # レイヤー情報作成
        layer_info = []
        groups_in_selection = set()
        for layer_idx in hit_layers:
            layer_num = layer_idx + 1
            group_name = self.colorizer.layers[layer_idx]
            layer_info.append(f"Layer{layer_num}({group_name})")
            groups_in_selection.add(group_name)
        
        info_text = f"座標 ({x}, {y}) → {', '.join(layer_info)}"
        
        # 共通グループがある場合はそのグループを選択、異なる場合はNone
        default_group = list(groups_in_selection)[0] if len(groups_in_selection) == 1 else None
        
        # GROUP追加を表示するかチェック
        should_show_group_add = self._should_show_group_add(hit_layers)
        
        # ラジオボタンの選択肢を動的に設定
        available_choices = self.colorizer.get_available_groups()
        if should_show_group_add:
            available_choices.append("GROUP追加")
        
        print(f"🎯 [on_click] Layer検出: {hit_layers}, Group: {default_group}")
        print(f"📡 [on_click] ラジオボタン更新を送信 - 次の1回のみスキップ")
        print(f"📋 [on_click] 選択肢: {available_choices}")
        
        # メイン画像のラベルを更新してオーバーレイを表示
        main_image_update = gr.update(value=overlay, label=f"メイン表示 {info_text}")
        
        # ラジオボタンを現在のグループ位置に更新
        return main_image_update, gr.update(value=default_group, choices=available_choices)

    def _should_show_group_add(self, hit_layers: List[int]) -> bool:
        """GROUP追加を表示するかチェック
        
        Args:
            hit_layers: ヒットしたレイヤーのリスト
            
        Returns:
            GROUP追加を表示するかの真偽値
        """
        if len(hit_layers) > 1:
            # 複数レイヤー選択時は常にGROUP追加可能
            print(f"✅ [on_click] 複数レイヤー選択({len(hit_layers)}個) → GROUP追加可能")
            return True
        elif len(hit_layers) == 1:
            # 単一レイヤー選択時は、そのグループに他のレイヤーがある場合のみGROUP追加可能
            current_group = self.colorizer.layers[hit_layers[0]]
            group_layer_count = len(self.colorizer.get_group_layers(current_group))
            if group_layer_count > 1:
                print(f"✅ [on_click] 単一レイヤー選択だが、グループ{current_group}に{group_layer_count}個のレイヤー → GROUP追加可能")
                return True
            else:
                print(f"❌ [on_click] 単一レイヤー選択で、グループ{current_group}に1個のみ → GROUP追加無効")
                return False
        return False

    def on_gallery_select(self, evt: gr.SelectData) -> List[Union[gr.update, float]]:
        """ギャラリー選択時のイベントハンドラ
        
        Args:
            evt: Gradioギャラリー選択イベント
            
        Returns:
            [メイン画像] + [ピッカー更新リスト] + [HSVスライダーリセット]
        """
        if hasattr(evt, 'index') and isinstance(evt.index, int):
            # ギャラリーの選択インデックスを取得
            selected_index = evt.index
            print(f"🖼️ [on_gallery_select] パターン{selected_index + 1}が選択されました")
            
            # 選択されたパターンをメイン画像として設定
            if selected_index < len(self.state.pattern_images):
                self.state.current_main_image = self.state.pattern_images[selected_index]
                print(f"🔄 [on_gallery_select] メイン画像を更新: パターン{selected_index + 1}")
                
                # ★重要: 選択されたパターンの色情報を内部状態に反映
                if selected_index < len(self.state.pattern_compositions) and self.state.used_groups_list:
                    # 修正：正しいパターンインデックスの色を取得
                    selected_colors = self.state.pattern_compositions[selected_index]
                    print(f"🎨 [on_gallery_select] 色情報を更新: {selected_colors}")
                    
                    # colorizer.group_colorsを選択されたパターンに合わせて更新
                    for i, group_name in enumerate(self.state.used_groups_list):
                        if i < len(selected_colors):
                            old_color = self.colorizer.group_colors.get(group_name, "未設定")
                            self.colorizer.group_colors[group_name] = selected_colors[i]
                            print(f"   {group_name}: {old_color} → {selected_colors[i]}")
                    
                    # ベース色をリセット（新しい色が選択されたため）
                    self.state.save_base_colors(self.colorizer)
                    
                    # カラーピッカーを更新
                    picker_updates = update_pickers_only(self.colorizer)
                    print(f"🔄 [on_gallery_select] カラーピッカーも更新")
                    
                    return [self.state.current_main_image] + picker_updates + [0, 0, 0]  # HSVスライダーもリセット
        
        print(f"❌ [on_gallery_select] 選択処理に失敗")
        return [gr.update()] + [gr.update() for _ in range(self.colorizer.num_layers)] + [gr.update(), gr.update(), gr.update()]

    def apply_group_change(self, selected_group: str, color_option: str = None) -> List[gr.update]:
        """選択したレイヤーにグループを適用
        
        Args:
            selected_group: 選択されたグループ名
            color_option: 色オプション
            
        Returns:
            [メイン画像] + [ピッカー更新リスト] + [ラジオボタン更新]
        """
        print(f"🔥 [apply_group_change] 発火！ Group: {selected_group}, Color Option: {color_option}, フラグ: {self.state.updating_from_click}")
        print(f"🔍 [apply_group_change] 選択レイヤー: {self.state.selected_layer_indices}")
        
        # 画像クリック由来の更新の場合は1回だけスキップしてフラグをリセット
        if self.state.updating_from_click:
            print(f"⏭️ [apply_group_change] 画像クリック由来のため1回スキップ - フラグをリセット")
            self.state.updating_from_click = False  # ここでフラグをリセット
            # スキップ時は画像を更新せず、ピッカーのみ更新
            return [gr.update()] + update_pickers_only(self.colorizer) + [gr.update()]
        
        print(f"⚙️ [apply_group_change] 手動選択による処理実行")
        
        if not self.state.selected_layer_indices:
            print(f"❌ [apply_group_change] 選択レイヤーが空です！画像をクリックしてレイヤーを選択してください")
            return [gr.update()] + update_pickers_only(self.colorizer) + [gr.update()]
            
        if not selected_group:
            print(f"❌ [apply_group_change] グループが選択されていません")
            return [gr.update()] + update_pickers_only(self.colorizer) + [gr.update()]
        
        # GROUP追加の処理
        if selected_group == "GROUP追加":
            if not self._validate_group_addition():
                return [gr.update()] + update_pickers_only(self.colorizer) + [gr.update()]
            
            selected_group = self.colorizer.add_new_group()
            print(f"➕ [apply_group_change] 新グループ追加: {selected_group}")
            
            # 色の設定
            self._set_new_group_color(selected_group, color_option)
        
        # 選択されたレイヤーのグループを更新
        print(f"🔄 [apply_group_change] レイヤー {self.state.selected_layer_indices} を {selected_group} に変更")
        for layer_idx in self.state.selected_layer_indices:
            old_group = self.colorizer.layers[layer_idx]
            self.colorizer.update_layer_group(layer_idx, selected_group)
            print(f"   Layer{layer_idx+1}: {old_group} → {selected_group}")
        
        # 現在の設定で画像を更新
        updated_image = self.colorizer.compose_layers()
        self.state.current_main_image = updated_image
        
        print(f"✅ [apply_group_change] 処理完了")
        print(f"📋 [apply_group_change] 更新後のレイヤー設定: {self.colorizer.layers}")
        print(f"🎨 [apply_group_change] 更新後のグループ色: {self.colorizer.group_colors}")
        
        # 新しい選択肢でラジオボタンを更新
        new_choices = self.colorizer.get_available_groups() + ["GROUP追加"]
        radio_update = gr.update(choices=new_choices, value=selected_group)
        print(f"📻 [apply_group_change] ラジオボタン選択肢更新: {new_choices}")
        
        return [updated_image] + update_pickers_only(self.colorizer) + [radio_update]

    def _validate_group_addition(self) -> bool:
        """GROUP追加の安全チェック
        
        Returns:
            GROUP追加が可能かの真偽値
        """
        print(f"🛡️ [apply_group_change] GROUP追加の安全チェック開始")
        
        # 複数レイヤー選択の場合はOK
        if len(self.state.selected_layer_indices) > 1:
            print(f"✅ [apply_group_change] 複数レイヤー選択({len(self.state.selected_layer_indices)}個) → GROUP追加許可")
            return True
        else:
            # 単一レイヤーの場合、そのグループに他のレイヤーがあるかチェック
            layer_idx = self.state.selected_layer_indices[0]
            current_group = self.colorizer.layers[layer_idx]
            group_layer_count = len(self.colorizer.get_group_layers(current_group))
            
            if group_layer_count <= 1:
                print(f"🚫 [apply_group_change] 安全チェック失敗: {current_group}に{group_layer_count}個のレイヤーのみ → GROUP追加無効")
                print(f"❌ [apply_group_change] GROUP追加を拒否しました")
                return False
            else:
                print(f"✅ [apply_group_change] 安全チェック通過: {current_group}に{group_layer_count}個のレイヤー → GROUP追加許可")
                return True

    def _set_new_group_color(self, group_name: str, color_option: str):
        """新グループの色を設定
        
        Args:
            group_name: グループ名
            color_option: 色オプション
        """
        # UI_CHOICESから選択肢を取得
        color_choices = UI_CHOICES["new_group_colors"]
        
        if color_option == color_choices[1]:  # "ピンク色"
            # ピンク色を設定（configから取得）
            pink_color = COLOR_SETTINGS["hot_pink"]
            self.colorizer.group_colors[group_name] = pink_color
            print(f"🎨 [apply_group_change] ピンク色({pink_color})を設定")
        else:
            # ヨモギ色（デフォルト）
            self.colorizer.group_colors[group_name] = DEFAULT_GROUP_COLOR
            print(f"🎨 [apply_group_change] ヨモギ色({DEFAULT_GROUP_COLOR})を設定")

    def update_color_from_picker(self, picker_index: int, new_color: str) -> List[Union[gr.update, float]]:
        """カラーピッカーからの色更新
        
        Args:
            picker_index: ピッカーのインデックス
            new_color: 新しい色
            
        Returns:
            [メイン画像] + [ピッカー更新リスト] + [HSVスライダーリセット]
        """
        print(f"🔍 [DEBUG] update_color_from_picker実行: ピッカー{picker_index}, 色{new_color}")
        
        sorted_group_data = self.colorizer.get_sorted_group_data(self.colorizer.layers)
        
        if picker_index < len(sorted_group_data):
            group_name, layer_indices = sorted_group_data[picker_index]
            current_color = self.colorizer.group_colors.get(group_name, DEFAULT_GROUP_COLOR)
            
            # ★修正: 同じ色の場合はHSVスライダーをリセットしない★
            if current_color == new_color:
                print(f"🔍 [DEBUG] {group_name}の色は既に{new_color}です - HSVスライダーリセットなし")
                # HSVスライダーをリセットせずに現在の状態を保持
                return [gr.update()] + [gr.update() for _ in range(self.colorizer.num_layers)] + [gr.update(), gr.update(), gr.update()]
            
            print(f"🔍 [DEBUG] {group_name}の色を{current_color} → {new_color}に更新")
            self.colorizer.group_colors[group_name] = new_color
            
            # 合成画像を更新
            updated_image = self.colorizer.compose_layers()
            self.state.current_main_image = updated_image
            
            # ベース色をリセット（手動で色が変更されたため）
            self.state.save_base_colors(self.colorizer)
            
            # ピッカーのラベルも更新（HSV値を含める）
            picker_updates = update_pickers_only(self.colorizer)
            return [updated_image] + picker_updates + [0, 0, 0]  # HSVスライダーもリセット
        
        return [gr.update()] + [gr.update() for _ in range(self.colorizer.num_layers)] + [gr.update(), gr.update(), gr.update()]

    def apply_hsv_shift(self, hue_shift: float, sat_shift: float, val_shift: float) -> List[gr.update]:
        """現在の全色にHSVシフトを適用（ベース色からの計算）
        
        Args:
            hue_shift: 色相シフト値
            sat_shift: 彩度シフト値
            val_shift: 明度シフト値
            
        Returns:
            [メイン画像] + [ピッカー更新リスト]
        """
        print(f"🎨 [DEBUG] HSVシフト適用: H{hue_shift:+.0f}° S{sat_shift:+.0f}% V{val_shift:+.0f}%")
        
        # ベース色が未設定の場合は現在の色を保存
        if not self.state.base_colors:
            self.state.save_base_colors(self.colorizer)
        
        # 使用中のグループを取得（configから）
        default_group = SYSTEM_SETTINGS["default_group_name"]
        used_groups = set(group for group in self.colorizer.layers if group != default_group)
        
        for group_name in used_groups:
            # ベース色を取得（なければ現在の色）
            base_color = self.state.base_colors.get(group_name, self.colorizer.group_colors.get(group_name, DEFAULT_GROUP_COLOR))
            
            # ベース色をHSVに変換
            h, s, v = hex_to_hsv(base_color)
            
            # シフトを適用
            new_h = (h + hue_shift) % 360  # 色相は0-360°でループ
            new_s = max(0, min(100, s + sat_shift))  # 彩度は0-100%でクランプ
            new_v = max(0, min(100, v + val_shift))  # 明度は0-100%でクランプ
            
            # HSVから16進数に変換
            new_color = hsv_to_hex(new_h, new_s / 100.0, new_v / 100.0)
            
            # 色を更新
            self.colorizer.group_colors[group_name] = new_color
            print(f"🔍 [DEBUG] {group_name}: {base_color} → {new_color} (H:{h:.0f}→{new_h:.0f}, S:{s:.0f}→{new_s:.0f}, V:{v:.0f}→{new_v:.0f})")
        
        # 合成画像を更新
        updated_image = self.colorizer.compose_layers()
        self.state.current_main_image = updated_image
        
        # ピッカーも更新
        picker_updates = update_pickers_only(self.colorizer)
        return [updated_image] + picker_updates

    def set_preset_params(self, preset_name: str) -> Tuple[float, ...]:
        """プリセットに応じてパラメータを設定
        
        Args:
            preset_name: プリセット名
            
        Returns:
            パラメータのタプル
        """
        if preset_name in COLOR_PRESETS:
            params = COLOR_PRESETS[preset_name]
            return (
                params.saturation_base,
                params.saturation_range,
                params.brightness_base,
                params.brightness_range,
                params.hue_center,
                params.hue_range,
                params.color_count,
                params.equal_hue_spacing,
                params.min_hue_distance
            )
        else:
            # デフォルト値を返す（configのスライダー設定から取得）
            from config import SLIDER_CONFIGS
            return (
                SLIDER_CONFIGS["saturation_base"]["value"],
                SLIDER_CONFIGS["saturation_range"]["value"],
                SLIDER_CONFIGS["brightness_base"]["value"],
                SLIDER_CONFIGS["brightness_range"]["value"],
                SLIDER_CONFIGS["hue_center"]["value"],
                SLIDER_CONFIGS["hue_range"]["value"],
                SLIDER_CONFIGS["color_count"]["value"],
                False,  # equal_hue_spacing
                SLIDER_CONFIGS["min_hue_distance"]["value"]
            )

    def create_picker_change_handler(self, picker_index: int):
        """カラーピッカー変更ハンドラーを作成
        
        Args:
            picker_index: ピッカーのインデックス
            
        Returns:
            ハンドラー関数
        """
        def handler(new_color: str) -> List[Union[gr.update, float]]:
            # プログラム的更新中は念のためスキップ（ランダム生成時など）
            if self.state.updating_programmatically:
                print(f"🔒 [DEBUG] プログラム的更新中のため、ピッカー{picker_index}の変更をスキップ")
                return [gr.update()] + [gr.update() for _ in range(self.colorizer.num_layers)] + [gr.update(), gr.update(), gr.update()]
            
            print(f"🔍 [DEBUG] ピッカー{picker_index}からの色更新: {new_color}")
            return self.update_color_from_picker(picker_index, new_color)
        return handler

    def create_hsv_shift_handler(self):
        """HSVシフトハンドラーを作成
        
        Returns:
            ハンドラー関数
        """
        def handler(hue_shift: float, sat_shift: float, val_shift: float) -> List[gr.update]:
            if self.state.updating_programmatically:
                print(f"🔒 [DEBUG] プログラム的更新中のため、HSVシフトをスキップ")
                return [gr.update()] + [gr.update() for _ in range(self.colorizer.num_layers)]
            
            print(f"🎨 [DEBUG] HSVシフト実行: H{hue_shift:+.0f}° S{sat_shift:+.0f}% V{val_shift:+.0f}%")
            return self.apply_hsv_shift(hue_shift, sat_shift, val_shift)
        return handler