"""
MS Color Generator - レイヤー管理クラス（config統合版）
"""

import os
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import numpy as np
from PIL import Image

from config import (
    MAX_LAYERS, TARGET_COLOR, DEFAULT_GROUP_COLOR, 
    SAVE_DIR, LAYER_DIR, CONFIG_FILE, IMAGE_SETTINGS, 
    SYSTEM_SETTINGS, COLOR_SETTINGS
)
from models import ColorGenerationParams
from presets import COLOR_PRESETS
from color_utils import generate_colors_from_params, generate_four_patterns


class LayerColorizer:
    """レイヤー着色管理クラス"""
    
    def __init__(self):
        """LayerColorizerの初期化"""
        # レイヤーファイル読み込み
        self.layer_files = self._load_layer_files()
        self.num_layers = len(self.layer_files)
        
        # 画像キャッシュ初期化
        self._image_cache: Dict[str, Image.Image] = {}
        self._load_images_with_cache()
        
        # 状態初期化
        self.current_composite: Optional[Image.Image] = None
        self.current_max_group = 0
        
        # グループ設定初期化
        self.layers = [SYSTEM_SETTINGS["default_group_name"]] * self.num_layers
        self.group_colors = {SYSTEM_SETTINGS["default_group_name"]: DEFAULT_GROUP_COLOR}
        
        # 設定ファイル読み込み
        self._load_grouping_config()
    
    def _load_layer_files(self) -> List[str]:
        """layerXファイルを読み込み
        
        Returns:
            レイヤーファイルパスのリスト
        """
        layer_pattern = re.compile(
            IMAGE_SETTINGS["layer_file_pattern"], 
            IMAGE_SETTINGS["layer_file_flags"]
        )
        layer_files = {}
        
        # layerフォルダが存在しない場合は作成
        os.makedirs(LAYER_DIR, exist_ok=True)
        
        # layerフォルダ内のファイルをチェック
        if os.path.exists(LAYER_DIR):
            for fname in os.listdir(LAYER_DIR):
                m = layer_pattern.fullmatch(fname)
                if m:
                    idx = int(m.group(1))
                    if 1 <= idx <= MAX_LAYERS:
                        layer_files[idx] = os.path.join(LAYER_DIR, fname)
        
        return [layer_files[i] for i in sorted(layer_files)]
    
    def _load_images_with_cache(self):
        """レイヤー画像をキャッシュ付きで読み込み"""
        self.orig_images = []
        
        for i, fname in enumerate(self.layer_files):
            try:
                if fname in self._image_cache:
                    print(f"🔄 [CACHE] キャッシュから読み込み: {fname}")
                    self.orig_images.append(self._image_cache[fname])
                else:
                    print(f"📁 [LOAD] ファイルから読み込み: {fname}")
                    img = Image.open(fname).convert(IMAGE_SETTINGS["default_image_mode"])
                    self._image_cache[fname] = img
                    self.orig_images.append(img)
                    
            except FileNotFoundError:
                print(f"❌ [ERROR] ファイルが見つかりません: {fname}")
                # configからダミー画像設定を取得
                dummy_size = IMAGE_SETTINGS["dummy_image_size"]
                dummy_color = IMAGE_SETTINGS["dummy_image_color"]
                dummy_img = Image.new(IMAGE_SETTINGS["default_image_mode"], dummy_size, dummy_color)
                self.orig_images.append(dummy_img)
            except Exception as e:
                print(f"❌ [ERROR] 画像読み込みエラー {fname}: {e}")
                # configからダミー画像設定を取得
                dummy_size = IMAGE_SETTINGS["dummy_image_size"]
                dummy_color = IMAGE_SETTINGS["dummy_image_color"]
                dummy_img = Image.new(IMAGE_SETTINGS["default_image_mode"], dummy_size, dummy_color)
                self.orig_images.append(dummy_img)

    def _load_grouping_config(self):
        """grouping.txtからグループ設定を読み込み（エラーハンドリング強化）"""
        try:
            if not os.path.exists(CONFIG_FILE):
                print(f"⚠️ [CONFIG] {CONFIG_FILE} が見つかりません。デフォルト設定を使用します。")
                self.current_max_group = 3
                return
                
            # configからエンコーディングを取得
            encoding = IMAGE_SETTINGS["file_encoding"]
            with open(CONFIG_FILE, encoding=encoding) as f:
                lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                
            if not lines:
                print(f"⚠️ [CONFIG] {CONFIG_FILE} が空です。デフォルト設定を使用します。")
                self.current_max_group = 3
                return
                
            self.current_max_group = len(lines)
            valid_groups = 0

            for i, line in enumerate(lines):
                try:
                    if ":" not in line:
                        print(f"⚠️ [CONFIG] 無効な行をスキップ: {line}")
                        continue
                        
                    group_id = f"GROUP{i+1}"
                    indices_part, color_part = line.split(":", 1)
                    
                    # インデックス部分の処理
                    indices_str = indices_part.strip()
                    if not indices_str:
                        print(f"⚠️ [CONFIG] {group_id}: レイヤーインデックスが空です")
                        continue
                        
                    indices = []
                    for x in indices_str.split(","):
                        x = x.strip()
                        if x.isdigit():
                            idx = int(x)
                            if 1 <= idx <= self.num_layers:
                                indices.append(idx)
                            else:
                                print(f"⚠️ [CONFIG] {group_id}: 無効なレイヤー番号 {idx} (範囲: 1-{self.num_layers})")
                        else:
                            print(f"⚠️ [CONFIG] {group_id}: 無効なレイヤー番号 '{x}'")
                    
                    if not indices:
                        print(f"⚠️ [CONFIG] {group_id}: 有効なレイヤーがありません")
                        continue
                    
                    # 色部分の処理
                    color = color_part.strip()
                    if not color:
                        print(f"⚠️ [CONFIG] {group_id}: 色が指定されていません。デフォルト色を使用")
                        color = DEFAULT_GROUP_COLOR
                    elif not color.startswith("#"):
                        if len(color) == 6 and all(c in '0123456789abcdefABCDEF' for c in color):
                            color = "#" + color
                        else:
                            print(f"⚠️ [CONFIG] {group_id}: 無効な色形式 '{color}'. デフォルト色を使用")
                            color = DEFAULT_GROUP_COLOR
                    else:
                        # #で始まる場合の検証
                        if len(color) != 7 or not all(c in '0123456789abcdefABCDEF' for c in color[1:]):
                            print(f"⚠️ [CONFIG] {group_id}: 無効な色形式 '{color}'. デフォルト色を使用")
                            color = DEFAULT_GROUP_COLOR
                    
                    # 設定を適用
                    self.group_colors[group_id] = color
                    for idx in indices:
                        self.layers[idx - 1] = group_id
                    
                    valid_groups += 1
                    print(f"✅ [CONFIG] {group_id}: レイヤー{indices}, 色{color}")
                    
                except Exception as e:
                    print(f"❌ [CONFIG] {group_id} 設定エラー: {e}")
                    continue
            
            if valid_groups == 0:
                print("⚠️ [CONFIG] 有効なグループ設定がありません。デフォルト設定を使用します。")
                self.current_max_group = 3
            else:
                print(f"✅ [CONFIG] {valid_groups}個のグループを読み込みました")
                
        except FileNotFoundError:
            print(f"⚠️ [CONFIG] {CONFIG_FILE} ファイルが見つかりません")
            self.current_max_group = 3
        except PermissionError:
            print(f"❌ [CONFIG] {CONFIG_FILE} の読み込み権限がありません")
            self.current_max_group = 3
        except UnicodeDecodeError:
            print(f"❌ [CONFIG] {CONFIG_FILE} の文字エンコーディングエラー")
            self.current_max_group = 3
        except Exception as e:
            print(f"❌ [CONFIG] {CONFIG_FILE} 読み込み中に予期しないエラー: {e}")
            self.current_max_group = 3

    def get_layer_color(self, layer_index: int) -> str:
        """レイヤーの色を取得
        
        Args:
            layer_index: レイヤーインデックス
            
        Returns:
            色コード
        """
        if 0 <= layer_index < len(self.layers):
            group_name = self.layers[layer_index]
            return self.group_colors.get(group_name, DEFAULT_GROUP_COLOR)
        return DEFAULT_GROUP_COLOR

    def get_group_layers(self, group_name: str) -> List[int]:
        """グループに属するレイヤーインデックスを取得
        
        Args:
            group_name: グループ名
            
        Returns:
            レイヤーインデックスのリスト
        """
        return [i for i, g in enumerate(self.layers) if g == group_name]

    def add_new_group(self) -> str:
        """新しいグループを追加
        
        Returns:
            新しいグループ名
        """
        self.current_max_group += 1
        # configからグループ名フォーマットを取得
        group_format = SYSTEM_SETTINGS["group_name_format"]
        new_group = group_format.format(i=self.current_max_group)
        self.group_colors[new_group] = DEFAULT_GROUP_COLOR
        return new_group

    def get_available_groups(self) -> List[str]:
        """利用可能なグループリストを取得
        
        Returns:
            グループ名のリスト
        """
        return [f"GROUP{i}" for i in range(1, self.current_max_group + 1)]

    def update_layer_group(self, layer_index: int, new_group: str):
        """レイヤーのグループを更新
        
        Args:
            layer_index: レイヤーインデックス
            new_group: 新しいグループ名
        """
        if 0 <= layer_index < self.num_layers:
            self.layers[layer_index] = new_group

    def sync_colors_by_group(self, color_values: List[str], group_assignments: List[str]) -> List[str]:
        """グループ内で色を同期
        
        Args:
            color_values: 色のリスト
            group_assignments: グループ割り当てのリスト
            
        Returns:
            同期された色のリスト
        """
        group_map = {}
        for idx, g in enumerate(group_assignments):
            group_map.setdefault(g, []).append(idx)
        
        adjusted_colors = list(color_values)
        for indices in group_map.values():
            if indices:
                indices.sort()
                ref_color = color_values[indices[0]]
                for idx in indices:
                    adjusted_colors[idx] = ref_color
        return adjusted_colors

    def get_sorted_group_data(self, groups: List[str]) -> List[Tuple[str, List[int]]]:
        """グループ順でソートされたグループデータを取得
        
        Args:
            groups: グループのリスト
            
        Returns:
            ソートされた(グループ名, レイヤーインデックスリスト)のタプルリスト
        """
        group_map = {}
        for idx, group in enumerate(groups):
            group_map.setdefault(group, []).append(idx)
        
        # グループをソート（GROUP1, GROUP2, GROUP3...の順）
        sorted_groups = sorted(group_map.items(), 
                              key=lambda x: (x[0] == "GROUP追加", int(x[0][5:]) if x[0].startswith("GROUP") and x[0][5:].isdigit() else 9999))
        
        return sorted_groups

    def apply_random_colors_with_params(self, params: ColorGenerationParams) -> List[List[str]]:
        """パラメータベースでランダムカラーを適用
        
        Args:
            params: 色生成パラメータ
            
        Returns:
            4つのパターンの色配列リスト
        """
        print(f"🔍 [DEBUG] パラメータベース色生成開始")
        
        # 色を動的生成
        generated_colors = generate_colors_from_params(params)
        print(f"🔍 [DEBUG] 生成色: {generated_colors}")
        
        # 使用中のグループを取得（configから）
        default_group = SYSTEM_SETTINGS["default_group_name"]
        used_groups = set(group for group in self.layers if group != default_group)
        used_groups_list = sorted(used_groups)
        print(f"🔍 [DEBUG] 使用中グループ: {used_groups_list}")
        
        # 必要な色数を確認
        needed_colors = len(used_groups_list)
        if needed_colors > len(generated_colors):
            print(f"⚠️ [DEBUG] 不足している色数: 必要{needed_colors}色、生成{len(generated_colors)}色")
            # 不足分は色を繰り返して補う
            while len(generated_colors) < needed_colors:
                generated_colors.extend(generated_colors)
            generated_colors = generated_colors[:needed_colors]
        
        # 4パターン生成
        pattern_compositions = generate_four_patterns(generated_colors[:needed_colors], used_groups_list)
        
        # 最初のパターンを現在の設定として適用
        first_pattern = pattern_compositions[0]
        for group_name, color in zip(used_groups_list, first_pattern):
            self.group_colors[group_name] = color
            
        # 合成画像を更新
        print(f"🔍 [DEBUG] 合成画像更新開始")
        self.current_composite = self.compose_layers()
        print(f"🔍 [DEBUG] 合成画像更新完了")
        
        return pattern_compositions

    def apply_random_colors(self, preset_name: str = "ダル") -> List[List[str]]:
        """プリセット名でランダムカラーを適用（後方互換性）
        
        Args:
            preset_name: プリセット名
            
        Returns:
            4つのパターンの色配列リスト
        """
        if preset_name in COLOR_PRESETS:
            params = COLOR_PRESETS[preset_name]
            return self.apply_random_colors_with_params(params)
        else:
            # フォールバック: ダルプリセット
            return self.apply_random_colors_with_params(COLOR_PRESETS["ダル"])

    def compose_layers_with_colors(self, colors: List[str]) -> Image.Image:
        """指定された色リストでレイヤーを合成（エラーハンドリング強化）
        
        Args:
            colors: 色のリスト
            
        Returns:
            合成された画像
        """
        try:
            # 使用中のグループを取得（configから）
            default_group = SYSTEM_SETTINGS["default_group_name"]
            used_groups = set(group for group in self.layers if group != default_group)
            used_groups_list = sorted(used_groups)
            
            # 色をグループに割り当て
            color_assignment = {}
            for i, group in enumerate(used_groups_list):
                if i < len(colors):
                    color_assignment[group] = colors[i]
                else:
                    color_assignment[group] = DEFAULT_GROUP_COLOR
            
            # 各レイヤーの色を決定
            layer_colors = []
            for layer_group in self.layers:
                layer_colors.append(color_assignment.get(layer_group, DEFAULT_GROUP_COLOR))
            
            # 合成処理
            base = None
            for i, (fname, col) in enumerate(zip(self.layer_files, layer_colors)):
                try:
                    # キャッシュから画像を取得
                    if fname in self._image_cache:
                        layer = self._image_cache[fname].copy()
                    else:
                        layer = Image.open(fname).convert(IMAGE_SETTINGS["default_image_mode"])
                        self._image_cache[fname] = layer.copy()
                    
                    rgb = self.hex_to_rgb(col)
                    colored = self.replace_color(layer, rgb)
                    base = colored if base is None else self.multiply_rgba(base, colored)
                    
                except Exception as e:
                    print(f"❌ [ERROR] レイヤー{i+1}合成エラー: {e}")
                    continue
            
            if base is None:
                print("⚠️ [WARNING] 合成画像がありません。空の画像を作成します")
                dummy_size = IMAGE_SETTINGS["dummy_image_size"]
                dummy_color = IMAGE_SETTINGS["dummy_image_color"]
                base = Image.new(IMAGE_SETTINGS["default_image_mode"], dummy_size, dummy_color)
                
            return base
            
        except Exception as e:
            print(f"❌ [ERROR] compose_layers_with_colors 致命的エラー: {e}")
            dummy_size = IMAGE_SETTINGS["dummy_image_size"]
            dummy_color = IMAGE_SETTINGS["dummy_image_color"]
            return Image.new(IMAGE_SETTINGS["default_image_mode"], dummy_size, dummy_color)

    def compose_layers(self, colors: Optional[List[str]] = None) -> Image.Image:
        """レイヤーを合成
        
        Args:
            colors: 色のリスト（Noneの場合は現在の色を使用）
            
        Returns:
            合成された画像
        """
        if colors is None:
            colors = [self.get_layer_color(i) for i in range(self.num_layers)]
            
        base = None
        for fname, col in zip(self.layer_files, colors):
            try:
                layer = Image.open(fname).convert(IMAGE_SETTINGS["default_image_mode"])
                rgb = self.hex_to_rgb(col)
                colored = self.replace_color(layer, rgb)
                base = colored if base is None else self.multiply_rgba(base, colored)
            except Exception as e:
                print(f"❌ [ERROR] レイヤー合成エラー: {e}")
                continue
        
        if base is None:
            dummy_size = IMAGE_SETTINGS["dummy_image_size"]
            dummy_color = IMAGE_SETTINGS["dummy_image_color"]
            base = Image.new(IMAGE_SETTINGS["default_image_mode"], dummy_size, dummy_color)
        return base

    def clear_image_cache(self):
        """画像キャッシュをクリア（メモリ節約用）"""
        self._image_cache.clear()
        print("🧹 [CACHE] 画像キャッシュをクリアしました")

    @staticmethod
    def hex_to_rgb(color_str) -> Tuple[int, int, int]:
        """16進数カラーコードをRGBに変換
        
        Args:
            color_str: 色の文字列
            
        Returns:
            RGB値のタプル
        """
        if isinstance(color_str, str):
            # 16進数カラーコードの場合
            if color_str.startswith("#"):
                h = color_str.lstrip("#")
                if len(h) == 6:  # 6桁の16進数かチェック
                    try:
                        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                    except ValueError:
                        # configからデフォルトRGB値を取得
                        return COLOR_SETTINGS["default_rgb_fallback"]
                else:
                    return COLOR_SETTINGS["default_rgb_fallback"]
            
            # rgb()形式の場合
            if color_str.startswith("rgb"):
                try:
                    inside = color_str[color_str.find("(")+1:-1]
                    parts = [int(float(v.strip())) for v in inside.split(",")[:3]]
                    return tuple(parts)
                except (ValueError, IndexError):
                    return COLOR_SETTINGS["default_rgb_fallback"]
            
            # その他の文字列（色名など）の場合
            return COLOR_SETTINGS["default_rgb_fallback"]
        
        # tupleの場合はそのまま返す
        if isinstance(color_str, (tuple, list)) and len(color_str) >= 3:
            return tuple(color_str[:3])
        
        # その他の場合はデフォルト色
        return COLOR_SETTINGS["default_rgb_fallback"]

    @staticmethod
    def replace_color(img: Image.Image, new_rgb: Tuple[int, int, int]) -> Image.Image:
        """ターゲット色を新しい色に置換
        
        Args:
            img: 処理対象画像
            new_rgb: 新しいRGB値
            
        Returns:
            色が置換された画像
        """
        img = img.convert("RGBA")
        data = np.array(img)
        r, g, b, _ = data.T
        mask = (r == TARGET_COLOR[0]) & (g == TARGET_COLOR[1]) & (b == TARGET_COLOR[2])
        data[..., :3][mask.T] = new_rgb
        return Image.fromarray(data)

    @staticmethod
    def multiply_rgba(img_a: Image.Image, img_b: Image.Image) -> Image.Image:
        """RGBA画像の乗算合成
        
        Args:
            img_a: 画像A
            img_b: 画像B
            
        Returns:
            乗算合成された画像
        """
        a_arr = np.asarray(img_a.convert("RGBA"), dtype=np.float32) / 255.0
        b_arr = np.asarray(img_b.convert("RGBA"), dtype=np.float32) / 255.0
        rgb = a_arr[..., :3] * b_arr[..., :3]
        alpha = np.maximum(a_arr[..., 3], b_arr[..., 3])[..., None]
        out = np.concatenate([rgb, alpha], axis=-1)
        out = (out * 255).clip(0, 255).astype(np.uint8)
        return Image.fromarray(out, "RGBA")

    @staticmethod
    def timestamp_filename(prefix: str) -> str:
        """タイムスタンプ付きファイル名を生成
        
        Args:
            prefix: ファイル名のプレフィックス
            
        Returns:
            タイムスタンプ付きファイルパス
        """
        # 保存フォルダが存在しない場合は作成
        os.makedirs(SAVE_DIR, exist_ok=True)
        timestamp_format = SYSTEM_SETTINGS["timestamp_format"]
        ts = datetime.now().strftime(timestamp_format)
        return os.path.join(SAVE_DIR, f"{prefix}_{ts}.png")