# Copyright (c) 2025. RIKEN All rights reserved.
# This is for academic and non-commercial research use only.
# The technology is currently under patent application.
# Commercial use is prohibited without a separate license agreement.
# E-mail: akihiro.ezoe@riken.jp

"""Command-line interface for EZ-Pair Graph."""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="ez-pair-graph",
        description="EZ-Pair Graph: Scalable unified-axis visualization for summarizing large-scale paired data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ez-pair-graph data.txt
  ez-pair-graph data.txt --format png
  ez-pair-graph data.txt --format svg --output-prefix experiment1
  ez-pair-graph data.txt --method hdbscan --min-cluster-size 3
  ez-pair-graph data.txt --plots trapezoid clustered_line
  ez-pair-graph data.txt --log2 --no-outliers --show-numbers

Copyright (c) 2025. RIKEN All rights reserved.
Academic and non-commercial research use only.
        """,
    )

    parser.add_argument("input_file", help="Input data file (comma/tab/space-separated X Y values)")

    # Output options
    parser.add_argument("--format", "-f", choices=["pdf", "svg", "png", "html", "json"],
                        default="pdf", help="Output format (default: pdf)")
    parser.add_argument("--output-dir", "-o", default="output_EZ",
                        help="Output directory (default: output_EZ)")
    parser.add_argument("--output-prefix", default=None,
                        help="Prefix for output filenames")
    parser.add_argument("--plots", nargs="+",
                        choices=["slopegraph", "trapezoid", "clustered_line", "parallel_arrow"],
                        default=None,
                        help="Which plots to generate (default: all)")

    # Display options
    parser.add_argument("--no-outliers", action="store_true",
                        help="Hide outliers (data points outside whiskers)")
    parser.add_argument("--log2", action="store_true",
                        help="Apply log2 transformation to values")
    parser.add_argument("--show-numbers", action="store_true",
                        help="Display cluster numbers or sample counts on plots")

    # Clustering options
    parser.add_argument("--method", "-m", choices=["hierarchical", "hdbscan"],
                        default="hierarchical",
                        help="Clustering method (default: hierarchical)")
    parser.add_argument("--max-k", type=int, default=7,
                        help="Maximum number of clusters for hierarchical (default: 7)")
    parser.add_argument("--linkage", choices=["ward", "complete", "average", "single"],
                        default="ward",
                        help="Linkage method for hierarchical clustering (default: ward)")
    parser.add_argument("--min-cluster-size", type=int, default=5,
                        help="Minimum cluster size for HDBSCAN (default: 5)")
    parser.add_argument("--min-samples", type=int, default=None,
                        help="Minimum samples for HDBSCAN core points")

    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    args = parser.parse_args()

    from ez_pair_graph.api import plot

    try:
        results = plot(
            input_file=args.input_file,
            output_dir=args.output_dir,
            format=args.format,
            plots=args.plots,
            method=args.method,
            max_k=args.max_k,
            linkage_method=args.linkage,
            min_cluster_size=args.min_cluster_size,
            min_samples=args.min_samples,
            no_outliers=args.no_outliers,
            log2=args.log2,
            show_numbers=args.show_numbers,
            output_prefix=args.output_prefix,
        )
        print(f"\nPipeline completed. Generated {len(results)} plot(s) in {args.output_dir}/")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
