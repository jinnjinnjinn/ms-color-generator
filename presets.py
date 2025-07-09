"""
MS Color Generator - プリセット定義
"""

from typing import Dict
from models import ColorGenerationParams


# プリセット定義（従来のトーンを再現）
COLOR_PRESETS: Dict[str, ColorGenerationParams] = {
    "ダル": ColorGenerationParams(
        saturation_base=35.0, saturation_range=15.0,
        brightness_base=50.0, brightness_range=20.0,
        hue_center=45.0, hue_range=60.0,
        color_count=4, equal_hue_spacing=False, min_hue_distance=30.0
    ),
    "ライト グレイッシュ": ColorGenerationParams(
        saturation_base=8.0, saturation_range=8.0,
        brightness_base=83.0, brightness_range=13.0,
        hue_center=180.0, hue_range=180.0,
        color_count=4, equal_hue_spacing=False, min_hue_distance=30.0
    ),
    "ペール": ColorGenerationParams(
        saturation_base=28.0, saturation_range=13.0,
        brightness_base=90.0, brightness_range=10.0,
        hue_center=0.0, hue_range=180.0,
        color_count=4, equal_hue_spacing=False, min_hue_distance=30.0
    ),
    "ビビッド": ColorGenerationParams(
        saturation_base=90.0, saturation_range=10.0,
        brightness_base=75.0, brightness_range=25.0,
        hue_center=0.0, hue_range=180.0,
        color_count=4, equal_hue_spacing=False, min_hue_distance=30.0
    ),
    "アース カラー": ColorGenerationParams(
        saturation_base=40.0, saturation_range=20.0,
        brightness_base=50.0, brightness_range=20.0,
        hue_center=40.0, hue_range=40.0,
        color_count=4, equal_hue_spacing=False, min_hue_distance=30.0
    ),
    "モノクロ": ColorGenerationParams(
        saturation_base=5.0, saturation_range=5.0,
        brightness_base=55.0, brightness_range=35.0,
        hue_center=0.0, hue_range=180.0,
        color_count=4, equal_hue_spacing=False, min_hue_distance=30.0
    )
}