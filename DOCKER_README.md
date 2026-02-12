# EZ_pair_graph - Docker セットアップ

## 前提条件

- Docker がインストールされていること

## クイックスタート

```bash
# イメージをビルド
make build

# テストデータで実行
make test

# 自分のデータで実行（dataディレクトリにファイルを置く）
make plot FILE=data/your_input.txt

# オプション付きで実行
make plot FILE=data/your_input.txt OPTS="--format png --log2"
```

## 直接Dockerコマンドで実行

```bash
# ビルド
docker build -t ez_pair_graph .

# テストデータで実行
docker run --rm \
    -v $(pwd)/output_EZ:/app/output_EZ \
    ez_pair_graph \
    ./pipeline_for_EZ_plot.sh test_dataset.txt

# 自分のデータで実行
docker run --rm \
    -v $(pwd)/data:/data \
    -v $(pwd)/output_EZ:/app/output_EZ \
    ez_pair_graph \
    ./pipeline_for_EZ_plot.sh /data/your_input.txt

# SVG形式で出力
docker run --rm \
    -v $(pwd)/data:/data \
    -v $(pwd)/output_EZ:/app/output_EZ \
    ez_pair_graph \
    ./pipeline_for_EZ_plot.sh /data/your_input.txt --format svg

# HDBSCAN クラスタリングで実行
docker run --rm \
    -v $(pwd)/data:/data \
    -v $(pwd)/output_EZ:/app/output_EZ \
    ez_pair_graph \
    ./pipeline_for_EZ_plot.sh /data/your_input.txt --method hdbscan --min_cluster_size 3
```

## 出力

結果は `output_EZ/` ディレクトリに保存されます：

- `clustered_data.txt` - クラスタリング済みデータ
- `calculated_points.txt` - 統計計算結果
- `slopegraph.pdf` - スロープグラフ
- `boxplot_with_lines.pdf` - クラスタ付き折れ線プロット
- `arrow_boxplot_chart.pdf` - 矢印付き箱ひげ図
- `trapezoid.pdf` - 台形プロット

## オプション一覧

| オプション | 説明 |
|---|---|
| `--format FORMAT` | 出力形式: pdf(デフォルト), svg, png, html, json |
| `--output-prefix PREFIX` | 出力ファイル名のプレフィックス |
| `--no-outliers` | 箱ひげ図の外れ値を非表示 |
| `--log2` | log2変換を適用 |
| `--show-numbers` | クラスタ番号/サンプル数を表示 |
| `--method METHOD` | クラスタリング手法: hierarchical(デフォルト), hdbscan |
| `--max_k N` | 階層クラスタリングの最大クラスタ数(デフォルト: 7) |
| `--linkage METHOD` | 連結法: ward(デフォルト), complete, average, single |
| `--min_cluster_size N` | HDBSCAN最小クラスタサイズ(デフォルト: 5) |
| `--min_samples N` | HDBSCANコアポイント最小サンプル数 |
