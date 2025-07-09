"""
MS Color Generator - UI関連（Color Extractor統合版・完全修正版）
"""

import os
from typing import List, Union, Dict, Any
import colorsys
from collections import Counter

import gradio as gr
import numpy as np
from PIL import Image

from config import (
    VERSION, DEFAULT_GROUP_COLOR, LAYER_DIR, UI_LAYOUT, 
    SLIDER_CONFIGS, UI_CHOICES, get_slider_config, IS_HUGGING_FACE_SPACES
)
from layer_manager import LayerColorizer
from ui_state import UIState
from ui_handlers import UIHandlers
from ui_generators import PatternGenerator
from ui_utils import create_initial_pickers, update_pickers_only, do_save, restart_server, backup_files


# Color Extractor クラス
class ColorExtractor:
    """画像から色を抽出するクラス（K-Meansのみ）"""
    
    def __init__(self):
        self.has_sklearn = self._check_sklearn()
    
    def _check_sklearn(self) -> bool:
        """scikit-learnが利用可能かチェック"""
        try:
            from sklearn.cluster import KMeans
            return True
        except ImportError:
            return False
    
    def extract_colors_with_hue_complement(self, image: Image.Image, base_count: int = 5) -> Dict[str, List[tuple]]:
        """5色抽出 + 色相補完"""
        print(f"🎨 色相補完抽出開始: ベース{base_count}色 + 色相分析")
        
        # ベース色を抽出（5色）
        base_colors = self.extract_colors_kmeans(image, base_count)
        
        # より多くの色を抽出（16色）して色相分析用データを取得
        extended_colors = self.extract_colors_kmeans(image, 16)
        
        # 色相補完を実行
        complement_colors = self._find_hue_complements(base_colors, extended_colors)
        
        # 結果をまとめる
        all_colors = base_colors + complement_colors
        
        result = {
            "base": base_colors,
            "complement": complement_colors,
            "all": all_colors,
            "extended": extended_colors
        }
        
        print(f"🌈 色相補完完了: ベース{len(base_colors)}色 + 補完{len(complement_colors)}色 = 合計{len(all_colors)}色")
        
        return result
    
    def _find_hue_complements(self, base_colors: List[tuple], 
                            extended_colors: List[tuple], 
                            hue_threshold: float = 60.0, 
                            saturation_min: float = 30.0) -> List[tuple]:
        """色相補完色を検索"""
        complement_colors = []
        
        # ベース色の色相を取得（グレースケール除外）
        base_hues = []
        for rgb in base_colors:
            h, s, v = ColorUtils.rgb_to_hsv(rgb)
            if s >= saturation_min:
                base_hues.append(h)
        
        print(f"🔍 ベース色相: {[f'{h:.0f}°' for h in base_hues]} (彩度{saturation_min}%以上)")
        
        # 拡張色から重要な色相を検索
        for rgb in extended_colors:
            if rgb in base_colors:
                continue
            
            h, s, v = ColorUtils.rgb_to_hsv(rgb)
            
            # 彩度と明度の条件チェック
            if s < saturation_min or v < 20:
                continue
            
            # 既存の色相と十分に離れているかチェック
            is_different_hue = True
            for base_hue in base_hues:
                hue_diff = self._calculate_hue_difference(h, base_hue)
                if hue_diff < hue_threshold:
                    is_different_hue = False
                    break
            
            # 既に追加された補完色との重複チェック
            if is_different_hue:
                for comp_rgb in complement_colors:
                    comp_h, comp_s, comp_v = ColorUtils.rgb_to_hsv(comp_rgb)
                    if comp_s >= saturation_min:
                        hue_diff = self._calculate_hue_difference(h, comp_h)
                        if hue_diff < hue_threshold:
                            is_different_hue = False
                            break
            
            if is_different_hue:
                complement_colors.append(rgb)
                base_hues.append(h)
                color_name = ColorUtils.get_color_name(rgb)
                print(f"  ➕ 補完色発見: {color_name} (色相{h:.0f}°, 彩度{s:.0f}%, 明度{v:.0f}%)")
                
                # 最大3色まで補完
                if len(complement_colors) >= 3:
                    break
        
        return complement_colors
    
    def _calculate_hue_difference(self, hue1: float, hue2: float) -> float:
        """色相の差を計算（円環を考慮）"""
        diff = abs(hue1 - hue2)
        if diff > 180:
            diff = 360 - diff
        return diff
    
    def extract_colors_kmeans(self, image: Image.Image, num_colors: int = 5) -> List[tuple]:
        """K-Meansクラスタリングで主要色を抽出"""
        if not self.has_sklearn:
            print("⚠️ scikit-learnが利用できません。")
            return [(128, 128, 128)] * num_colors
        
        from sklearn.cluster import KMeans
        
        # 画像をリサイズ
        image = image.resize((150, 150))
        
        # RGB画像に変換
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # numpy配列に変換
        data = np.array(image)
        data = data.reshape((-1, 3))
        
        # 透明度や完全な黒を除外
        data = data[~np.all(data == [0, 0, 0], axis=1)]
        
        if len(data) == 0:
            return [(128, 128, 128)] * num_colors
        
        # K-Meansクラスタリング
        actual_clusters = min(num_colors, len(data))
        kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
        kmeans.fit(data)
        
        colors = kmeans.cluster_centers_.astype(int)
        
        # クラスターのサイズでソート
        labels = kmeans.labels_
        cluster_sizes = Counter(labels)
        sorted_colors = []
        
        for cluster_id, size in cluster_sizes.most_common():
            color = colors[cluster_id]
            sorted_colors.append(tuple(color))
        
        # 不足分を補完
        while len(sorted_colors) < num_colors:
            sorted_colors.append((128, 128, 128))
        
        return sorted_colors[:num_colors]


class ColorUtils:
    """色関連のユーティリティ"""
    
    @staticmethod
    def rgb_to_hex(rgb: tuple) -> str:
        """RGB値を16進数に変換"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    @staticmethod
    def rgb_to_hsv(rgb: tuple) -> tuple:
        """RGB値をHSV値に変換"""
        r, g, b = [x / 255.0 for x in rgb]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return (h * 360, s * 100, v * 100)
    
    @staticmethod
    def get_color_name(rgb: tuple) -> str:
        """RGB値に最も近い色名を取得（簡易版）"""
        r, g, b = rgb
        
        # グレースケール判定
        if abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30:
            if r < 50:
                return "黒系"
            elif r < 100:
                return "濃いグレー"
            elif r < 150:
                return "グレー"
            elif r < 200:
                return "薄いグレー"
            else:
                return "白系"
        
        # カラー判定
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        
        if max_val - min_val < 50:
            return "グレー系"
        
        # 主要色判定
        if r > g and r > b:
            if g > b:
                return "オレンジ系" if g > r * 0.6 else "赤系"
            else:
                return "ピンク系" if b > r * 0.6 else "赤系"
        elif g > r and g > b:
            if r > b:
                return "黄緑系" if r > g * 0.6 else "緑系"
            else:
                return "青緑系" if b > g * 0.6 else "緑系"
        else:
            if r > g:
                return "紫系" if r > b * 0.6 else "青系"
            else:
                return "水色系" if g > b * 0.6 else "青系"
    
    @staticmethod
    def calculate_brightness(rgb: tuple) -> float:
        """色の明度を計算"""
        r, g, b = rgb
        return (0.299 * r + 0.587 * g + 0.114 * b)


# グローバル変数（アプリケーション状態管理）
colorizer = LayerColorizer()
ui_state = UIState()
ui_handlers = UIHandlers(colorizer, ui_state)
pattern_generator = PatternGenerator(colorizer, ui_state)
color_extractor = ColorExtractor()
extracted_colors = []  # 抽出された色の保存用


def update_colors() -> List[Union[gr.update, list]]:
    """初期色更新処理"""
    ui_state.set_initial_state(colorizer)
    picker_updates = update_pickers_only(colorizer)
    return [ui_state.current_main_image, ui_state.pattern_images] + picker_updates


# この関数は削除（個別チェックボックス対応で不要）


def extract_and_display_colors(image):
    """画像から色を抽出して3分割表示（チェックボックス + 色見本 + テキスト）"""
    print(f"🔍 extract_and_display_colors呼び出し: image={image is not None}")
    
    if image is None:
        print("❌ 画像がNullです")
        # 8行全て非表示にする
        row_updates = [gr.update(visible=False) for _ in range(8)]
        checkbox_updates = [gr.update(value=False) for _ in range(8)]
        swatch_updates = [gr.update(value="") for _ in range(8)]
        label_updates = [gr.update(value="") for _ in range(8)]
        return [gr.update(visible=False)] + row_updates + checkbox_updates + swatch_updates + label_updates
    
    try:
        print("🎨 色抽出処理開始...")
        
        # 固定パラメータで色抽出実行
        results = color_extractor.extract_colors_with_hue_complement(
            image, base_count=5
        )
        
        print(f"🔍 抽出結果: base={len(results['base'])}色, extended={len(results['extended'])}色")
        
        # 固定設定で色相補完
        base_colors = results["base"]
        extended_colors = results["extended"]
        complement_colors = color_extractor._find_hue_complements(
            base_colors, extended_colors, 
            hue_threshold=60.0,  # 固定値
            saturation_min=30.0  # 固定値
        )
        
        print(f"🔍 色相補完結果: complement={len(complement_colors)}色")
        
        # 色情報の作成
        color_data = []
        all_colors = base_colors + complement_colors
        
        print("🔍 全色処理中...")
        for i, rgb in enumerate(all_colors):
            hex_color = ColorUtils.rgb_to_hex(rgb)
            h, s, v = ColorUtils.rgb_to_hsv(rgb)
            
            color_data.append({
                'rgb': rgb,
                'hex': hex_color,
                'h': h,
                's': s,
                'v': v,
                'index': i
            })
            print(f"  色{i+1}: {hex_color} (H:{h:.0f}° S:{s:.0f}% V:{v:.0f}%)")
        
        # グローバル変数に保存
        global extracted_colors
        extracted_colors = color_data
        
        # 8行の更新データを作成
        row_updates = []
        checkbox_updates = []
        swatch_updates = []
        label_updates = []
        
        for i in range(8):
            if i < len(color_data):
                color_info = color_data[i]
                hex_color = color_info['hex']
                h = color_info['h']
                s = color_info['s'] 
                v = color_info['v']
                
                # 行を表示
                row_updates.append(gr.update(visible=True))
                
                # チェックボックス（初期選択）
                checkbox_updates.append(gr.update(value=True))
                
                # 色見本HTML
                swatch_html = f"""
                <div style="
                    width: 50px; 
                    height: 30px; 
                    background-color: {hex_color}; 
                    border: 1px solid #ddd; 
                    border-radius: 4px;
                    margin: 2px;
                "></div>
                """
                swatch_updates.append(gr.update(value=swatch_html))
                
                # テキストラベル
                label_text = f"`{hex_color}` (H:{h:.0f}° S:{s:.0f}% V:{v:.0f}%)"
                label_updates.append(gr.update(value=label_text))
            else:
                # 色がない場合は非表示
                row_updates.append(gr.update(visible=False))
                checkbox_updates.append(gr.update(value=False))
                swatch_updates.append(gr.update(value=""))
                label_updates.append(gr.update(value=""))
        
        print(f"✅ 色抽出完了: {len(color_data)}個の色")
        
        # 戻り値: color_selection_area + 8行 + 8チェックボックス + 8色見本 + 8ラベル
        return [gr.update(visible=True)] + row_updates + checkbox_updates + swatch_updates + label_updates
        
    except Exception as e:
        print(f"❌ 色抽出エラー: {e}")
        import traceback
        traceback.print_exc()
        # エラー時は全て非表示
        row_updates = [gr.update(visible=False) for _ in range(8)]
        checkbox_updates = [gr.update(value=False) for _ in range(8)]
        swatch_updates = [gr.update(value="") for _ in range(8)]
        label_updates = [gr.update(value="") for _ in range(8)]
        return [gr.update(visible=False)] + row_updates + checkbox_updates + swatch_updates + label_updates


def apply_selected_colors_to_patterns(*checkbox_values):
    """選択された色を使って4配色パターンを生成"""
    global extracted_colors
    
    print(f"🔍 apply_selected_colors_to_patterns呼び出し")

    if not extracted_colors:
        print("❌ 抽出された色がありません")
        picker_updates = update_pickers_only(colorizer)
        return [gr.update(), []] + picker_updates + [0, 0, 0]
    
    try:
        # チェックされている色を取得
        selected_colors = []
        for i, is_checked in enumerate(checkbox_values):
            if is_checked and i < len(extracted_colors):
                rgb = extracted_colors[i]['rgb']
                hex_color = ColorUtils.rgb_to_hex(rgb)
                selected_colors.append(hex_color)
                print(f"  選択色{i+1}: {hex_color}")
        
        if not selected_colors:
            print("❌ 色が選択されていません")
            picker_updates = update_pickers_only(colorizer)
            return [gr.update(), []] + picker_updates + [0, 0, 0]
        
        print(f"🎨 選択色でパターン生成: {selected_colors}")
        
        # ★ ui_generators の新しいメソッドを呼び出し ★
        return pattern_generator.apply_selected_colors_patterns(selected_colors)
        
    except Exception as e:
        print(f"❌ パターン生成エラー: {e}")
        import traceback
        traceback.print_exc()
        picker_updates = update_pickers_only(colorizer)
        return [gr.update(), []] + picker_updates + [0, 0, 0]

def adjust_color_brightness(hex_color, factor):
    """色の明度を調整"""
    try:
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
        h, s, v = ColorUtils.rgb_to_hsv(rgb)
        
        # 明度を調整（0-100の範囲内で）
        v = min(100, max(0, v * factor))
        
        # HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(h/360, s/100, v/100)
        rgb_adjusted = (int(r*255), int(g*255), int(b*255))
        
        return ColorUtils.rgb_to_hex(rgb_adjusted)
    except:
        return hex_color


def adjust_color_saturation(hex_color, factor):
    """色の彩度を調整"""
    try:
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
        h, s, v = ColorUtils.rgb_to_hsv(rgb)
        
        # 彩度を調整（0-100の範囲内で）
        s = min(100, max(0, s * factor))
        
        # HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(h/360, s/100, v/100)
        rgb_adjusted = (int(r*255), int(g*255), int(b*255))
        
        return ColorUtils.rgb_to_hex(rgb_adjusted)
    except:
        return hex_color


def shift_color_hue(hex_color, hue_shift):
    """色相をシフトした色を返す"""
    try:
        # HEX to RGB
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
        
        # RGB to HSV
        h, s, v = ColorUtils.rgb_to_hsv(rgb)
        
        # 色相をシフト
        h = (h + hue_shift) % 360
        
        # HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(h/360, s/100, v/100)
        rgb_shifted = (int(r*255), int(g*255), int(b*255))
        
        # RGB to HEX
        return ColorUtils.rgb_to_hex(rgb_shifted)
    except:
        return hex_color  # エラー時は元の色を返す


def create_ui() -> gr.Blocks:
    """Gradio UIを作成"""
    
    custom_css = """
    #edit-panel { 
        background: transparent; 
        border: none; 
        padding: 10px; 
    }
    #pattern_gallery {
        scrollbar-width: thin;
        scrollbar-color: #333333 #1a1a1a;
    }
    #pattern_gallery::-webkit-scrollbar {
        width: 8px;
    }
    #pattern_gallery::-webkit-scrollbar-track {
        background: #1a1a1a;
    }
    #pattern_gallery::-webkit-scrollbar-thumb {
        background: #333333;
        border-radius: 4px;
    }
    #pattern_gallery::-webkit-scrollbar-thumb:hover {
        background: #444444;
    }
    #pattern_gallery .gallery {
        scrollbar-width: thin;
        scrollbar-color: #333333 #1a1a1a;
    }
    #pattern_gallery .gallery::-webkit-scrollbar {
        width: 8px;
    }
    #pattern_gallery .gallery::-webkit-scrollbar-track {
        background: #1a1a1a;
    }
    #pattern_gallery .gallery::-webkit-scrollbar-thumb {
        background: #333333;
        border-radius: 4px;
    }
    #pattern_gallery .gallery::-webkit-scrollbar-thumb:hover {
        background: #444444;
    }
    #color_extractor_area {
        /* border関連を全て削除 */
    }
    """
    
    with gr.Blocks(css=custom_css, title=f"MS Color Generator {VERSION}") as demo:
        if colorizer.num_layers == 0:
            _create_no_layers_ui()
            return demo
        
        # メインUI構築
        main_image, pickers, layer_group_radio, color_inherit_radio, save_btn, downloader = _create_main_ui_section()
        pattern_gallery, backup_btn, restart_btn = _create_pattern_gallery_section()
        
        # パラメータ制御部分を横並びで配置
        with gr.Row():
            with gr.Column(scale=2):
                parameter_controls = _create_parameter_controls()
            with gr.Column(scale=2):
                hsv_controls = _create_hsv_controls()
            with gr.Column(scale=3):
                color_extractor_components = _create_color_extractor_section()
        
        
        
        # イベント登録
        _register_events(
            main_image, pattern_gallery, layer_group_radio, color_inherit_radio,
            save_btn, backup_btn, restart_btn, pickers, 
            parameter_controls, hsv_controls, downloader, color_extractor_components
        )
        
        # 初期表示
        demo.load(fn=update_colors, outputs=[main_image, pattern_gallery] + pickers)
    
    return demo


def _create_no_layers_ui():
    """レイヤーファイルがない場合のUI"""
    gr.Markdown("### layerX.png ファイルが見つかりませんでした。")
    gr.Markdown(f"**{LAYER_DIR}** フォルダ内に layer1.png, layer2.png... のファイルを配置してください。")


def _create_main_ui_section():
    """メインUI部分を作成"""
    layout = UI_LAYOUT
    
    with gr.Group():
        with gr.Row():
            # 左: メイン画像エリア（configから寸法取得）
            with gr.Column(scale=layout["main_content_scale"]):
                main_image = gr.Image(
                    type="pil", 
                    label="メイン表示", 
                    interactive=True,
                    height=layout["main_image_height"]
                )
            
            # 右: カラーピッカー＋レイヤー編集（configから寸法取得）
            with gr.Column(scale=layout["picker_control_scale"]):
                # カラーピッカー
                gr.Markdown("### レイヤーカラー")
                pickers = create_initial_pickers(colorizer)
                
                # レイヤー編集パネル
                gr.Markdown("### 選択レイヤーのグループ変更")
                with gr.Row():
                    layer_group_radio = gr.Radio(
                        choices=colorizer.get_available_groups() + ["GROUP追加"],
                        label="グループ変更",
                        value=None
                    )
                    
                    # UI_CHOICESから選択肢を取得
                    color_inherit_radio = gr.Radio(
                        choices=UI_CHOICES["new_group_colors"],
                        label="新GROUP色",
                        value=UI_CHOICES["new_group_colors"][0]  # "ヨモギ色"
                    )
                
                # メイン画像保存ボタン（configからサイズ取得）
                save_btn = gr.Button(
                    "メイン表示を保存", 
                    variant="primary", 
                    size=layout["large_button_size"]
                )
                downloader = gr.File(label="ダウンロード", visible=False)
    
    return main_image, pickers, layer_group_radio, color_inherit_radio, save_btn, downloader


def _create_pattern_gallery_section():
    """パターンギャラリー部分を作成"""
    layout = UI_LAYOUT
    
    with gr.Row():
        # 左側: 4パターン比較ギャラリー
        with gr.Column(scale=1):
            pattern_gallery = gr.Gallery(
                label="4パターン比較",
                show_label=True,
                elem_id="pattern_gallery",
                columns=layout["gallery_columns"],
                rows=layout["gallery_rows"],
                height=layout["pattern_gallery_height"],
                object_fit=layout["gallery_object_fit"],
                allow_preview=False
            )
        
        # 右側: 操作ボタン + アプリ情報
        with gr.Column(scale=1):
            # 操作ボタンを横並びに配置
            if not IS_HUGGING_FACE_SPACES:
                with gr.Row():
                    backup_btn = gr.Button(
                        "コードをバックアップ", 
                        variant="secondary", 
                        size=layout["small_button_size"]
                    )
                    restart_btn = gr.Button(
                        "再起動", 
                        variant="secondary", 
                        size=layout["small_button_size"]
                    )
            else:
                # 開発者ボタンは非表示（ダミーを返す）
                backup_btn = gr.Button("バックアップ", visible=False)
                restart_btn = gr.Button("再起動", visible=False)
            
            # アプリ情報（ボタンの下に配置）
            gr.Markdown(f"**MS Color Generator {VERSION}**")
            gr.Markdown(f"*{colorizer.num_layers}個のレイヤー読み込み完了*")
    
    return pattern_gallery, backup_btn, restart_btn


def _create_parameter_controls():
    """パラメータ制御部分を作成"""
    layout = UI_LAYOUT
    preset_names = UI_CHOICES["preset_names"]
    
    # 左カラム: プリセット選択とパラメータ調整
    with gr.Column(scale=layout["picker_control_scale"]):
        # プリセット選択とパラメータ調整（統合グループ）
        with gr.Group():
            gr.Markdown("### パラメータ調整")
            
            # プリセット選択（configから取得）
            with gr.Row():
                preset_buttons = []
                for i in range(0, 3):  # 最初の3個
                    if i < len(preset_names):
                        btn = gr.Button(
                            preset_names[i], 
                            variant="secondary", 
                            size=layout["small_button_size"]
                        )
                        preset_buttons.append(btn)
            
            with gr.Row():
                for i in range(3, 6):  # 次の3個
                    if i < len(preset_names):
                        btn = gr.Button(
                            preset_names[i], 
                            variant="secondary", 
                            size=layout["small_button_size"]
                        )
                        preset_buttons.append(btn)
            
            # パラメータ調整スライダー（configから設定取得）
            sliders = []
            
            # 彩度スライダー
            with gr.Row():
                sat_base_config = get_slider_config("saturation_base")
                saturation_base = gr.Slider(
                    sat_base_config["min"], sat_base_config["max"], 
                    value=sat_base_config["value"], step=sat_base_config["step"], 
                    label=sat_base_config["label"]
                )
                sliders.append(saturation_base)
                
                sat_range_config = get_slider_config("saturation_range")
                saturation_range = gr.Slider(
                    sat_range_config["min"], sat_range_config["max"], 
                    value=sat_range_config["value"], step=sat_range_config["step"], 
                    label=sat_range_config["label"]
                )
                sliders.append(saturation_range)
            
            # 明度スライダー
            with gr.Row():
                bright_base_config = get_slider_config("brightness_base")
                brightness_base = gr.Slider(
                    bright_base_config["min"], bright_base_config["max"], 
                    value=bright_base_config["value"], step=bright_base_config["step"], 
                    label=bright_base_config["label"]
                )
                sliders.append(brightness_base)
                
                bright_range_config = get_slider_config("brightness_range")
                brightness_range = gr.Slider(
                    bright_range_config["min"], bright_range_config["max"], 
                    value=bright_range_config["value"], step=bright_range_config["step"], 
                    label=bright_range_config["label"]
                )
                sliders.append(brightness_range)
            
            # 色相スライダー
            with gr.Row():
                hue_center_config = get_slider_config("hue_center")
                hue_center = gr.Slider(
                    hue_center_config["min"], hue_center_config["max"], 
                    value=hue_center_config["value"], step=hue_center_config["step"], 
                    label=hue_center_config["label"]
                )
                sliders.append(hue_center)
                
                hue_range_config = get_slider_config("hue_range")
                hue_range = gr.Slider(
                    hue_range_config["min"], hue_range_config["max"], 
                    value=hue_range_config["value"], step=hue_range_config["step"], 
                    label=hue_range_config["label"]
                )
                sliders.append(hue_range)
            
            # その他の設定
            with gr.Row():
                color_count_config = get_slider_config("color_count")
                color_count = gr.Slider(
                    color_count_config["min"], color_count_config["max"], 
                    value=color_count_config["value"], step=color_count_config["step"], 
                    label=color_count_config["label"]
                )
                sliders.append(color_count)
                
                equal_spacing = gr.Checkbox(value=False, label="色相等間隔生成")
                sliders.append(equal_spacing)
            
            with gr.Row():
                min_hue_distance_config = get_slider_config("min_hue_distance")
                min_hue_distance = gr.Slider(
                    min_hue_distance_config["min"], min_hue_distance_config["max"], 
                    value=min_hue_distance_config["value"], step=min_hue_distance_config["step"], 
                    label=min_hue_distance_config["label"]
                )
                sliders.append(min_hue_distance)
                
                generate_btn = gr.Button(
                    "現在のパラメーターで4配色パターン生成", 
                    variant="primary", 
                    size=layout["large_button_size"]
                )
    
    return {
        'preset_buttons': preset_buttons,
        'sliders': sliders,
        'generate_btn': generate_btn
    }


def _create_hsv_controls():
    """HSV制御部分を作成"""
    layout = UI_LAYOUT
    variation_modes = UI_CHOICES["variation_modes"]
    
    # 右カラム: 操作ボタン＋全色一括調整
    with gr.Column(scale=layout["picker_control_scale"]):
        # 全色一括調整とパターン生成（統合グループ）
        with gr.Group():
            gr.Markdown("### 全レイヤー 一括調整")
            
            # HSVシフトスライダー（configから設定取得）
            hsv_sliders = []
            
            with gr.Row():
                hue_shift_config = get_slider_config("hue_shift")
                hue_shift_slider = gr.Slider(
                    hue_shift_config["min"], hue_shift_config["max"], 
                    value=hue_shift_config["value"], step=hue_shift_config["step"], 
                    label=hue_shift_config["label"], 
                    interactive=True
                )
                hsv_sliders.append(hue_shift_slider)
            
            with gr.Row():
                sat_shift_config = get_slider_config("saturation_shift")
                sat_shift_slider = gr.Slider(
                    sat_shift_config["min"], sat_shift_config["max"], 
                    value=sat_shift_config["value"], step=sat_shift_config["step"], 
                    label=sat_shift_config["label"], 
                    interactive=True
                )
                hsv_sliders.append(sat_shift_slider)
            
            with gr.Row():
                val_shift_config = get_slider_config("brightness_shift")
                val_shift_slider = gr.Slider(
                    val_shift_config["min"], val_shift_config["max"], 
                    value=val_shift_config["value"], step=val_shift_config["step"], 
                    label=val_shift_config["label"], 
                    interactive=True
                )
                hsv_sliders.append(val_shift_slider)
            
            # HSV変化パターン生成
            with gr.Row():
                variation_mode_radio = gr.Radio(
                    choices=variation_modes,
                    label="変化モード",
                    value=variation_modes[0]  # "等間隔"
                )
            
            with gr.Row():
                hue_variation_btn = gr.Button(
                    "現在の色の色相違いを4パターン生成", 
                    variant="secondary", 
                    size=layout["small_button_size"]
                )
            
            # 現在の色でパターン生成ボタン
            current_colors_btn = gr.Button(
                "現在の色で4配色パターン生成", 
                variant="primary", 
                size=layout["large_button_size"]
            )
    
    return {
        'sliders': hsv_sliders,
        'variation_mode': variation_mode_radio,
        'buttons': [hue_variation_btn, current_colors_btn]
    }


def _create_color_extractor_section():
    """Color Extractor セクションを作成"""
    with gr.Group(elem_id="color_extractor_area"):
        gr.Markdown("### カラーパレット抽出")
        
        with gr.Row():
            # 左側: 画像アップロード
            with gr.Column(scale=1, min_width=100):
                upload_image = gr.Image(
                    type="pil",
                    label="画像をアップロード",
                    height=300
                )
            
            # 右側: 抽出された色の表示と選択
            with gr.Column(scale=1):
                with gr.Group(visible=False) as color_selection_area:
                    gr.Markdown("#### 使用する色を選択")
                    
                    # 個別色選択行（最大8色まで対応）
                    color_rows = []
                    color_checkboxes = []
                    color_swatches = []
                    color_labels = []
                    
                    for i in range(8):
                        with gr.Row(visible=False) as color_row:
                            # チェックボックス
                            with gr.Column(scale=1, min_width=10):
                                checkbox = gr.Checkbox(
                                    value=True,
                                    label=""
                                )
                            
                            # 色見本（HTMLで色付き四角）
                            with gr.Column(scale=1, min_width=10):
                                color_swatch = gr.HTML(
                                    value=""
                                )
                            
                            # 色情報テキスト（HTMLで直接幅制御）
                            with gr.Column(scale=3, min_width=50):  # scale=2から1に変更、min_width追加
                                color_label = gr.HTML(  # gr.MarkdownからHTMLに変更
                                    value=""
                                )
                            
                            color_rows.append(color_row)
                            color_checkboxes.append(checkbox)
                            color_swatches.append(color_swatch)
                            color_labels.append(color_label)
                    
                    # パターン生成ボタン
                    generate_patterns_btn = gr.Button(
                        "抽出した色で4配色パターンを生成", 
                        variant="primary",
                        size="lg"
                    )
    
    return {
        'upload_image': upload_image,
        'color_selection_area': color_selection_area,
        'color_rows': color_rows,
        'color_checkboxes': color_checkboxes,
        'color_swatches': color_swatches,
        'color_labels': color_labels,
        'generate_patterns_btn': generate_patterns_btn
    }




def _register_events(main_image, pattern_gallery, layer_group_radio, color_inherit_radio,
                    save_btn, backup_btn, restart_btn, pickers, parameter_controls, 
                    hsv_controls, downloader, color_extractor_components):
    """イベントを登録（重複修正版）"""
    
    # Color Extractor イベント登録（一意のapi_name指定）
    color_extractor_components['upload_image'].upload(
        fn=extract_and_display_colors,
        inputs=[color_extractor_components['upload_image']],
        outputs=[
            color_extractor_components['color_selection_area']
        ] + color_extractor_components['color_rows'] + color_extractor_components['color_checkboxes'] + color_extractor_components['color_swatches'] + color_extractor_components['color_labels'],
        api_name="extract_colors_upload"  # 一意のapi_name
    )

    # 画像クリックで色追加（一意のapi_name指定）
    color_extractor_components['upload_image'].select(
        fn=add_color_from_click,
        inputs=[color_extractor_components['upload_image']],
        outputs=(
            color_extractor_components['color_rows'] + 
            color_extractor_components['color_checkboxes'] + 
            color_extractor_components['color_swatches'] + 
            color_extractor_components['color_labels']
        ),
        api_name="add_color_click"  # 一意のapi_name
    )

    # 画像変更時（一意のapi_name指定）
    color_extractor_components['upload_image'].change(
        fn=extract_and_display_colors,
        inputs=[color_extractor_components['upload_image']],
        outputs=[
            color_extractor_components['color_selection_area']
        ] + color_extractor_components['color_rows'] + color_extractor_components['color_checkboxes'] + color_extractor_components['color_swatches'] + color_extractor_components['color_labels'],
        api_name="extract_colors_change"  # 一意のapi_name
    )
    
    # パターン生成ボタン（一意のapi_name指定）
    color_extractor_components['generate_patterns_btn'].click(
        fn=apply_selected_colors_to_patterns,
        inputs=color_extractor_components['color_checkboxes'],
        outputs=[
            main_image,
            pattern_gallery
        ] + pickers + hsv_controls['sliders'],
        show_progress=True,
        api_name="generate_patterns_from_extracted"  # 一意のapi_name
    )
    
    # メイン画像クリック（レイヤー選択用）
    main_image.select(
        fn=ui_handlers.on_click, 
        outputs=[main_image, layer_group_radio],
        api_name="main_image_click"  # 一意のapi_name
    )
    
    # ギャラリー選択
    pattern_gallery.select(
        fn=ui_handlers.on_gallery_select,
        outputs=[main_image] + pickers + hsv_controls['sliders'],
        api_name="gallery_select"  # 一意のapi_name
    )
    
    # ラジオボタン変更で即適用
    layer_group_radio.change(
        fn=ui_handlers.apply_group_change,
        inputs=[layer_group_radio, color_inherit_radio],
        outputs=[main_image] + pickers + [layer_group_radio],
        api_name="group_change"  # 一意のapi_name
    )
    
    # プリセットボタンイベント登録
    _register_preset_events(parameter_controls)
    
    # パラメータ関連イベント登録
    _register_parameter_events(parameter_controls, hsv_controls, main_image, pattern_gallery, pickers)
    
    # カラーピッカーイベント登録
    _register_picker_events(pickers, main_image, hsv_controls)
    
    # HSVシフトイベント登録
    _register_hsv_events(hsv_controls, main_image, pickers)
    
    # その他のボタンイベント登録
    _register_utility_events(save_btn, backup_btn, restart_btn, downloader)


def _register_preset_events(parameter_controls):
    """プリセットボタンのイベントを登録（修正版）"""
    preset_names = UI_CHOICES["preset_names"]
    
    for i, (btn, preset_name) in enumerate(zip(parameter_controls['preset_buttons'], preset_names)):
        btn.click(
            fn=lambda name=preset_name: ui_handlers.set_preset_params(name),
            outputs=parameter_controls['sliders'],
            api_name=f"preset_{i}_{preset_name.replace(' ', '_')}"  # 一意のapi_name
        )


def _register_parameter_events(parameter_controls, hsv_controls, main_image, pattern_gallery, pickers):
    """パラメータ関連のイベントを登録（修正版）"""
    # ランダム生成ボタン
    parameter_controls['generate_btn'].click(
        fn=pattern_generator.apply_custom_colors,
        inputs=parameter_controls['sliders'],
        outputs=[main_image, pattern_gallery] + pickers + hsv_controls['sliders'],
        show_progress=True,
        api_name="generate_custom_colors"  # 一意のapi_name
    )
    
    # HSV変化パターン生成ボタン
    hsv_controls['buttons'][0].click(  # hue_variation_btn
        fn=lambda mode: pattern_generator.generate_hsv_variation_patterns("hue", mode == UI_CHOICES["variation_modes"][1]),
        inputs=[hsv_controls['variation_mode']],
        outputs=[main_image, pattern_gallery] + pickers + hsv_controls['sliders'],
        show_progress=True,
        api_name="generate_hue_variations"  # 一意のapi_name
    )

    # 現在の色でパターン生成ボタン
    hsv_controls['buttons'][1].click(  # current_colors_btn
        fn=pattern_generator.apply_current_colors_patterns,
        outputs=[main_image, pattern_gallery] + pickers + hsv_controls['sliders'],
        show_progress=True,
        api_name="generate_current_patterns"  # 一意のapi_name
    )


def _register_picker_events(pickers, main_image, hsv_controls):
    """カラーピッカーのイベントを登録（修正版）"""
    for i, picker in enumerate(pickers):
        picker.change(
            fn=ui_handlers.create_picker_change_handler(i),
            inputs=[picker],
            outputs=[main_image] + pickers + hsv_controls['sliders'],
            api_name=f"picker_change_{i}"  # 一意のapi_name
        )


def _register_hsv_events(hsv_controls, main_image, pickers):
    """HSVシフトのイベントを登録（修正版）"""
    hsv_handler = ui_handlers.create_hsv_shift_handler()
    
    for i, slider in enumerate(hsv_controls['sliders']):
        slider_names = ['hue_shift', 'sat_shift', 'val_shift']
        slider_name = slider_names[i] if i < len(slider_names) else f'slider_{i}'
        
        slider.change(
            fn=hsv_handler,
            inputs=hsv_controls['sliders'],
            outputs=[main_image] + pickers,
            api_name=f"hsv_{slider_name}"  # 一意のapi_name
        )


def _register_utility_events(save_btn, backup_btn, restart_btn, downloader):
    """ユーティリティボタンのイベントを登録（修正版）"""
    # 保存ボタン
    def save_and_update():
        """環境に応じた保存処理"""
        try:            
            saved_path = do_save(ui_state.current_main_image)
            
            if saved_path:
                if IS_HUGGING_FACE_SPACES:
                    # 🌐 Hugging Face Spaces: ダウンロードリンク表示
                    print(f"✅ [SAVE] ダウンロード準備完了: {saved_path}")
                    return gr.update(value=saved_path, visible=True)
                else:
                    # 💻 ローカル: リンク非表示（従来通り）
                    print(f"✅ [SAVE] ローカル保存完了: {saved_path}")
                    return gr.update(value=None, visible=False)
            else:
                print(f"❌ [SAVE] 保存失敗")
                return gr.update(value=None, visible=False)
                
        except Exception as e:
            print(f"❌ [SAVE] エラー: {e}")
            return gr.update(value=None, visible=False)
    
    save_btn.click(
        fn=save_and_update,
        outputs=downloader
    )
    
    # バックアップボタン
    backup_btn.click(
        fn=backup_files, 
        outputs=backup_btn,
        api_name="backup_files"  # 一意のapi_name
    )
    
    # 再起動ボタン
    from config import RESTART_SETTINGS
    restart_wait = RESTART_SETTINGS["restart_wait_ms"]
    recovery_interval = RESTART_SETTINGS["recovery_check_interval_ms"]
    max_attempts = RESTART_SETTINGS["max_recovery_attempts"]
    
    restart_btn.click(
        fn=restart_server,
        inputs=[],
        outputs=[restart_btn],
        api_name="restart_server",  # 一意のapi_name
        js=f"""() => {{
            setTimeout(() => {{
                console.log('🔄 サーバー再起動確認を開始...');
                let attempts = 0;
                const maxAttempts = {max_attempts};
                
                const checkServer = () => {{
                    fetch(window.location.href, {{ method: 'HEAD' }})
                        .then(response => {{
                            if (response.ok) {{
                                console.log('✅ サーバー復旧: ページをリロード');
                                window.location.reload();
                            }}
                        }})
                        .catch(() => {{
                            attempts++;
                            if (attempts < maxAttempts) {{
                                setTimeout(checkServer, {recovery_interval});
                            }} else {{
                                window.location.reload();
                            }}
                        }});
                }};
                
                checkServer();
            }}, {restart_wait});
        }}"""
    )


def add_color_from_click(image, evt: gr.SelectData):
    """画像クリック時に色を追加
    
    Args:
        image: クリックされた画像
        evt: Gradioクリックイベント
        
    Returns:
        更新されたUI要素のリスト
    """
    global extracted_colors
    
    print(f"🖱️ 画像クリック: 座標({evt.index[0]}, {evt.index[1]})")
    
    if image is None:
        print("❌ 画像がありません")
        return _get_empty_color_updates()
    
    try:
        x, y = evt.index
        
        # クリック位置の色を取得
        if hasattr(image, 'getpixel'):
            rgb = image.getpixel((x, y))
            if len(rgb) >= 3:
                rgb = rgb[:3]  # RGB部分のみ
            else:
                print(f"❌ 無効なピクセル値: {rgb}")
                return _get_empty_color_updates()
        else:
            print("❌ 画像からピクセル取得不可")
            return _get_empty_color_updates()
        
        hex_color = ColorUtils.rgb_to_hex(rgb)
        h, s, v = ColorUtils.rgb_to_hsv(rgb)
        
        print(f"🎨 クリック色取得: {hex_color} (H:{h:.0f}° S:{s:.0f}% V:{v:.0f}%)")
        
        # 重複チェック（色の差が小さい場合は追加しない）
        color_threshold = 10  # RGB値の差の閾値
        is_duplicate = False
        
        for existing_color in extracted_colors:
            existing_rgb = existing_color['rgb']
            color_diff = sum(abs(a - b) for a, b in zip(rgb, existing_rgb))
            if color_diff < color_threshold:
                print(f"🔍 類似色のため追加スキップ: 差={color_diff}")
                is_duplicate = True
                break
        
        if not is_duplicate:
            # 新しい色を追加
            new_color = {
                'rgb': rgb,
                'hex': hex_color,
                'h': h,
                's': s,
                'v': v,
                'index': len(extracted_colors)
            }
            extracted_colors.append(new_color)
            print(f"✅ 新色追加: {hex_color} (総数: {len(extracted_colors)}色)")
        
        # UIを更新
        return _update_color_selection_ui()
        
    except Exception as e:
        print(f"❌ 色追加エラー: {e}")
        import traceback
        traceback.print_exc()
        return _get_empty_color_updates()


def _update_color_selection_ui():
    """色選択UIを更新
    
    Returns:
        更新されたUI要素のリスト
    """
    global extracted_colors
    
    # 8行の更新データを作成
    row_updates = []
    checkbox_updates = []
    swatch_updates = []
    label_updates = []
    
    for i in range(8):
        if i < len(extracted_colors):
            color_info = extracted_colors[i]
            hex_color = color_info['hex']
            h = color_info['h']
            s = color_info['s']
            v = color_info['v']
            
            # 行を表示
            row_updates.append(gr.update(visible=True))
            
            # チェックボックス（新しく追加された色はデフォルトでチェック）
            checkbox_updates.append(gr.update(value=True))
            
            # 色見本HTML
            swatch_html = f"""
            <div style="
                width: 50px; 
                height: 30px; 
                background-color: {hex_color}; 
                border: 1px solid #ddd; 
                border-radius: 4px;
                margin: 2px;
            "></div>
            """
            swatch_updates.append(gr.update(value=swatch_html))
            
            # テキストラベル
            label_text = f"`{hex_color}` (H:{h:.0f}° S:{s:.0f}% V:{v:.0f}%)"
            label_updates.append(gr.update(value=label_text))
        else:
            # 色がない場合は非表示
            row_updates.append(gr.update(visible=False))
            checkbox_updates.append(gr.update(value=False))
            swatch_updates.append(gr.update(value=""))
            label_updates.append(gr.update(value=""))
    
    print(f"🔄 UI更新: {len(extracted_colors)}色を表示")
    
    # 戻り値: 8行 + 8チェックボックス + 8色見本 + 8ラベル
    return row_updates + checkbox_updates + swatch_updates + label_updates


def _get_empty_color_updates():
    """空のUI更新データを取得
    
    Returns:
        空のUI更新データのリスト
    """
    row_updates = [gr.update(visible=False) for _ in range(8)]
    checkbox_updates = [gr.update(value=False) for _ in range(8)]
    swatch_updates = [gr.update(value="") for _ in range(8)]
    label_updates = [gr.update(value="") for _ in range(8)]
    
    return row_updates + checkbox_updates + swatch_updates + label_updates