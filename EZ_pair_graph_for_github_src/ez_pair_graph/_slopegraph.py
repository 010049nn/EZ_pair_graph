#Copyright (c) 2025. RIKEN All rights reserved.
#This is for academic and non-commercial research use only.
#The technology is currently under patent application.
#Commercial use is prohibited without a separate license agreement.
#E-mail: akihiro.ezoe@riken.jp

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import argparse
import json
import io
from matplotlib.backends.backend_pdf import PdfPages


def apply_log2_transform(data, min_value=1e-10):
    data = np.array(data, dtype=float)
    data = np.where(data <= 0, min_value, data)
    return np.log2(data), 0


def export_json(output_path, lines_data, stats):
    json_data = {
        'type': 'slopegraph',
        'statistics': stats,
        'lines': lines_data
    }
    with open(output_path, 'w') as f:
        json.dump(json_data, f, indent=2)


def export_html(output_path, svg_content, title):
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        {svg_content}
    </div>
</body>
</html>'''
    with open(output_path, 'w') as f:
        f.write(html_content)


def main():
    parser = argparse.ArgumentParser(description='Generate slope graph')
    parser.add_argument('--format', '-f', choices=['pdf', 'svg', 'png', 'html', 'json'],
                        default='pdf', help='Output format (default: pdf)')
    parser.add_argument('--output', '-o', default=None, help='Output filename (optional)')
    parser.add_argument('--output-prefix', default=None, help='Prefix for output filename')
    parser.add_argument('--no-outliers', action='store_true',
                        help='Hide outliers (data points outside whiskers)')
    parser.add_argument('--log2', action='store_true',
                        help='Apply log2 transformation to values')
    parser.add_argument('--alpha', type=float, default=0.3,
                        help='Line transparency (default: 0.3)')
    parser.add_argument('--linewidth', type=float, default=0.5,
                        help='Line width (default: 0.5)')
    parser.add_argument('--show-numbers', action='store_true',
                        help='Display count of ascending/descending lines')
    args = parser.parse_args()
    
    cluster_data = pd.read_csv('output_EZ/clustered_data.txt', sep=r'\s+')
    
    marker_file = 'output_EZ/.log2_transformed'
    already_transformed = os.path.exists(marker_file)
    
    use_log2 = args.log2
    if use_log2 and not already_transformed:
        print("Applying log2 transformation...")
        cluster_data['X'], _ = apply_log2_transform(cluster_data['X'])
        cluster_data['Y'], _ = apply_log2_transform(cluster_data['Y'])
    elif use_log2 and already_transformed:
        print("Data already log2 transformed in preparation step, skipping transformation.")
    
    if args.output_prefix:
        base_name = f'output_EZ/{args.output_prefix}_slopegraph'
    else:
        base_name = 'output_EZ/slopegraph'
    if use_log2:
        base_name += '_log2'
    if args.output:
        output_filename = args.output
    else:
        output_filename = f'{base_name}.{args.format}'
    
    total_pairs = len(cluster_data)
    differences = cluster_data['Y'] - cluster_data['X']
    positive_count = int((differences > 0).sum())
    negative_count = int((differences < 0).sum())
    tie_count = int((differences == 0).sum())
    
    positive_pct = 100 * positive_count / total_pairs
    negative_pct = 100 * negative_count / total_pairs
    tie_pct = 100 * tie_count / total_pairs
    
    print(f"Total pairs: {total_pairs}")
    print(f"Ascending (Y > X): {positive_count} ({positive_pct:.1f}%)")
    print(f"Descending (Y < X): {negative_count} ({negative_pct:.1f}%)")
    print(f"No change (tie): {tie_count} ({tie_pct:.1f}%)")
    
    if args.no_outliers:
        x_data = cluster_data['X'].values
        y_data = cluster_data['Y'].values
        q1_x, q3_x = np.percentile(x_data, [25, 75])
        q1_y, q3_y = np.percentile(y_data, [25, 75])
        iqr_x, iqr_y = q3_x - q1_x, q3_y - q1_y
        lower_x, upper_x = q1_x - 1.5 * iqr_x, q3_x + 1.5 * iqr_x
        lower_y, upper_y = q1_y - 1.5 * iqr_y, q3_y + 1.5 * iqr_y
        
        mask = (cluster_data['X'] >= lower_x) & (cluster_data['X'] <= upper_x) & \
               (cluster_data['Y'] >= lower_y) & (cluster_data['Y'] <= upper_y)
        plot_data = cluster_data[mask].copy()
        filtered_count = len(cluster_data) - len(plot_data)
        if filtered_count > 0:
            print(f"Filtered out {filtered_count} data points outside whisker range for plotting")
    else:
        plot_data = cluster_data
    
    stats = {
        'total_pairs': total_pairs,
        'ascending_count': positive_count,
        'ascending_pct': positive_pct,
        'descending_count': negative_count,
        'descending_pct': negative_pct,
        'tie_count': tie_count,
        'tie_pct': tie_pct,
        'log2_transformed': use_log2,
        'no_outliers': args.no_outliers
    }
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    x_pos = 1.0
    y_pos = 2.0
    
    lines_data = []
    
    for _, row in plot_data.iterrows():
        x_val = row['X']
        y_val = row['Y']
        diff = y_val - x_val
        
        if diff > 0:
            color = 'green'
            direction = 'ascending'
        elif diff < 0:
            color = 'red'
            direction = 'descending'
        else:
            color = 'gray'
            direction = 'tie'
        
        ax.plot([x_pos, y_pos], [x_val, y_val], 
                color=color, alpha=args.alpha, linewidth=args.linewidth, zorder=2)
        
        lines_data.append({
            'x_start': x_pos,
            'x_end': y_pos,
            'y_start': float(x_val),
            'y_end': float(y_val),
            'direction': direction
        })
    
    ax.set_xticks([x_pos, y_pos])
    ax.set_xticklabels(['X', 'Y'], fontsize=12)
    ax.set_xlim(x_pos - 0.5, y_pos + 0.5)
    
    title = 'Slope Graph'
    if use_log2:
        title += ' (log2 scale)'
    ax.set_title(title, fontsize=14)
    
    ylabel = 'log2(Value)' if use_log2 else 'Value'
    ax.set_ylabel(ylabel, fontsize=12)
    
    ax.grid(True, linestyle='--', alpha=0.3)
    
    if args.show_numbers:
        y_min, y_max = ax.get_ylim()
        text_y = y_max - 0.03 * (y_max - y_min)
        line_height = 0.05 * (y_max - y_min)
        
        ax.text(y_pos + 0.15, text_y, f'Ascending: {positive_count} ({positive_pct:.1f}%)', 
                fontsize=10, color='green', verticalalignment='top')
        ax.text(y_pos + 0.15, text_y - line_height, f'Descending: {negative_count} ({negative_pct:.1f}%)', 
                fontsize=10, color='red', verticalalignment='top')
        if tie_count > 0:
            ax.text(y_pos + 0.15, text_y - 2 * line_height, f'Tie: {tie_count} ({tie_pct:.1f}%)', 
                    fontsize=10, color='gray', verticalalignment='top')
    
    copyright_text = "Copyright (c) 2025. RIKEN All rights reserved. This is for academic and non-commercial research use only.\nThe technology is currently under patent application. Commercial use is prohibited without a separate license agreement. E-mail: akihiro.ezoe@riken.jp"
    plt.figtext(0.5, 0.01, copyright_text, ha='center', fontsize=8, color='black')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)
    
    if args.format == 'json':
        export_json(output_filename, lines_data, stats)
    elif args.format == 'html':
        svg_buffer = io.StringIO()
        plt.savefig(svg_buffer, format='svg')
        svg_content = svg_buffer.getvalue()
        svg_content = svg_content[svg_content.find('<svg'):]
        export_html(output_filename, svg_content, title)
    elif args.format == 'pdf':
        with PdfPages(output_filename) as pdf:
            pdf.savefig(fig, dpi=300, bbox_inches='tight')
    else:
        plt.savefig(output_filename, format=args.format, dpi=300 if args.format == 'png' else None, bbox_inches='tight')
    
    plt.close()
    
    print(f"Log2 transformation: {use_log2}")
    print(f"Output file: {output_filename}")


if __name__ == "__main__":
    main()
