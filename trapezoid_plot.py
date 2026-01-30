#Copyright (c) 2025. RIKEN All rights reserved.
#This is for academic and non-commercial research use only.
#The technology is currently under patent application.
#Commercial use is prohibited without a separate license agreement.
#E-mail: akihiro.ezoe@riken.jp

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
import pandas as pd
import os
import sys
import argparse
import json
import io


def apply_log2_transform(data, min_value=1e-10):
    data = np.array(data, dtype=float)
    data = np.where(data <= 0, min_value, data)
    return np.log2(data), 0


def calculate_quartiles(length):
    if length == 0:
        return None, None, None
    
    q1_idx = int(length / 4)
    q2_idx = int(length / 2)
    q3_idx = int(length * 3 / 4)
    
    return q1_idx, q2_idx, q3_idx


def check_outliers_extent(data):
    if not data or len(data) <= 4:
        return False
    
    if isinstance(data[0], list):
        flat_data = []
        for sublist in data:
            flat_data.extend(sublist)
        data = flat_data
    
    sorted_data = sorted(data)
    
    n = len(sorted_data)
    q1_idx = int(n / 4)
    q3_idx = int(3 * n / 4)
    
    q1 = sorted_data[q1_idx]
    q3 = sorted_data[q3_idx]
    
    iqr = q3 - q1
    lower_threshold = q1 - 1.5 * iqr
    upper_threshold = q3 + 1.5 * iqr
    
    outliers = [x for x in sorted_data if x < lower_threshold or x > upper_threshold]
    
    if not outliers:
        return False
    
    data_range = max(sorted_data) - min(sorted_data)
    
    outlier_min = min(outliers)
    outlier_max = max(outliers)
    
    non_outliers = [x for x in sorted_data if lower_threshold <= x <= upper_threshold]
    non_outlier_min = min(non_outliers) if non_outliers else min(sorted_data)
    non_outlier_max = max(non_outliers) if non_outliers else max(sorted_data)
    
    outlier_extent = 0
    if outlier_min < non_outlier_min:
        outlier_extent += non_outlier_min - outlier_min
    if outlier_max > non_outlier_max:
        outlier_extent += outlier_max - non_outlier_max
    
    return outlier_extent > data_range / 3


def get_whisker_range(data):
    sorted_data = sorted(data)
    q1 = np.percentile(sorted_data, 25)
    q3 = np.percentile(sorted_data, 75)
    iqr = q3 - q1
    
    lower_whisker = q1 - 1.5 * iqr
    upper_whisker = q3 + 1.5 * iqr
    
    whisker_min = min([x for x in sorted_data if x >= lower_whisker])
    whisker_max = max([x for x in sorted_data if x <= upper_whisker])
    
    return whisker_min, whisker_max


def export_json(output_path, boxplot_data, bands_data, quartile_lines_data, stats):
    json_data = {
        'type': 'trapezoid_plot',
        'statistics': stats,
        'boxplots': boxplot_data,
        'quartile_bands': bands_data,
        'quartile_lines': quartile_lines_data
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


def create_visualization(sabun_up, sabun_tie, sabun_down, sorted_sabun_up, sorted_sabun_down, 
                         num_up_total, num_down_total, num_tie_total,
                         output_filename, output_format, no_outliers=False, use_log2=False, show_numbers=False):
    fig, ax = plt.subplots(figsize=(8, 8))
    
    x_pos = 1.0
    y_pos = 1.4
    
    all_data = [
        [item[0] for item in sorted_sabun_up + sorted_sabun_down + sabun_tie], 
        [item[1] for item in sorted_sabun_up + sorted_sabun_down + sabun_tie]
    ]
    
    hide_outliers = check_outliers_extent([item for sublist in all_data for item in sublist])
    
    gray_color = 'gray'
    
    bp = ax.boxplot(all_data, positions=[x_pos, y_pos], widths=0.35,
                    tick_labels=['Group1', 'Group2'], showfliers=False,
                    medianprops=dict(color=gray_color),
                    whiskerprops=dict(color=gray_color),
                    capprops=dict(color=gray_color),
                    boxprops=dict(color=gray_color),
                    patch_artist=True)
    
    for patch in bp['boxes']:
        patch.set_facecolor('lightgray')
        patch.set_edgecolor(gray_color)
        patch.set_alpha(0.8)
    
    whisker1_min, whisker1_max = get_whisker_range(all_data[0])
    whisker2_min, whisker2_max = get_whisker_range(all_data[1])
    
    y_min, y_max = ax.get_ylim()
    
    rect1 = Rectangle((x_pos, y_min), 0.35, y_max - y_min, 
                       facecolor='white', edgecolor='none', zorder=5)
    ax.add_patch(rect1)
    
    rect2 = Rectangle((y_pos - 0.35, y_min), 0.35, y_max - y_min, 
                       facecolor='white', edgecolor='none', zorder=5)
    ax.add_patch(rect2)
    
    ax.plot([x_pos, x_pos], [whisker1_min, whisker1_max], color=gray_color, linewidth=1, zorder=6)
    ax.plot([y_pos, y_pos], [whisker2_min, whisker2_max], color=gray_color, linewidth=1, zorder=6)
    
    if no_outliers:
        data0 = np.array(all_data[0])
        data1 = np.array(all_data[1])
        q1_0, q3_0 = np.percentile(data0, [25, 75])
        q1_1, q3_1 = np.percentile(data1, [25, 75])
        iqr_0, iqr_1 = q3_0 - q1_0, q3_1 - q1_1
        lower_0, upper_0 = q1_0 - 1.5 * iqr_0, q3_0 + 1.5 * iqr_0
        lower_1, upper_1 = q1_1 - 1.5 * iqr_1, q3_1 + 1.5 * iqr_1
        
        sorted_sabun_up = [item for item in sorted_sabun_up 
                          if lower_0 <= item[0] <= upper_0 and lower_1 <= item[1] <= upper_1]
        sorted_sabun_down = [item for item in sorted_sabun_down 
                            if lower_0 <= item[0] <= upper_0 and lower_1 <= item[1] <= upper_1]
        sabun_up = [item for item in sabun_up 
                   if lower_0 <= item[0] <= upper_0 and lower_1 <= item[1] <= upper_1]
        sabun_down = [item for item in sabun_down 
                     if lower_0 <= item[0] <= upper_0 and lower_1 <= item[1] <= upper_1]
        
        filtered_up = num_up_total - len(sabun_up)
        filtered_down = num_down_total - len(sabun_down)
        if filtered_up > 0 or filtered_down > 0:
            print(f"Filtered out {filtered_up} ascending and {filtered_down} descending points outside whisker range")
    
    num_up_display = num_up_total
    num_down_display = num_down_total
    total = num_up_total + num_down_total + num_tie_total
    
    up_width = 1 + 5 * num_up_display / total if total > 0 else 1
    down_width = 1 + 5 * num_down_display / total if total > 0 else 1
    
    up_alpha = 0.3 + 0.7 * num_up_display / total if total > 0 else 0.3
    down_alpha = 0.3 + 0.7 * num_down_display / total if total > 0 else 0.3
    
    up_color_intensity = 0.3 + 0.7 * num_up_display / total if total > 0 else 0.3
    down_color_intensity = 0.3 + 0.7 * num_down_display / total if total > 0 else 0.3
    
    up_zorder = 10 + int(10 * num_up_display / total) if total > 0 else 10
    down_zorder = 10 + int(10 * num_down_display / total) if total > 0 else 10
    
    print(f"Line widths - Up: {up_width}, Down: {down_width}")
    print(f"Line alphas - Up: {up_alpha:.2f}, Down: {down_alpha:.2f}")
    print(f"Color intensities - Up: {up_color_intensity:.2f}, Down: {down_color_intensity:.2f}")
    print(f"Hiding outliers: {hide_outliers}")
    
    boxplot_data = [
        {
            'label': 'Group1 (X)',
            'position': x_pos,
            'whisker_min': float(whisker1_min),
            'whisker_max': float(whisker1_max),
            'q1': float(np.percentile(all_data[0], 25)),
            'median': float(np.percentile(all_data[0], 50)),
            'q3': float(np.percentile(all_data[0], 75)),
            'data_points': [float(x) for x in all_data[0]]
        },
        {
            'label': 'Group2 (Y)',
            'position': y_pos,
            'whisker_min': float(whisker2_min),
            'whisker_max': float(whisker2_max),
            'q1': float(np.percentile(all_data[1], 25)),
            'median': float(np.percentile(all_data[1], 50)),
            'q3': float(np.percentile(all_data[1], 75)),
            'data_points': [float(x) for x in all_data[1]]
        }
    ]
    
    bands_data = []
    quartile_lines_data = []
    
    if sabun_up:
        num_up_filtered = len(sorted_sabun_up)
        q1_idx, q2_idx, q3_idx = calculate_quartiles(num_up_filtered)
        
        sorted_by_slope_up = sorted(sabun_up.copy(), key=lambda x: x[2], reverse=True)
        
        q1_start = sorted_sabun_up[q1_idx][0]
        q1_diff = sorted_by_slope_up[q1_idx][2]
        q1_end = q1_start + q1_diff
        
        q2_start = sorted_sabun_up[q2_idx][0]
        q2_diff = sorted_by_slope_up[q2_idx][2]
        q2_end = q2_start + q2_diff
        
        q3_start = sorted_sabun_up[q3_idx][0]
        q3_diff = sorted_by_slope_up[q3_idx][2]
        q3_end = q3_start + q3_diff
        
        up_line_color = (0, up_color_intensity, 0)
        ax.plot([x_pos, y_pos], [q1_start, q1_end], color=up_line_color, linestyle=':', linewidth=2, alpha=up_alpha, zorder=up_zorder)
        ax.plot([x_pos, y_pos], [q2_start, q2_end], color=up_line_color, linestyle='-', linewidth=up_width, alpha=up_alpha, zorder=up_zorder)
        ax.plot([x_pos, y_pos], [q3_start, q3_end], color=up_line_color, linestyle=':', linewidth=2, alpha=up_alpha, zorder=up_zorder)
        
        x_coords = [x_pos, y_pos, y_pos, x_pos]
        y_coords = [q1_start, q1_end, q3_end, q3_start]
        ax.fill(x_coords, y_coords, color='green', alpha=0.2, zorder=8)
        
        if show_numbers:
            mid_x = (x_pos + y_pos) / 2
            mid_y = (q2_start + q2_end) / 2
            text_y = mid_y + 0.05 * (whisker1_max - whisker1_min)
            ax.text(mid_x, text_y, f'n={num_up_display}', fontsize=9, 
                    color=up_line_color, ha='center', va='bottom', 
                    fontweight='bold', zorder=up_zorder + 1)
        
        bands_data.append({
            'group': 'up',
            'num_samples': num_up_display,
            'num_samples_filtered': num_up_filtered,
            'color': 'green',
            'vertices': [
                {'x': x_pos, 'y': float(q1_start)},
                {'x': y_pos, 'y': float(q1_end)},
                {'x': y_pos, 'y': float(q3_end)},
                {'x': x_pos, 'y': float(q3_start)}
            ]
        })
        
        quartile_lines_data.append({
            'group': 'up',
            'quartile': 'Q1',
            'x_start': x_pos, 'y_start': float(q1_start),
            'x_end': y_pos, 'y_end': float(q1_end),
            'style': 'dotted', 'color': f'rgb(0, {int(up_color_intensity*255)}, 0)', 'width': 2
        })
        quartile_lines_data.append({
            'group': 'up',
            'quartile': 'Q2 (median)',
            'x_start': x_pos, 'y_start': float(q2_start),
            'x_end': y_pos, 'y_end': float(q2_end),
            'style': 'solid', 'color': f'rgb(0, {int(up_color_intensity*255)}, 0)', 
            'color_intensity': float(up_color_intensity),
            'width': float(up_width), 'alpha': float(up_alpha)
        })
        quartile_lines_data.append({
            'group': 'up',
            'quartile': 'Q3',
            'x_start': x_pos, 'y_start': float(q3_start),
            'x_end': y_pos, 'y_end': float(q3_end),
            'style': 'dotted', 'color': f'rgb(0, {int(up_color_intensity*255)}, 0)', 'width': 2
        })
    
    if sabun_down:
        num_down_filtered = len(sorted_sabun_down)
        q1_idx, q2_idx, q3_idx = calculate_quartiles(num_down_filtered)
        
        sorted_by_slope_down = sorted(sabun_down.copy(), key=lambda x: x[2], reverse=False)
        
        q1_start = sorted_sabun_down[q1_idx][0]
        q1_diff = sorted_by_slope_down[q1_idx][2]
        q1_end = q1_start + q1_diff
        
        q2_start = sorted_sabun_down[q2_idx][0]
        q2_diff = sorted_by_slope_down[q2_idx][2]
        q2_end = q2_start + q2_diff
        
        q3_start = sorted_sabun_down[q3_idx][0]
        q3_diff = sorted_by_slope_down[q3_idx][2]
        q3_end = q3_start + q3_diff
        
        down_line_color = (down_color_intensity, 0, 0)
        ax.plot([x_pos, y_pos], [q1_start, q1_end], color=down_line_color, linestyle=':', linewidth=2, alpha=down_alpha, zorder=down_zorder)
        ax.plot([x_pos, y_pos], [q2_start, q2_end], color=down_line_color, linestyle='-', linewidth=down_width, alpha=down_alpha, zorder=down_zorder)
        ax.plot([x_pos, y_pos], [q3_start, q3_end], color=down_line_color, linestyle=':', linewidth=2, alpha=down_alpha, zorder=down_zorder)
        
        x_coords = [x_pos, y_pos, y_pos, x_pos]
        y_coords = [q1_start, q1_end, q3_end, q3_start]
        ax.fill(x_coords, y_coords, color='red', alpha=0.2, zorder=8)
        
        if show_numbers:
            mid_x = (x_pos + y_pos) / 2
            mid_y = (q2_start + q2_end) / 2
            text_y = mid_y - 0.05 * (whisker1_max - whisker1_min)
            ax.text(mid_x, text_y, f'n={num_down_display}', fontsize=9, 
                    color=down_line_color, ha='center', va='top', 
                    fontweight='bold', zorder=down_zorder + 1)
        
        bands_data.append({
            'group': 'down',
            'num_samples': num_down_display,
            'num_samples_filtered': num_down_filtered,
            'color': 'red',
            'vertices': [
                {'x': x_pos, 'y': float(q1_start)},
                {'x': y_pos, 'y': float(q1_end)},
                {'x': y_pos, 'y': float(q3_end)},
                {'x': x_pos, 'y': float(q3_start)}
            ]
        })
        
        quartile_lines_data.append({
            'group': 'down',
            'quartile': 'Q1',
            'x_start': x_pos, 'y_start': float(q1_start),
            'x_end': y_pos, 'y_end': float(q1_end),
            'style': 'dotted', 'color': f'rgb({int(down_color_intensity*255)}, 0, 0)', 'width': 2
        })
        quartile_lines_data.append({
            'group': 'down',
            'quartile': 'Q2 (median)',
            'x_start': x_pos, 'y_start': float(q2_start),
            'x_end': y_pos, 'y_end': float(q2_end),
            'style': 'solid', 'color': f'rgb({int(down_color_intensity*255)}, 0, 0)',
            'color_intensity': float(down_color_intensity),
            'width': float(down_width), 'alpha': float(down_alpha)
        })
        quartile_lines_data.append({
            'group': 'down',
            'quartile': 'Q3',
            'x_start': x_pos, 'y_start': float(q3_start),
            'x_end': y_pos, 'y_end': float(q3_end),
            'style': 'dotted', 'color': f'rgb({int(down_color_intensity*255)}, 0, 0)', 'width': 2
        })
    
    title = 'Trapezoid Plot'
    if use_log2:
        title += ' (log2 scale)'
    plt.title(title)
    
    ylabel = 'log2(Value)' if use_log2 else 'Value'
    plt.ylabel(ylabel)
    ax.set_xlim(x_pos - 0.4, y_pos + 0.4)
    
    copyright_text = "Copyright (c) 2025. RIKEN All rights reserved. This is for academic and non-commercial research use only.\nThe technology is currently under patent application. Commercial use is prohibited without a separate license agreement. E-mail: akihiro.ezoe@riken.jp"
    plt.figtext(0.5, 0.01, copyright_text, ha='center', fontsize=8, wrap=True)
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    
    stats = {
        'num_up': num_up_display,
        'num_down': num_down_display,
        'total': total,
        'up_width': float(up_width),
        'down_width': float(down_width),
        'up_alpha': float(up_alpha),
        'down_alpha': float(down_alpha),
        'up_color_intensity': float(up_color_intensity),
        'down_color_intensity': float(down_color_intensity),
        'hide_outliers': hide_outliers,
        'no_outliers_option': no_outliers,
        'log2_transformed': use_log2,
        'show_numbers': show_numbers
    }
    
    if output_format == 'json':
        export_json(output_filename, boxplot_data, bands_data, quartile_lines_data, stats)
    elif output_format == 'html':
        svg_buffer = io.StringIO()
        plt.savefig(svg_buffer, format='svg')
        svg_content = svg_buffer.getvalue()
        svg_content = svg_content[svg_content.find('<svg'):]
        export_html(output_filename, svg_content, title)
    elif output_format == 'pdf':
        with PdfPages(output_filename) as pdf:
            pdf.savefig(fig)
    else:
        plt.savefig(output_filename, format=output_format, dpi=300 if output_format == 'png' else None)
    
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Generate trapezoid plot')
    parser.add_argument('--format', '-f', choices=['pdf', 'svg', 'png', 'html', 'json'],
                        default='pdf', help='Output format (default: pdf)')
    parser.add_argument('--output', '-o', default=None, help='Output filename (optional)')
    parser.add_argument('--output-prefix', default=None, help='Prefix for output filename')
    parser.add_argument('--no-outliers', action='store_true', 
                        help='Hide outliers (data points outside whiskers)')
    parser.add_argument('--log2', action='store_true',
                        help='Apply log2 transformation to values')
    parser.add_argument('--show-numbers', action='store_true',
                        help='Display sample counts (n) for up/down groups')
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
    
    sabun_up = []
    sabun_tie = []
    sabun_down = []
    
    for _, row in cluster_data.iterrows():
        val1 = row['X']
        val2 = row['Y']
        diff = val2 - val1
        
        if diff > 0:
            sabun_up.append([val1, val2, diff])
        elif diff == 0:
            sabun_tie.append([val1, val2, diff])
        else:
            sabun_down.append([val1, val2, diff])
    
    sorted_sabun_up = sorted(sabun_up.copy(), key=lambda x: x[0], reverse=True)
    sorted_sabun_down = sorted(sabun_down.copy(), key=lambda x: x[0], reverse=True)
    
    num_up_total = len(sabun_up)
    num_down_total = len(sabun_down)
    num_tie_total = len(sabun_tie)
    
    os.makedirs("output_EZ", exist_ok=True)
    
    if args.output_prefix:
        base_name = f'output_EZ/{args.output_prefix}_trapezoid'
    else:
        base_name = 'output_EZ/trapezoid'
    if use_log2:
        base_name += '_log2'
    if args.output:
        output_filename = args.output
    else:
        output_filename = f'{base_name}.{args.format}'
    
    create_visualization(sabun_up, sabun_tie, sabun_down, sorted_sabun_up, sorted_sabun_down, 
                        num_up_total, num_down_total, num_tie_total,
                        output_filename, args.format, args.no_outliers, use_log2, args.show_numbers)
    
    print(f"Log2 transformation: {use_log2}")
    print(f"Show numbers: {args.show_numbers}")
    print(f"No outliers: {args.no_outliers}")
    print(f"Done. Output file: {output_filename}")


if __name__ == "__main__":
    main()
