---
title: MS Color Generator
sdk: gradio
sdk_version: 5.35.0
app_file: app.py
pinned: false
license: mit
thumbnail: >-
  https://huggingface.co/spaces/jinnjinnjinn/ms-color-generator/resolve/main/ico.png
short_description: Propose ideas for unique mobile suit coloring patterns
emoji: ⚡
colorFrom: purple
colorTo: pink
---


# MS Color Generator

<div align="center">

![MS Color Generator Logo](https://huggingface.co/spaces/jinnjinnjinn/ms-color-generator/resolve/main/ico.png)

**Propose ideas for unique mobile suit coloring patterns**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Gradio](https://img.shields.io/badge/Gradio-4.0+-orange.svg)](https://gradio.app)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*Dynamically change colors of layered images with real-time preview and intelligent color generation*

[English](#english) | [日本語](#japanese)

</div>

---

## English

### Overview

MS Color Generator is a powerful tool for dynamically changing colors in layered PNG images. It features intelligent color generation, HSV manipulation, and real-time preview capabilities.

### ✨ Key Features

- **🎨 Dynamic Color Management**: Change colors of specific layers in real-time
- **🤖 Intelligent Color Generation**: AI-powered color palette generation with multiple presets
- **🖼️ Multi-Pattern Preview**: Generate and compare 4 different color patterns simultaneously  
- **🎯 Interactive Layer Selection**: Click on images to select and edit specific layers
- **🌈 Advanced Color Tools**: HSV manipulation, color extraction from uploaded images
- **💾 Export & Save**: Save your creations with timestamp organization

### 🚀 Quick Start

#### Prerequisites
- Python 3.8 or higher
- 4GB+ RAM recommended
- Modern web browser

#### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jinnjinnjinn/ms-color-generator.git
   cd ms-color-generator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare your layer files**
   - Create a `layer` folder in the project directory
   - Add your PNG layer files named as: `layer1.png`, `layer2.png`, `layer3.png`, etc.
   - Ensure layers use **magenta (#ff00ff)** as the target color to be replaced

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Open in browser**
   - Navigate to `http://localhost:7860`
   - The interface will automatically open in your default browser

### 📁 Project Structure

```
ms-color-generator/
├── main.py                 # Application entry point
├── config.py              # Configuration settings
├── models.py              # Data models
├── layer_manager.py       # Layer processing logic
├── color_utils.py         # Color manipulation utilities
├── ui.py                  # Main UI components
├── ui_handlers.py         # Event handlers
├── ui_generators.py       # Pattern generation
├── ui_state.py           # State management
├── ui_utils.py           # UI utilities
├── presets.py            # Color presets
├── layer/                # Layer files directory
│   ├── layer1.png
│   ├── layer2.png
│   └── ...
├── output/               # Generated images
└── grouping.txt         # Layer grouping configuration
```

### 🎯 How to Use

#### Basic Workflow

1. **Prepare Layer Files**
   - Create PNG images with transparent backgrounds
   - Use magenta (#ff00ff) for areas you want to colorize
   - Save as `layer1.png`, `layer2.png`, etc. in the `layer/` folder

2. **Configure Groups** (Optional)
   - Edit `grouping.txt` to define layer groups
   - Format: `layer_numbers:color_code`
   - Example: `1,3,5:#ff0000` (layers 1,3,5 in red group)

3. **Generate Colors**
   - Choose a preset (Vivid, Pale, Earth tones, etc.)
   - Adjust HSV parameters as needed
   - Click "Generate 4 Color Patterns"

4. **Refine Colors**
   - Use color pickers for manual adjustments
   - Apply HSV shifts to all colors simultaneously
   - Click layers in the image for direct editing

5. **Export Results**
   - Select your favorite pattern from the gallery
   - Click "Save Main Display" to export

#### Advanced Features

**Color Extraction**
- Upload reference images to extract color palettes
- Select colors from the extracted palette
- Generate patterns based on real-world color schemes

**HSV Manipulation**
- Shift hue, saturation, and brightness globally
- Create variations of existing color schemes
- Generate complementary color patterns

**Pattern Generation Modes**
- **Equal Spacing**: Distribute colors evenly across the color wheel
- **Random**: Generate random colors within specified parameters
- **Current Colors**: Create variations of currently selected colors

### ⚙️ Configuration

#### Basic Settings (`config.py`)

Key settings you might want to modify:

```python
# UI Layout
UI_LAYOUT = {
    "main_image_height": 480,     # Main display height
    "gallery_columns": 4,         # Gallery columns
    "pattern_gallery_height": 250 # Gallery height
}

# Color Generation
COLOR_SETTINGS = {
    "hue_display_precision": 0,    # HSV display precision
    "overlay_alpha": 0.5           # Layer selection overlay
}
```

#### Layer Grouping (`grouping.txt`)

Define which layers belong to the same color group:

```
1,5,6,7,8,9,12,18,19,21,22,23,24,26:#afb998
2,16,17:#7a8268
3,4,11,13,15:#424539
10,14,20,25:#d0d3c9
```

### 🎨 Color Presets

Built-in presets for different styles:

- **Vivid**: High saturation, bright colors
- **Pale**: Soft, light colors
- **Dull**: Muted, understated tones
- **Earth**: Natural, earthy tones
- **Light Grayish**: Subtle, sophisticated grays
- **Monochrome**: Black and white variations

### 🔧 Troubleshooting

#### Common Issues

**"No layer files found"**
- Ensure layer files are in the `layer/` folder
- Check file naming: `layer1.png`, `layer2.png`, etc.
- Verify PNG format with transparency

**"Colors not changing"**
- Confirm target areas use magenta (#ff00ff)
- Check layer file format (RGBA PNG required)
- Verify image permissions

**Performance Issues**
- Reduce image resolution for faster processing
- Close unused browser tabs
- Increase system RAM if possible

**Browser Compatibility**
- Use modern browsers (Chrome, Firefox, Safari, Edge)
- Enable JavaScript
- Clear browser cache if UI appears broken

### 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting PRs.

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 🙏 Acknowledgments

- Built with [Gradio](https://gradio.app/) for the web interface
- Uses [Pillow](https://pillow.readthedocs.io/) for image processing
- Color science powered by Python's `colorsys` module

---

## Japanese

### 概要

MS Color Generatorは、レイヤー化されたPNG画像の色を動的に変更するための強力なツールです。インテリジェントな色生成、HSV操作、リアルタイムプレビュー機能を備えています。

### ✨ 主な機能

- **🎨 動的色管理**: 特定のレイヤーの色をリアルタイムで変更
- **🤖 インテリジェント色生成**: 複数のプリセットを持つカラーパレット生成支援
- **🖼️ マルチパターンプレビュー**: 4つの異なる配色パターンを同時に生成・比較
- **🎯 インタラクティブレイヤー選択**: 画像をクリックして特定のレイヤーを選択し編集
- **🌈 高度なカラーツール**: 色相・彩度・明度の操作、アップロード画像からの色抽出
- **💾 エクスポート・保存**: タイムスタンプ付きで作品を保存

### 🚀 クイックスタート

#### 前提条件
- Python 3.8以上
- 4GB以上のRAM推奨
- モダンなウェブブラウザ

#### インストール

1. **リポジトリをクローン**
   ```bash
   git clone https://github.com/jinnjinnjinn/ms-color-generator.git
   cd ms-color-generator
   ```

2. **依存関係をインストール**
   ```bash
   pip install -r requirements.txt
   ```

3. **レイヤーファイルを準備**
   - プロジェクトディレクトリに`layer`フォルダを作成
   - PNGレイヤーファイルを`layer1.png`, `layer2.png`, `layer3.png`等の名前で追加
   - レイヤーは**マゼンタ色(#ff00ff)**をターゲット色として使用

4. **アプリケーションを実行**
   ```bash
   python main.py
   ```

5. **ブラウザで開く**
   - `http://localhost:7860`にアクセス
   - デフォルトブラウザで自動的に開きます

### 📁 プロジェクト構造

```
ms-color-generator/
├── main.py                 # アプリケーションエントリーポイント
├── config.py              # 設定
├── models.py              # データモデル
├── layer_manager.py       # レイヤー処理ロジック
├── color_utils.py         # 色操作ユーティリティ
├── ui.py                  # メインUIコンポーネント
├── ui_handlers.py         # イベントハンドラ
├── ui_generators.py       # パターン生成
├── ui_state.py           # 状態管理
├── ui_utils.py           # UIユーティリティ
├── presets.py            # カラープリセット
├── layer/                # レイヤーファイルディレクトリ
│   ├── layer1.png
│   ├── layer2.png
│   └── ...
├── output/               # 生成画像
└── grouping.txt         # レイヤーグループ設定
```

### 🎯 使用方法

#### 基本的なワークフロー

1. **レイヤーファイルの準備**
   - 透明背景のPNG画像を作成
   - 色付けしたい部分にマゼンタ色(#ff00ff)を使用
   - `layer/`フォルダに`layer1.png`, `layer2.png`等で保存

2. **グループ設定**（オプション）
   - `grouping.txt`を編集してレイヤーグループを定義
   - フォーマット: `レイヤー番号:カラーコード`
   - 例: `1,3,5:#ff0000` (レイヤー1,3,5を赤グループに)

3. **色の生成**
   - プリセット（ビビッド、ペール、アースカラー等）を選択
   - 必要に応じてHSVパラメータを調整
   - 「4配色パターン生成」をクリック

4. **色の調整**
   - カラーピッカーで単色の手動調整
   - 全色に同時HSVシフトを適用
   - 画像内のレイヤーをクリックして直接グループを編集

5. **結果のエクスポート**
   - ギャラリーからパターンを選択
   - 「メイン表示を保存」でエクスポート

#### 高度な機能

**色抽出**
- 参考画像をアップロードしてカラーパレットを抽出
- 抽出されたパレットから色を選択
- 実世界の配色スキームに基づいたパターン生成

**HSV操作**
- 色相、彩度、明度をグローバルにシフト
- 既存配色のバリエーション作成
- 補色パターンの生成

**パターン生成モード**
- **等間隔**: 色相環上に色を均等分散
- **ランダム**: 指定パラメータ内でランダム色生成
- **色相違い**: 選択中の色で色相を変えた別のバリエーション作成

### ⚙️ 設定

#### 基本設定 (`config.py`)

変更可能な主要設定:

```python
# UIレイアウト
UI_LAYOUT = {
    "main_image_height": 480,     # メイン表示高さ
    "gallery_columns": 4,         # ギャラリー列数
    "pattern_gallery_height": 250 # ギャラリー高さ
}

# 色設定
COLOR_SETTINGS = {
    "hue_display_precision": 0,    # HSV表示精度
    "overlay_alpha": 0.5           # レイヤー選択オーバーレイ
}
```

#### レイヤーグループ設定 (`grouping.txt`)

同じ色グループに属するレイヤーを定義:

```
1,5,6,7,8,9,12,18,19,21,22,23,24,26:#afb998
2,16,17:#7a8268
3,4,11,13,15:#424539
10,14,20,25:#d0d3c9
```

### 🎨 カラープリセット

様々なスタイルのビルトインプリセット:

- **ビビッド**: 高彩度、鮮やかな色
- **ペール**: 柔らかく、明るい色
- **ダル**: 落ち着いた、控えめなトーン
- **アースカラー**: 自然で土っぽいトーン
- **ライトグレイッシュ**: 繊細で洗練されたグレー
- **モノクロ**: 白黒バリエーション

### 🔧 トラブルシューティング

#### よくある問題

**「レイヤーファイルが見つかりません」**
- レイヤーファイルが`layer/`フォルダにあることを確認
- ファイル名をチェック: `layer1.png`, `layer2.png`等
- PNG形式で透明度があることを確認

**「色が変わらない」**
- ターゲットエリアがマゼンタ色(#ff00ff)を使用していることを確認
- レイヤーファイルフォーマット（RGBA PNG必須）をチェック
- 画像のアクセス権限を確認

**パフォーマンスの問題**
- 高速処理のため画像解像度を下げる
- 未使用のブラウザタブを閉じる
- 可能であればシステムRAMを増設

**ブラウザ互換性**
- モダンブラウザを使用（Chrome、Firefox、Safari、Edge）
- JavaScriptを有効にする
- UIが壊れて見える場合はブラウザキャッシュをクリア

### 🤝 コントリビューション

コントリビューションを歓迎します！PRを提出する前に[Contributing Guidelines](CONTRIBUTING.md)をお読みください。

### 📄 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

### 🙏 謝辞

- ウェブインターフェースに[Gradio](https://gradio.app/)を使用
- 画像処理に[Pillow](https://pillow.readthedocs.io/)を使用
- Pythonのcolorsysモジュールによるカラーサイエンス

TAMIYA（田宮模型） 様には、1948年の創業以来「First in Quality Around the World」の精神で培われた模型文化への貢献に敬意を表します。

グンゼ産業（Mr. Hobby／Mr. Color） 様には、アクリル・ラッカー塗料の長年にわたる研究開発と品質向上への取り組みに感謝します。

ガイアカラー 様には、プロモデラーにも支持される高品質塗料の提供と業界の発展への貢献に深く敬意を表します。

加藤一彌（カトキハジメ） 氏には、独自のメカデザインとモデリング哲学により多くのクリエイターに影響を与えてこられた功績に感謝いたします。