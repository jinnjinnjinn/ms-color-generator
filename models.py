"""
MS Color Generator - データモデル定義
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ColorGenerationParams:
    """色生成パラメータクラス"""
    saturation_base: float = 50.0       # 彩度基準 (0-100%)
    saturation_range: float = 15.0      # 彩度誤差範囲 (±この値, 最大50)
    brightness_base: float = 60.0       # 明度基準 (0-100%) 
    brightness_range: float = 15.0      # 明度誤差範囲 (±この値, 最大50)
    hue_center: float = 180.0           # 中心色相 (0-360度)
    hue_range: float = 60.0             # 色相誤差範囲 (±この値, 最大180度)
    color_count: int = 4                # 生成色数
    equal_hue_spacing: bool = False     # 色相等間隔生成モード
    min_hue_distance: float = 30.0      # 最小色相距離 (0-180度)
    
    def __post_init__(self):
        """パラメータ値の検証"""
        # 範囲チェック
        self.saturation_base = max(0.0, min(100.0, self.saturation_base))
        self.saturation_range = max(0.0, min(50.0, self.saturation_range))
        self.brightness_base = max(0.0, min(100.0, self.brightness_base))
        self.brightness_range = max(0.0, min(50.0, self.brightness_range))
        self.hue_center = self.hue_center % 360.0
        self.hue_range = max(1.0, min(180.0, self.hue_range))
        self.color_count = max(2, min(10, self.color_count))
        self.min_hue_distance = max(0.0, min(180.0, self.min_hue_distance))