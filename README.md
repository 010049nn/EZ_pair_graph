# EZ Plot Pipeline

Copyright (c) 2025. RIKEN All rights reserved.
This is for academic and non-commercial research use only.
The technology is currently under patent application.
Commercial use is prohibited without a separate license agreement.
E-mail: akihiro.ezoe@riken.jp

## Overview

This pipeline generates multiple visualizations for paired data (X, Y values) analysis.

## Quick Start

```bash
bash pipeline_for_EZ_plot.sh test_dataset.txt
```

## Docker

You can run the pipeline in a Docker container without installing dependencies locally.

### Build

```bash
docker build -t ez_pair_graph .
```

### Run with test data

```bash
docker run --rm \
    -v $(pwd)/output_EZ:/app/output_EZ \
    ez_pair_graph \
    bash ./pipeline_for_EZ_plot.sh test_dataset.txt
```

### Run with your own data

Place your input file in a `data/` directory, then:

```bash
docker run --rm \
    -v $(pwd)/data:/data \
    -v $(pwd)/output_EZ:/app/output_EZ \
    ez_pair_graph \
    bash ./pipeline_for_EZ_plot.sh /data/your_input.txt
```

Results are saved in the `output_EZ/` directory.

## Input File Format

The input file should contain paired X and Y values. The following formats are accepted:

- Space-separated values
- Tab-separated values
- Comma-separated values (CSV)
- With or without header line (auto-detected)

Example:
```
X Y
1.5 2.3
2.0 1.8
3.1 4.2
```

## Pipeline Steps

1. **preparation_1.py** - Clustering analysis
2. **preparation_2.py** - Statistical calculations
3. **slopegraph.py** - Simple slope graph
4. **clustered_line_plot.py** - Clustered line plot with boxplots
5. **parallel_arrow_plot.py** - Parallel arrow plot
6. **trapezoid_plot.py** - Trapezoid plot with quartile bands

All visualization scripts read from `output_EZ/clustered_data.txt` to ensure consistent data across all plots.

## Command Line Options

### Output Options

| Option | Description |
|--------|-------------|
| `--format FORMAT` | Output format: `pdf` (default), `svg`, `png`, `html`, `json` |
| `--output-prefix PREFIX` | Prefix for output filenames (e.g., 'exp1' creates exp1_slopegraph.pdf) |
| `--no-outliers` | Hide outliers in boxplots |
| `--log2` | Apply log2 transformation to values |
| `--show-numbers` | Display cluster numbers (g_num) or sample counts on plots |

### Clustering Options

| Option | Description |
|--------|-------------|
| `--method METHOD` | Clustering method: `hierarchical` (default) or `hdbscan` |
| `--max_k N` | Maximum number of clusters for hierarchical clustering (default: 7) |
| `--linkage METHOD` | Linkage method for hierarchical: `ward` (default), `complete`, `average`, `single` |
| `--min_cluster_size N` | Minimum cluster size for HDBSCAN (default: 5) |
| `--min_samples N` | Minimum samples for HDBSCAN core points (default: None) |

## Option Details

### --format

Specifies the output file format for all generated plots.

- **pdf**: Portable Document Format (default) - Best for printing and publications
- **svg**: Scalable Vector Graphics - Best for web and editing
- **png**: Portable Network Graphics - Raster image format, 300 DPI
- **html**: HTML with embedded SVG - Web-ready format
- **json**: JSON data - Plot position data for custom rendering

### --output-prefix

Specifies a prefix for all output filenames. Useful for organizing multiple analyses.

Example: `--output-prefix wheat_exp1` produces:
- wheat_exp1_slopegraph.pdf
- wheat_exp1_boxplot_with_lines.pdf
- wheat_exp1_arrow_boxplot_chart.pdf
- wheat_exp1_trapezoid.pdf

### --no-outliers

When enabled, data points outside the boxplot whisker range (Q1 - 1.5×IQR to Q3 + 1.5×IQR) are excluded from visualization elements (lines, bands, arrows). This helps focus on the main data distribution.

Note: The sample counts (n=) displayed with `--show-numbers` still reflect the **total** number of ascending/descending samples, not the filtered count. This allows you to see both the full group sizes and the filtered visualization.

### --log2

Applies log2 transformation to all values before analysis and visualization. Useful for:
- Data with exponential distributions
- Gene expression data
- Data spanning multiple orders of magnitude

Non-positive values are replaced with a minimum value (1e-10) before transformation.

Output files will have `_log2` suffix (e.g., `slopegraph_log2.pdf`).

### --show-numbers

Displays additional numerical information on plots:
- **slopegraph.py**: Shows count of ascending/descending lines
- **clustered_line_plot.py**: Shows cluster numbers (g_num) on lines
- **parallel_arrow_plot.py**: Shows cluster numbers (g_num) on arrows
- **trapezoid_plot.py**: Shows sample counts (n) for up/down groups

### --method

Selects the clustering algorithm:

**hierarchical** (default):
- Uses agglomerative hierarchical clustering
- Automatically determines optimal cluster count using elbow method
- Suitable for most datasets

**hdbscan**:
- Density-based clustering
- Does not require specifying cluster count
- Better for datasets with varying cluster densities

### --linkage

Linkage method for hierarchical clustering:

- **ward** (default): Minimizes within-cluster variance. Best for compact, spherical clusters.
- **complete**: Maximum distance between cluster members. Creates more compact clusters.
- **average**: Average distance between cluster members. Balanced approach.
- **single**: Minimum distance between cluster members. Can create elongated clusters.

## Output Files

All output files are saved in the `output_EZ/` directory.

### Plot Files

| File | Description |
|------|-------------|
| `[PREFIX_]slopegraph.FORMAT` | Simple slope graph showing all data points |
| `[PREFIX_]boxplot_with_lines.FORMAT` | Clustered line plot with half-boxplots |
| `[PREFIX_]arrow_boxplot_chart.FORMAT` | Parallel arrow plot with boxplots |
| `[PREFIX_]trapezoid.FORMAT` | Trapezoid plot with quartile bands |

Note: `[PREFIX_]` is included only if `--output-prefix` is specified.

## Usage Examples

With output prefix:
```bash
bash pipeline_for_EZ_plot.sh data.txt --output-prefix experiment1
```

Output as PNG with log2 transformation and prefix:
```bash
bash pipeline_for_EZ_plot.sh data.txt --format png --log2 --output-prefix wheat_data
```

Full options example:
```bash
bash pipeline_for_EZ_plot.sh data.txt --format svg --log2 --no-outliers --show-numbers --output-prefix my_analysis --method hierarchical --max_k 10
```

## Dependencies

- Python 3.x
- NumPy
- Pandas
- Matplotlib
- SciPy

## License

This software is for academic and non-commercial research use only.
Commercial use is prohibited without a separate license agreement.

<img width="2403" height="883" alt="Image" src="https://github.com/user-attachments/assets/a0fb21c0-dde7-4ff6-9e51-be7fa00f9cbf" />
