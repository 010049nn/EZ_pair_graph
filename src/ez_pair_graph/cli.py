# Copyright (c) 2025. RIKEN All rights reserved.
# This is for academic and non-commercial research use only.
# The technology is currently under patent application.
# Commercial use is prohibited without a separate license agreement.
# E-mail: akihiro.ezoe@riken.jp

"""
Command-line interface for ez-pair-graph.
Usage: ez-pair-graph data.txt [options]
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog='ez-pair-graph',
        description='EZ-Pair Graph: Scalable unified-axis visualization '
                    'for summarizing large-scale paired data',
    )

    parser.add_argument('input_file', help='Input data file (space/tab/comma-separated)')

    parser.add_argument('--format', '-f',
                        choices=['pdf', 'svg', 'png', 'html', 'json'],
                        default='pdf',
                        help='Output format (default: pdf)')
    parser.add_argument('--output-dir', default='output_EZ',
                        help='Output directory (default: output_EZ)')
    parser.add_argument('--output-prefix', default=None,
                        help='Prefix for output filenames')
    parser.add_argument('--plots', nargs='+',
                        choices=['slopegraph', 'trapezoid',
                                 'clustered_line', 'parallel_arrow'],
                        default=None,
                        help='Which plots to generate (default: all)')

    parser.add_argument('--no-outliers', action='store_true',
                        help='Hide outliers in boxplots')
    parser.add_argument('--log2', action='store_true',
                        help='Apply log2 transformation to values')
    parser.add_argument('--show-numbers', action='store_true',
                        help='Display cluster numbers or sample counts on plots')

    parser.add_argument('--method',
                        choices=['hierarchical', 'hdbscan'],
                        default='hierarchical',
                        help='Clustering method (default: hierarchical)')
    parser.add_argument('--max-k', type=int, default=7,
                        help='Maximum clusters for hierarchical (default: 7)')
    parser.add_argument('--linkage',
                        choices=['ward', 'complete', 'average', 'single'],
                        default='ward',
                        help='Linkage method for hierarchical (default: ward)')
    parser.add_argument('--min-cluster-size', type=int, default=5,
                        help='Min cluster size for HDBSCAN (default: 5)')
    parser.add_argument('--min-samples', type=int, default=None,
                        help='Min samples for HDBSCAN core points')

    args = parser.parse_args()

    from . import plot

    try:
        outputs = plot(
            args.input_file,
            output_dir=args.output_dir,
            format=args.format,
            output_prefix=args.output_prefix,
            plots=args.plots,
            method=args.method,
            max_k=args.max_k,
            linkage_method=args.linkage,
            min_cluster_size=args.min_cluster_size,
            min_samples=args.min_samples,
            log2=args.log2,
            no_outliers=args.no_outliers,
            show_numbers=args.show_numbers,
        )

        print("Pipeline completed successfully.")
        print(f"Output directory: {args.output_dir}")
        for name, path in outputs.items():
            print(f"  {name}: {path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
