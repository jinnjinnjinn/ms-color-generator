"""
MS Color Generator - 色関連ユーティリティ（config統合版）
"""

import random
import colorsys
import itertools
from typing import List, Tuple, Optional

from models import ColorGenerationParams
from config import COLOR_SETTINGS, SYSTEM_SETTINGS


def hsv_to_hex(h: float, s: float, v: float) -> str:
    """HSV値を16進数カラーコードに変換
    
    Args:
        h: 色相 (0-360度)
        s: 彩度 (0-1)
        v: 明度 (0-1)
        
    Returns:
        16進数カラーコード (#rrggbb)
    """
    try:
        # HSV → RGB変換
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
        
        # RGB値を0-255の整数に変換
        r_int = max(0, min(255, int(r * 255)))
        g_int = max(0, min(255, int(g * 255)))
        b_int = max(0, min(255, int(b * 255)))
        
        # 16進数文字列に変換
        return f"#{r_int:02x}{g_int:02x}{b_int:02x}"
    except Exception as e:
        print(f"❌ [COLOR_UTILS] HSV→HEX変換エラー: {e}")
        # configからフォールバック色を取得
        return COLOR_SETTINGS["black_fallback"]


def hex_to_hsv(hex_color: str) -> Tuple[float, float, float]:
    """16進数カラーコードをHSV値に変換
    
    Args:
        hex_color: 16進数カラーコード (#rrggbb または rrggbb)
        
    Returns:
        (色相[度], 彩度[%], 明度[%])のタプル
    """
    if not hex_color or not isinstance(hex_color, str):
        return (0.0, 0.0, 0.0)
    
    # #を除去
    hex_color = hex_color.lstrip('#')
    
    if len(hex_color) != 6:
        return (0.0, 0.0, 0.0)
    
    try:
        # RGB値を取得
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        # HSV値に変換
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        
        # 度数とパーセンテージに変換（configから精度取得）
        hue_precision = COLOR_SETTINGS["hue_display_precision"]
        sat_precision = COLOR_SETTINGS["saturation_display_precision"]
        bright_precision = COLOR_SETTINGS["brightness_display_precision"]
        
        h_deg = round(h * 360.0, hue_precision)
        s_percent = round(s * 100.0, sat_precision)
        v_percent = round(v * 100.0, bright_precision)
        
        return (h_deg, s_percent, v_percent)
    except (ValueError, TypeError) as e:
        print(f"❌ [COLOR_UTILS] HEX→HSV変換エラー ({hex_color}): {e}")
        return (0.0, 0.0, 0.0)


def calculate_hue_distance(hue1: float, hue2: float) -> float:
    """2つの色相間の最短距離を計算（0-180度）
    
    Args:
        hue1: 色相1 (度)
        hue2: 色相2 (度)
        
    Returns:
        最短距離 (0-180度)
    """
    try:
        diff = abs(hue1 - hue2)
        return min(diff, 360 - diff)
    except (TypeError, ValueError):
        return 0.0


def generate_colors_from_params(params: ColorGenerationParams) -> List[str]:
    """パラメータに基づいて色を動的生成
    
    Args:
        params: 色生成パラメータ
        
    Returns:
        生成された色のリスト (16進数カラーコード)
    """
    colors = []
    
    try:
        if params.equal_hue_spacing:
            # 等間隔生成モード
            print(f"🔍 [DEBUG] 等間隔生成モード: {params.color_count}色を等間隔で生成")
            
            # 色相範囲を計算
            hue_start = params.hue_center - params.hue_range
            hue_end = params.hue_center + params.hue_range
            total_range = hue_end - hue_start
            
            if params.color_count == 1:
                # 1色の場合は中心色相を使用
                hues = [params.hue_center]
            elif total_range >= 360:
                # 全色相範囲（360度以上）の場合は特別処理
                step = 360.0 / params.color_count
                hues = [i * step for i in range(params.color_count)]
                print(f"🔍 [DEBUG] 全色相範囲: step={step:.1f}°")
            else:
                # 部分的な色相範囲の場合
                step = total_range / max(1, params.color_count - 1)
                hues = [hue_start + i * step for i in range(params.color_count)]
            
            # 色相を0-360度の範囲に正規化
            hues = [h % 360 for h in hues]
            
            # 等間隔で生成した色相をランダムに並び替え
            random.shuffle(hues)
            
            # 表示精度でフォーマット（configから取得）
            hue_precision = COLOR_SETTINGS["hue_display_precision"]
            print(f"🔍 [DEBUG] 等間隔色相（シャッフル後）: {[f'{h:.{hue_precision}f}°' for h in hues]}")
            
            for h in hues:
                # 彩度と明度はランダム生成
                s_percent = random.uniform(
                    max(0, params.saturation_base - params.saturation_range),
                    min(100, params.saturation_base + params.saturation_range)
                )
                s = s_percent / 100.0
                
                v_percent = random.uniform(
                    max(0, params.brightness_base - params.brightness_range),
                    min(100, params.brightness_base + params.brightness_range)
                )
                v = v_percent / 100.0
                
                colors.append(hsv_to_hex(h, s, v))
        
        else:
            # 従来のランダム生成モード（色相距離チェック付き）
            print(f"🔍 [DEBUG] ランダム生成モード: 最小色相距離 {params.min_hue_distance}°")
            
            generated_hues = []
            # configから最大試行回数を取得
            max_attempts = SYSTEM_SETTINGS["max_color_generation_attempts"]
            
            for i in range(params.color_count):
                attempts = 0
                while attempts < max_attempts:
                    # 色相をランダム生成
                    h = random.uniform(
                        params.hue_center - params.hue_range,
                        params.hue_center + params.hue_range
                    ) % 360
                    
                    # 既存の色相との距離をチェック
                    if all(calculate_hue_distance(h, existing_h) >= params.min_hue_distance 
                           for existing_h in generated_hues):
                        generated_hues.append(h)
                        break
                    
                    attempts += 1
                
                # 最大試行回数に達した場合は距離チェックを無視して追加
                if attempts >= max_attempts:
                    h = random.uniform(
                        params.hue_center - params.hue_range,
                        params.hue_center + params.hue_range
                    ) % 360
                    generated_hues.append(h)
                    print(f"⚠️ [DEBUG] 色相距離チェック失敗: {h:.1f}° を強制追加")
                
                # 彩度と明度はランダム生成
                s_percent = random.uniform(
                    max(0, params.saturation_base - params.saturation_range),
                    min(100, params.saturation_base + params.saturation_range)
                )
                s = s_percent / 100.0
                
                v_percent = random.uniform(
                    max(0, params.brightness_base - params.brightness_range),
                    min(100, params.brightness_base + params.brightness_range)
                )
                v = v_percent / 100.0
                
                colors.append(hsv_to_hex(generated_hues[-1], s, v))
            
            # 表示精度でフォーマット（configから取得）
            hue_precision = COLOR_SETTINGS["hue_display_precision"]
            print(f"🔍 [DEBUG] ランダム生成色相: {[f'{h:.{hue_precision}f}°' for h in generated_hues]}")
        
    except Exception as e:
        print(f"❌ [COLOR_UTILS] 色生成エラー: {e}")
        # エラー時はconfigからフォールバック色を返す
        fallback_colors = COLOR_SETTINGS["error_fallback_colors"]
        colors = fallback_colors[:params.color_count]
        # 不足分は最初の色で補完
        while len(colors) < params.color_count:
            colors.append(fallback_colors[0])
    
    return colors


def generate_four_patterns(colors: List[str], groups: List[str]) -> List[List[str]]:
    """4つの異なる色割り当てパターンを生成（重複なし完全ランダム）
    
    Args:
        colors: 色のリスト
        groups: グループのリスト
        
    Returns:
        4つのパターンのリスト（各パターンは色のリスト）
    """
    print(f"🎨 [DEBUG] 4パターン生成開始: {len(colors)}色, {len(groups)}グループ")
    
    if len(colors) != len(groups):
        raise ValueError(f"色数({len(colors)})とグループ数({len(groups)})が一致しません")
    
    try:
        # 全ての順列を生成
        all_permutations = list(itertools.permutations(colors))
        print(f"🎨 [DEBUG] 全順列数: {len(all_permutations)}通り")
        
        # パターン数をconfigから取得
        from config import HSV_VARIATION_PATTERNS
        pattern_count = HSV_VARIATION_PATTERNS["pattern_count"]
        
        # 指定数以上の順列がある場合は重複なしで選択
        if len(all_permutations) >= pattern_count:
            selected_patterns = random.sample(all_permutations, pattern_count)
            print(f"🎨 [DEBUG] 完全ランダムで{pattern_count}パターン選択")
        else:
            # 不足の場合は全て使用
            selected_patterns = all_permutations
            # 不足分は最初のパターンをコピーして補完
            while len(selected_patterns) < pattern_count:
                selected_patterns.append(all_permutations[0] if all_permutations else tuple(colors))
            print(f"🎨 [DEBUG] 全パターン使用+補完: {len(selected_patterns)}個")
        
        # tupleをlistに変換
        result_patterns = [list(pattern) for pattern in selected_patterns]
        
        # デバッグ出力
        for i, pattern in enumerate(result_patterns, 1):
            assignments = [f"{group}={color}" for group, color in zip(groups, pattern)]
            print(f"🎨 [DEBUG] パターン{i}: {', '.join(assignments)}")
        
        return result_patterns
        
    except Exception as e:
        print(f"❌ [COLOR_UTILS] パターン生成エラー: {e}")
        # エラー時は同じパターンを指定数返す
        from config import HSV_VARIATION_PATTERNS
        pattern_count = HSV_VARIATION_PATTERNS["pattern_count"]
        return [colors] * pattern_count