#!/bin/bash

#Copyright (c) 2025. RIKEN All rights reserved. This is for academic and non-commercial research use only.
#The technology is currently under patent application. Commercial use is prohibited without a separate license agreement.
#E-mail: akihiro.ezoe@riken.jp

set -e

show_help() {
    cat << EOF
Usage: $0 <input_file> [options]

Arguments:
  input_file          Input data file (space/tab-separated X Y values)

Output Options:
  --format FORMAT     Output format: 'pdf' (default), 'svg', 'png', 'html', 'json'
                      JSON outputs plot position data instead of images
  --output-prefix PREFIX  Prefix for output filenames (e.g., 'experiment1' creates
                      experiment1_slopegraph.pdf, experiment1_boxplot_with_lines.pdf, etc.)
  --no-outliers       Hide outliers in boxplots
  --log2              Apply log2 transformation to values
  --show-numbers      Display cluster numbers (g_num) or sample counts on plots

Clustering Options (passed to preparation_1.py):
  --method METHOD     Clustering method: 'hierarchical' (default) or 'hdbscan'
  --max_k N           Maximum number of clusters for hierarchical (default: 7)
  --linkage METHOD    Linkage method for hierarchical clustering:
                      'ward' (default), 'complete', 'average', 'single'
  --min_cluster_size N  Minimum cluster size for HDBSCAN (default: 5)
  --min_samples N     Minimum samples for HDBSCAN core points (default: None)

Examples:
  $0 data.txt
  $0 data.txt --format svg
  $0 data.txt --output-prefix experiment1
  $0 data.txt --output-prefix wheat_data --format png --log2
  $0 data.txt --format png --method hierarchical --max_k 5
  $0 data.txt --method hdbscan --min_cluster_size 3

Output:
  output_EZ/clustered_data.txt            - Clustered data
  output_EZ/calculated_points.txt         - Calculated statistics
  output_EZ/[PREFIX_]slopegraph.FORMAT    - Simple slope graph
  output_EZ/[PREFIX_]boxplot_with_lines.FORMAT - Clustered line plot
  output_EZ/[PREFIX_]arrow_boxplot_chart.FORMAT - Parallel arrow plot
  output_EZ/[PREFIX_]trapezoid.FORMAT     - Trapezoid plot

  With --log2 option, output files will have '_log2' suffix before extension.
EOF
    exit 0
}

if [ $# -eq 0 ]; then
    echo "Error: input_file is required"
    echo "Use '$0 --help' for usage information"
    exit 1
fi

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
fi

INPUT_FILE=$1
shift

CLUSTER_OPTS=""
OUTPUT_FORMAT="pdf"
OUTPUT_PREFIX=""
MAX_K=""
NO_OUTLIERS=""
LOG2=""
SHOW_NUMBERS=""

while [ $# -gt 0 ]; do
    case "$1" in
        --format|-f)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --output-prefix)
            OUTPUT_PREFIX="$2"
            shift 2
            ;;
        --no-outliers)
            NO_OUTLIERS="--no-outliers"
            shift
            ;;
        --log2)
            LOG2="--log2"
            shift
            ;;
        --show-numbers)
            SHOW_NUMBERS="--show-numbers"
            shift
            ;;
        --method)
            CLUSTER_OPTS="$CLUSTER_OPTS --method $2"
            shift 2
            ;;
        --max_k)
            MAX_K="$2"
            shift 2
            ;;
        --linkage)
            CLUSTER_OPTS="$CLUSTER_OPTS --linkage $2"
            shift 2
            ;;
        --min_cluster_size)
            CLUSTER_OPTS="$CLUSTER_OPTS --min_cluster_size $2"
            shift 2
            ;;
        --min_samples)
            CLUSTER_OPTS="$CLUSTER_OPTS --min_samples $2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Output format: $OUTPUT_FORMAT"
if [ -n "$OUTPUT_PREFIX" ]; then
    echo "Output prefix: $OUTPUT_PREFIX"
    PREFIX_OPT="--output-prefix $OUTPUT_PREFIX"
else
    PREFIX_OPT=""
fi
if [ -n "$LOG2" ]; then
    echo "Log2 transformation: enabled"
fi
if [ -n "$SHOW_NUMBERS" ]; then
    echo "Show numbers: enabled"
fi
echo ""

echo "Step 1: Running preparation_1.py with $INPUT_FILE..."
if [ -n "$MAX_K" ]; then
    python preparation_1.py "$INPUT_FILE" "$MAX_K" $CLUSTER_OPTS $LOG2
else
    python preparation_1.py "$INPUT_FILE" $CLUSTER_OPTS $LOG2
fi

echo "Step 2: Running preparation_2.py..."
python preparation_2.py

echo "Step 3: Running Python visualization scripts..."
echo "  3a: Running slopegraph.py..."
python slopegraph.py --format "$OUTPUT_FORMAT" $PREFIX_OPT $NO_OUTLIERS $LOG2 $SHOW_NUMBERS

echo "  3b: Running clustered_line_plot.py..."
python clustered_line_plot.py --format "$OUTPUT_FORMAT" $PREFIX_OPT $NO_OUTLIERS $LOG2 $SHOW_NUMBERS

echo "  3c: Running parallel_arrow_plot.py..."
python parallel_arrow_plot.py --format "$OUTPUT_FORMAT" $PREFIX_OPT $NO_OUTLIERS $LOG2 $SHOW_NUMBERS

echo "  3d: Running trapezoid_plot.py..."
python trapezoid_plot.py --format "$OUTPUT_FORMAT" $PREFIX_OPT $NO_OUTLIERS $LOG2 $SHOW_NUMBERS

echo ""
echo "Pipeline execution completed successfully"
echo "Output format: $OUTPUT_FORMAT"
if [ -n "$LOG2" ]; then
    echo "Log2 transformation: applied"
fi
if [ -n "$SHOW_NUMBERS" ]; then
    echo "Show numbers: applied"
fi
