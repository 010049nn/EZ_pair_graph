# EZ Plot Pipeline

Copyright (c) 2025. RIKEN All rights reserved.
This is for academic and non-commercial research use only.
The technology is currently under patent application.
Commercial use is prohibited without a separate license agreement.
E-mail: akihiro.ezoe@riken.jp

## Overview

This pipeline generates multiple visualizations for paired data (X, Y values) analysis, including clustering and statistical compariso
ns.

## Quick Start

```bash
bash pipeline_for_EZ_plot.sh data.txt
```

## Input File Format

The input file should contain paired X and Y values. The following formats are supported:

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

When enabled, data points outside the boxplot whisker range (Q1 - 1.5×IQR to Q3 + 1.5×IQR) are excluded from visualization elements (l
ines, bands, arrows). This helps focus on the main data distribution.

Note: The sample counts (n=) displayed with `--show-numbers` still reflect the **total** number of ascending/descending samples, not t
he filtered count. This allows you to see both the full group sizes and the filtered visualization.

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

### --max_k

Maximum number of clusters to consider for hierarchical clustering. The algorithm uses the elbow method to find the optimal number up
to this limit.

Default: 7

### --linkage

Linkage method for hierarchical clustering:

- **ward** (default): Minimizes within-cluster variance. Best for compact, spherical clusters.
- **complete**: Maximum distance between cluster members. Creates more compact clusters.
- **average**: Average distance between cluster members. Balanced approach.
- **single**: Minimum distance between cluster members. Can create elongated clusters.

### --min_cluster_size

Minimum number of points required to form a cluster in HDBSCAN. Points in smaller groups are treated as noise.

Default: 5

### --min_samples

Number of samples in a neighborhood for a point to be considered a core point in HDBSCAN. If not specified, defaults to min_cluster_si
ze.

## Output Files

All output files are saved in the `output_EZ/` directory.

### Data Files

| File | Description |
|------|-------------|
| `clustered_data.txt` | Clustered data with X, Y, and Cluster columns |
| `calculated_points.txt` | Calculated statistics for each cluster |
| `group_statistics.txt` | Detailed statistics per group |
| `.log2_transformed` | Marker file indicating log2 transformation was applied |

### Plot Files

| File | Description |
|------|-------------|
| `[PREFIX_]slopegraph.FORMAT` | Simple slope graph showing all data points |
| `[PREFIX_]boxplot_with_lines.FORMAT` | Clustered line plot with half-boxplots |
| `[PREFIX_]arrow_boxplot_chart.FORMAT` | Parallel arrow plot with boxplots |
| `[PREFIX_]trapezoid.FORMAT` | Trapezoid plot with quartile bands |

Note: `[PREFIX_]` is included only if `--output-prefix` is specified.

## Data Processing

### Data Consistency

All visualization scripts read from `output_EZ/clustered_data.txt` to ensure:
- Consistent data point counts across all plots
- Identical ascending/descending group classifications

## Usage Examples

Basic usage:
```bash
bash pipeline_for_EZ_plot.sh data.txt
```

With output prefix:
```bash
bash pipeline_for_EZ_plot.sh data.txt --output-prefix experiment1
```

Output as PNG with log2 transformation and prefix:
```bash
bash pipeline_for_EZ_plot.sh data.txt --format png --log2 --output-prefix wheat_data
```

HDBSCAN clustering with custom parameters:
```bash
bash pipeline_for_EZ_plot.sh data.txt --method hdbscan --min_cluster_size 3
```

Hierarchical clustering with specific settings:
```bash
bash pipeline_for_EZ_plot.sh data.txt --method hierarchical --max_k 5 --linkage complete
```

Full options example:
```bash
bash pipeline_for_EZ_plot.sh data.txt --format svg --log2 --no-outliers --show-numbers --output-prefix my_analysis --method hierarchic
al --max_k 10
```

## Individual Script Usage

Each visualization script can be run independently after running the preparation scripts:

```bash
python slopegraph.py --format png --log2 --show-numbers --output-prefix mydata
python clustered_line_plot.py --format svg --no-outliers --output-prefix mydata
python parallel_arrow_plot.py --format pdf --show-numbers --output-prefix mydata
python trapezoid_plot.py --format png --log2 --output-prefix mydata
```

Note: All scripts read from `output_EZ/clustered_data.txt`, so `preparation_1.py` must be run first.

## Dependencies

- Python 3.x
- NumPy
- Pandas
- Matplotlib
- SciPy

## License

This software is for academic and non-commercial research use only.
Commercial use is prohibited without a separate license agreement.


![Image](https://github.com/user-attachments/assets/f91cde18-4acd-4082-bd2e-3735907b1e3b)
