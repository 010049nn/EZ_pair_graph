#Copyright (c) 2025. RIKEN All rights reserved.
#This is for academic and non-commercial research use only.
#The technology is currently under patent application.
#Commercial use is prohibited without a separate license agreement.
#E-mail: akihiro.ezoe@riken.jp

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import matplotlib.colors as mcolors
from matplotlib.patches import Polygon, Rectangle
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LinearSegmentedColormap
import argparse
import json
import io


def apply_log2_transform(data, min_value=1e-10):
    data = np.array(data, dtype=float)
    data = np.where(data <= 0, min_value, data)
    return np.log2(data), 0


def draw_half_boxplot(ax, data, position, width, side='left',
                      facecolor='lightgray', edgecolor='gray', alpha=0.7,
                      show_outliers=True):
    data = np.array(data)

    q1 = np.percentile(data, 25)
    median = np.percentile(data, 50)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1

    lower_whisker = q1 - 1.5 * iqr
    upper_whisker = q3 + 1.5 * iqr

    whisker_min = data[data >= lower_whisker].min()
    whisker_max = data[data <= upper_whisker].max()

    half_width = width / 2

    if side == 'left':
        box_left = position - half_width
        box_right = position
    else:
        box_left = position
        box_right = position + half_width

    box = Rectangle(
        (box_left, q1),
        box_right - box_left,
        q3 - q1,
        facecolor=facecolor,
        edgecolor=edgecolor,
        alpha=alpha,
        linewidth=1,
        zorder=1
    )
    ax.add_patch(box)

    ax.plot([box_left, box_right], [median, median],
            color=edgecolor, linewidth=1.5, alpha=0.7, zorder=2)

    cap_width = half_width * 0.4

    if side == 'left':
        cap_left = position - cap_width
        cap_right = position
    else:
        cap_left = position
        cap_right = position + cap_width

    ax.plot([position, position], [whisker_min, q1],
            color=edgecolor, linewidth=1, alpha=0.5, zorder=1)
    ax.plot([cap_left, cap_right], [whisker_min, whisker_min],
            color=edgecolor, linewidth=1, alpha=0.5, zorder=1)

    ax.plot([position, position], [q3, whisker_max],
            color=edgecolor, linewidth=1, alpha=0.5, zorder=1)
    ax.plot([cap_left, cap_right], [whisker_max, whisker_max],
            color=edgecolor, linewidth=1, alpha=0.5, zorder=1)

    return whisker_min, whisker_max, {
        'position': float(position),
        'side': side,
        'q1': float(q1),
        'median': float(median),
        'q3': float(q3),
        'whisker_min': float(whisker_min),
        'whisker_max': float(whisker_max),
        'box_left': float(box_left),
        'box_right': float(box_right)
    }


def export_json(output_path, boxplot_data, arrows_data, stats, axis_info):
    json_data = {
        'type': 'parallel_arrow_plot',
        'statistics': stats,
        'axis': axis_info,
        'boxplots': boxplot_data,
        'arrows': arrows_data
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


def create_truncated_colormap(cmap_name, vmin=0.3, vmax=1.0):
    cmap = plt.get_cmap(cmap_name)
    colors = cmap(np.linspace(vmin, vmax, 256))
    return LinearSegmentedColormap.from_list(f'trunc_{cmap_name}', colors)


def main():
    parser = argparse.ArgumentParser(description='Generate parallel arrow plot')
    parser.add_argument('--format', '-f', choices=['pdf', 'svg', 'png', 'html', 'json'],
                        default='pdf', help='Output format (default: pdf)')
    parser.add_argument('--output', '-o', default=None, help='Output filename (optional)')
    parser.add_argument('--output-prefix', default=None, help='Prefix for output filename')
    parser.add_argument('--no-outliers', action='store_true',
                        help='Hide outliers in boxplot')
    parser.add_argument('--log2', action='store_true',
                        help='Apply log2 transformation to values')
    parser.add_argument('--show-numbers', action='store_true',
                        help='Display cluster numbers (g_num) on arrows')
    args = parser.parse_args()

    clustered_data = pd.read_csv('output_EZ/clustered_data.txt', sep=' ')
    calculated_points = pd.read_csv('output_EZ/calculated_points.txt', sep='\t')

    marker_file = 'output_EZ/.log2_transformed'
    already_transformed = os.path.exists(marker_file)

    use_log2 = args.log2
    if use_log2 and not already_transformed:
        print("Applying log2 transformation...")
        clustered_data['X'], _ = apply_log2_transform(clustered_data['X'])
        clustered_data['Y'], _ = apply_log2_transform(clustered_data['Y'])
        calculated_points['X_Mean'], _ = apply_log2_transform(calculated_points['X_Mean'])
        calculated_points['Y_Calculated_Mean'], _ = apply_log2_transform(calculated_points['Y_Calculated_Mean'])
    elif use_log2 and already_transformed:
        print("Data already log2 transformed in preparation step, skipping transformation.")

    if args.output_prefix:
        base_name = f'output_EZ/{args.output_prefix}_arrow_boxplot_chart'
    else:
        base_name = 'output_EZ/arrow_boxplot_chart'
    if use_log2:
        base_name += '_log2'
    if args.output:
        output_filename = args.output
    else:
        output_filename = f'{base_name}.{args.format}'

    total_pairs = len(clustered_data)
    differences = clustered_data['Y'] - clustered_data['X']
    positive_count = int((differences > 0).sum())
    negative_count = int((differences < 0).sum())
    tie_count = int((differences == 0).sum())

    positive_pct = 100 * positive_count / total_pairs
    negative_pct = 100 * negative_count / total_pairs
    tie_pct = 100 * tie_count / total_pairs

    print(f"Total pairs: {total_pairs}")
    print(f"Positive differences (ascending): {positive_count} ({positive_pct:.1f}%)")
    print(f"Negative differences (descending): {negative_count} ({negative_pct:.1f}%)")
    print(f"No change (tie): {tie_count} ({tie_pct:.1f}%)")

    stats = {
        'total_pairs': total_pairs,
        'positive_count': positive_count,
        'positive_pct': positive_pct,
        'negative_count': negative_count,
        'negative_pct': negative_pct,
        'tie_count': tie_count,
        'tie_pct': tie_pct,
        'log2_transformed': use_log2
    }

    fig, ax = plt.subplots(figsize=(8, 9.0))

    x_box_pos = 0.35
    y_box_pos = 0.65
    box_width = 0.15
    labels = ['X Values', 'Y Values']

    boxplot_data = []

    show_outliers = not args.no_outliers

    whisker1_min, whisker1_max, bp_x = draw_half_boxplot(
        ax, clustered_data['X'], x_box_pos, box_width,
        side='left', facecolor='lightgray', edgecolor='gray', alpha=0.7,
        show_outliers=show_outliers
    )
    bp_x['label'] = 'X'
    boxplot_data.append(bp_x)

    whisker2_min, whisker2_max, bp_y = draw_half_boxplot(
        ax, clustered_data['Y'], y_box_pos, box_width,
        side='right', facecolor='lightgray', edgecolor='gray', alpha=0.7,
        show_outliers=show_outliers
    )
    bp_y['label'] = 'Y'
    boxplot_data.append(bp_y)

    calculated_points_filtered = calculated_points[
        (calculated_points['X_Mean'] >= whisker1_min) &
        (calculated_points['X_Mean'] <= whisker1_max) &
        (calculated_points['Y_Calculated_Mean'] >= whisker2_min) &
        (calculated_points['Y_Calculated_Mean'] <= whisker2_max)
    ].copy()

    filtered_count = len(calculated_points) - len(calculated_points_filtered)
    if filtered_count > 0:
        print(f"Filtered out {filtered_count} cluster(s) outside whisker range")

    if len(calculated_points_filtered) == 0:
        print("Warning: All clusters filtered out. Using original data.")
        calculated_points_filtered = calculated_points.copy()

    calculated_points_sorted = calculated_points_filtered.sort_values('g_num', ascending=False)
    max_g_num = calculated_points_filtered['g_num'].max()
    min_g_num = calculated_points_filtered['g_num'].min()

    arrow_center_pos = (x_box_pos + y_box_pos) / 2
    arrow_width = 0.15
    arrow_gap = 0.02

    ascending_points = calculated_points_sorted[
        calculated_points_sorted['Y_Calculated_Mean'] > calculated_points_sorted['X_Mean']
    ].copy()
    descending_points = calculated_points_sorted[
        calculated_points_sorted['Y_Calculated_Mean'] <= calculated_points_sorted['X_Mean']
    ].copy()

    num_ascending = len(ascending_points)
    num_descending = len(descending_points)

    half_width = (arrow_width - arrow_gap) / 2

    if num_ascending > 1:
        ascending_positions = np.linspace(
            arrow_center_pos - arrow_width/2,
            arrow_center_pos - arrow_gap/2,
            num_ascending
        )
    elif num_ascending == 1:
        ascending_positions = [arrow_center_pos - arrow_width/4]
    else:
        ascending_positions = []

    if num_descending > 1:
        descending_positions = np.linspace(
            arrow_center_pos + arrow_gap/2,
            arrow_center_pos + arrow_width/2,
            num_descending
        )
    elif num_descending == 1:
        descending_positions = [arrow_center_pos + arrow_width/4]
    else:
        descending_positions = []

    arrow_min = min(calculated_points_filtered['X_Mean'].min(), calculated_points_filtered['Y_Calculated_Mean'].min())
    arrow_max = max(calculated_points_filtered['X_Mean'].max(), calculated_points_filtered['Y_Calculated_Mean'].max())

    boxplot_min = min(whisker1_min, whisker2_min)
    boxplot_max = max(whisker1_max, whisker2_max)

    overall_min = min(arrow_min, boxplot_min)
    overall_max = max(arrow_max, boxplot_max)

    data_range = overall_max - overall_min

    bottom_padding = data_range * 0.1
    top_padding = data_range * 0.1

    y_min = overall_min - bottom_padding
    y_max = overall_max + top_padding

    arrows_data = []

    for i, (_, row) in enumerate(ascending_points.iterrows()):
        x_mean = row['X_Mean']
        y_mean = row['Y_Calculated_Mean']
        g_num = row['g_num']

        line_width = 1 + 7 * (g_num - min_g_num) / (max_g_num - min_g_num) if max_g_num != min_g_num else 4

        color_val = (g_num - min_g_num) / (max_g_num - min_g_num) if max_g_num != min_g_num else 0.5

        color = mcolors.to_rgba(plt.cm.Blues(0.3 + 0.7 * color_val))

        color_hex = '#{:02x}{:02x}{:02x}'.format(int(color[0]*255), int(color[1]*255), int(color[2]*255))

        z_val = 10 + int(g_num)

        arrow_x = ascending_positions[i]

        triangle_height = data_range * 0.03
        triangle_width = 0.007 * line_width

        ax.plot([arrow_x, arrow_x], [x_mean, y_mean],
                color=color, linewidth=line_width, zorder=z_val)

        triangle = Polygon([
            (arrow_x - triangle_width/2, y_mean - triangle_height/2),
            (arrow_x + triangle_width/2, y_mean - triangle_height/2),
            (arrow_x, y_mean + triangle_height/2)
        ], closed=True, facecolor=color, edgecolor=color, zorder=z_val)
        ax.add_patch(triangle)

        if args.show_numbers:
            mid_y = (x_mean + y_mean) / 2
            text_x = arrow_x - 0.02
            ax.text(text_x, mid_y, str(int(g_num)), fontsize=7,
                    color=color, ha='right', va='center', zorder=z_val + 1)

        arrows_data.append({
            'group': int(row['Group']) if 'Group' in row else None,
            'x_position': float(arrow_x),
            'y_start': float(x_mean),
            'y_end': float(y_mean),
            'g_num': int(g_num),
            'direction': 'up',
            'color': color_hex,
            'line_width': float(line_width),
            'triangle_height': float(triangle_height),
            'triangle_width': float(triangle_width)
        })

    for i, (_, row) in enumerate(descending_points.iterrows()):
        x_mean = row['X_Mean']
        y_mean = row['Y_Calculated_Mean']
        g_num = row['g_num']

        line_width = 1 + 7 * (g_num - min_g_num) / (max_g_num - min_g_num) if max_g_num != min_g_num else 4

        color_val = (g_num - min_g_num) / (max_g_num - min_g_num) if max_g_num != min_g_num else 0.5

        color = mcolors.to_rgba(plt.cm.Blues(0.3 + 0.7 * color_val))

        color_hex = '#{:02x}{:02x}{:02x}'.format(int(color[0]*255), int(color[1]*255), int(color[2]*255))

        z_val = 10 + int(g_num)

        arrow_x = descending_positions[i]

        triangle_height = data_range * 0.03
        triangle_width = 0.007 * line_width

        ax.plot([arrow_x, arrow_x], [x_mean, y_mean],
                color=color, linewidth=line_width, zorder=z_val)

        triangle = Polygon([
            (arrow_x - triangle_width/2, y_mean + triangle_height/2),
            (arrow_x + triangle_width/2, y_mean + triangle_height/2),
            (arrow_x, y_mean - triangle_height/2)
        ], closed=True, facecolor=color, edgecolor=color, zorder=z_val)
        ax.add_patch(triangle)

        if args.show_numbers:
            mid_y = (x_mean + y_mean) / 2
            text_x = arrow_x + 0.02
            ax.text(text_x, mid_y, str(int(g_num)), fontsize=7,
                    color=color, ha='left', va='center', zorder=z_val + 1)

        arrows_data.append({
            'group': int(row['Group']) if 'Group' in row else None,
            'x_position': float(arrow_x),
            'y_start': float(x_mean),
            'y_end': float(y_mean),
            'g_num': int(g_num),
            'direction': 'down',
            'color': color_hex,
            'line_width': float(line_width),
            'triangle_height': float(triangle_height),
            'triangle_width': float(triangle_width)
        })

    ax.set_ylim(y_min, y_max)
    ax.set_xlim(0, 1)
    ax.set_xlabel('', fontsize=12)

    ylabel = 'log2(Value)' if use_log2 else 'Value'
    ax.set_ylabel(ylabel, fontsize=12)

    title = 'Changes from X to Y Values with Boxplots'
    if use_log2:
        title += ' (log2 scale)'
    ax.set_title(title, fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.4)

    ax.set_xticks([x_box_pos, y_box_pos])
    ax.set_xticklabels(labels, fontsize=12)

    cmap_blue = create_truncated_colormap('Blues', 0.3, 1.0)

    cax_blue = fig.add_axes([0.92, 0.35, 0.02, 0.35])
    norm = mcolors.Normalize(vmin=min_g_num, vmax=max_g_num)
    sm_blue = plt.cm.ScalarMappable(cmap=cmap_blue, norm=norm)
    sm_blue.set_array([])
    cbar_blue = fig.colorbar(sm_blue, cax=cax_blue)
    cbar_blue.set_ticks([min_g_num, max_g_num])
    cbar_blue.set_ticklabels([str(int(min_g_num)), str(int(max_g_num))])
    cbar_blue.ax.set_title('g_num', fontsize=10, pad=5)
    cbar_blue.ax.tick_params(labelsize=9)

    copyright_text = """Copyright (c) 2025. RIKEN All rights reserved. This is for academic and non-commercial research use only.
The technology is currently under patent application. Commercial use is prohibited without a separate license agreement. E-mail: akihi
ro.ezoe@riken.jp"""

    plt.subplots_adjust(left=0.1, right=0.88, top=0.9, bottom=0.15)
    plt.figtext(0.5, 0.02, copyright_text, ha='center', fontsize=8, color='black')

    axis_info = {
        'x_min': 0,
        'x_max': 1,
        'y_min': float(y_min),
        'y_max': float(y_max),
        'x_box_pos': float(x_box_pos),
        'y_box_pos': float(y_box_pos),
        'log2_transformed': use_log2
    }

    if args.format == 'json':
        export_json(output_filename, boxplot_data, arrows_data, stats, axis_info)
    elif args.format == 'html':
        svg_buffer = io.StringIO()
        plt.savefig(svg_buffer, format='svg', bbox_inches='tight')
        svg_content = svg_buffer.getvalue()
        svg_content = svg_content[svg_content.find('<svg'):]
        export_html(output_filename, svg_content, title)
    elif args.format == 'pdf':
        with PdfPages(output_filename) as pdf:
            pdf.savefig(fig, dpi=300, bbox_inches='tight')
            d = pdf.infodict()
            d['Title'] = 'X-Y Value Changes with Boxplots'
            d['Author'] = 'Generated by Python'
            d['Subject'] = 'Data Visualization'
            d['Keywords'] = 'boxplot, arrows, data visualization'
            d['CreationDate'] = pd.Timestamp.now()
    else:
        plt.savefig(output_filename, format=args.format, dpi=300 if args.format == 'png' else None, bbox_inches='tight')

    plt.close()

    print(f"Output file: '{output_filename}'")
    print(f"\nDebug information:")
    print(f"Log2 transformation: {use_log2}")
    print(f"Show numbers: {args.show_numbers}")
    print(f"Number of arrows: {len(calculated_points_sorted)} (ascending: {num_ascending}, descending: {num_descending})")
    print(f"Arrow data range: {arrow_min:.2f} to {arrow_max:.2f}")
    print(f"Boxplot range: {boxplot_min:.2f} to {boxplot_max:.2f}")
    print(f"Y-axis range: {y_min:.2f} to {y_max:.2f}")
    print(f"Triangle height: {data_range * 0.03:.2f}")


if __name__ == "__main__":
    main()
