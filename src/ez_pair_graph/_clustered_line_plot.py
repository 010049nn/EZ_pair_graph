#Copyright (c) 2025. RIKEN All rights reserved.
#This is for academic and non-commercial research use only.
#The technology is currently under patent application.
#Commercial use is prohibited without a separate license agreement.
#E-mail: akihiro.ezoe@riken.jp

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.colors as mcolors
import argparse
import json
import os


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

    outliers = data[(data < lower_whisker) | (data > upper_whisker)]

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
            color=edgecolor, linewidth=1.5, zorder=2)

    cap_width = half_width * 0.4

    if side == 'left':
        cap_left = position - cap_width
        cap_right = position
    else:
        cap_left = position
        cap_right = position + cap_width

    ax.plot([position, position], [whisker_min, q1],
            color=edgecolor, linewidth=1, zorder=1)
    ax.plot([cap_left, cap_right], [whisker_min, whisker_min],
            color=edgecolor, linewidth=1, zorder=1)

    ax.plot([position, position], [q3, whisker_max],
            color=edgecolor, linewidth=1, zorder=1)
    ax.plot([cap_left, cap_right], [whisker_max, whisker_max],
            color=edgecolor, linewidth=1, zorder=1)

    if show_outliers and len(outliers) > 0:
        ax.scatter([position] * len(outliers), outliers,
                   color=edgecolor, marker='o', s=20,
                   edgecolors=edgecolor, facecolors='none', zorder=1)

    return {
        'position': position,
        'side': side,
        'q1': float(q1),
        'median': float(median),
        'q3': float(q3),
        'whisker_min': float(whisker_min),
        'whisker_max': float(whisker_max),
        'outliers': [float(o) for o in outliers],
        'box_left': float(box_left),
        'box_right': float(box_right)
    }


def export_json(output_path, boxplot_data, lines_data, stats):
    json_data = {
        'type': 'clustered_line_plot',
        'statistics': stats,
        'boxplots': boxplot_data,
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


def create_truncated_colormap(cmap_name, vmin=0.3, vmax=1.0):
    cmap = plt.get_cmap(cmap_name)
    colors = cmap(np.linspace(vmin, vmax, 256))
    return LinearSegmentedColormap.from_list(f'trunc_{cmap_name}', colors)


def main():
    parser = argparse.ArgumentParser(description='Generate clustered line plot')
    parser.add_argument('--format', '-f', choices=['pdf', 'svg', 'png', 'html', 'json'],
                        default='pdf', help='Output format (default: pdf)')
    parser.add_argument('--output', '-o', default=None, help='Output filename (optional)')
    parser.add_argument('--output-prefix', default=None, help='Prefix for output filename')
    parser.add_argument('--no-outliers', action='store_true',
                        help='Hide outliers in boxplot')
    parser.add_argument('--log2', action='store_true',
                        help='Apply log2 transformation to values')
    parser.add_argument('--show-numbers', action='store_true',
                        help='Display cluster numbers (g_num) on lines')
    args = parser.parse_args()

    cluster_data = pd.read_csv('output_EZ/clustered_data.txt', sep=r'\s+')
    calculated_points = pd.read_csv('output_EZ/calculated_points.txt', sep=r'\s+')

    marker_file = 'output_EZ/.log2_transformed'
    already_transformed = os.path.exists(marker_file)

    use_log2 = args.log2
    if use_log2 and not already_transformed:
        print("Applying log2 transformation...")
        cluster_data['X'], _ = apply_log2_transform(cluster_data['X'])
        cluster_data['Y'], _ = apply_log2_transform(cluster_data['Y'])
        calculated_points['X_Mean'], _ = apply_log2_transform(calculated_points['X_Mean'])
        calculated_points['Y_Calculated_Mean'], _ = apply_log2_transform(calculated_points['Y_Calculated_Mean'])
    elif use_log2 and already_transformed:
        print("Data already log2 transformed in preparation step, skipping transformation.")

    if args.output_prefix:
        base_name = f'output_EZ/{args.output_prefix}_boxplot_with_lines'
    else:
        base_name = 'output_EZ/boxplot_with_lines'
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

    fig, ax = plt.subplots(figsize=(8, 7))

    x_pos = 1.0
    y_pos = 1.4
    box_width = 0.5
    boxplot_data = []

    show_outliers = not args.no_outliers

    bp_x = draw_half_boxplot(ax, cluster_data['X'], position=x_pos, width=box_width,
                      side='left', facecolor='lightgray', edgecolor='gray',
                      show_outliers=show_outliers)
    bp_x['label'] = 'X'
    boxplot_data.append(bp_x)

    bp_y = draw_half_boxplot(ax, cluster_data['Y'], position=y_pos, width=box_width,
                      side='right', facecolor='lightgray', edgecolor='gray',
                      show_outliers=show_outliers)
    bp_y['label'] = 'Y'
    boxplot_data.append(bp_y)

    calculated_points = calculated_points.sort_values(by='g_num', ascending=True)

    x_whisker_min, x_whisker_max = bp_x['whisker_min'], bp_x['whisker_max']
    y_whisker_min, y_whisker_max = bp_y['whisker_min'], bp_y['whisker_max']

    calculated_points_filtered = calculated_points[
        (calculated_points['X_Mean'] >= x_whisker_min) &
        (calculated_points['X_Mean'] <= x_whisker_max) &
        (calculated_points['Y_Calculated_Mean'] >= y_whisker_min) &
        (calculated_points['Y_Calculated_Mean'] <= y_whisker_max)
    ].copy()

    filtered_count = len(calculated_points) - len(calculated_points_filtered)
    if filtered_count > 0:
        print(f"Filtered out {filtered_count} cluster(s) outside whisker range")

    if len(calculated_points_filtered) == 0:
        print("Warning: All clusters filtered out. Using original data.")
        calculated_points_filtered = calculated_points.copy()

    g_num_min = calculated_points_filtered['g_num'].min()
    g_num_max = calculated_points_filtered['g_num'].max()

    lines_data = []

    for _, row in calculated_points_filtered.iterrows():
        norm_g_num = (row['g_num'] - g_num_min) / (g_num_max - g_num_min) if g_num_max > g_num_min else 0.5

        color = plt.cm.Blues(0.3 + 0.7 * norm_g_num)

        color_hex = '#{:02x}{:02x}{:02x}'.format(int(color[0]*255), int(color[1]*255), int(color[2]*255))

        line_width = 1 + 4 * norm_g_num

        ax.plot([x_pos, y_pos], [row['X_Mean'], row['Y_Calculated_Mean']],
                 color=color, linewidth=line_width, solid_capstyle='round',
                 zorder=int(10 + 90 * norm_g_num))

        if args.show_numbers:
            mid_x = (x_pos + y_pos) / 2
            mid_y = (row['X_Mean'] + row['Y_Calculated_Mean']) / 2
            ax.text(mid_x, mid_y + 0.02 * (y_whisker_max - y_whisker_min),
                    str(int(row['g_num'])), fontsize=7,
                    color=color, ha='center', va='bottom',
                    zorder=int(10 + 90 * norm_g_num) + 1)

        is_ascending = row['Y_Calculated_Mean'] > row['X_Mean']

        lines_data.append({
            'group': int(row['Group']) if 'Group' in row else None,
            'x_start': x_pos,
            'x_end': y_pos,
            'y_start': float(row['X_Mean']),
            'y_end': float(row['Y_Calculated_Mean']),
            'g_num': int(row['g_num']),
            'direction': 'ascending' if is_ascending else 'descending',
            'color': color_hex,
            'line_width': float(line_width),
            'norm_g_num': float(norm_g_num)
        })

    ax.set_xticks([x_pos, y_pos])
    ax.set_xticklabels(['X', 'Y'])
    ax.set_xlim(x_pos - 0.5, y_pos + 0.5)

    title = 'Boxplot with Calculated Points'
    if use_log2:
        title += ' (log2 scale)'
    ax.set_title(title, pad=30)

    ylabel = 'log2(Value)' if use_log2 else 'Value'
    ax.set_ylabel(ylabel)

    cmap_blue = create_truncated_colormap('Blues', 0.3, 1.0)
    cax_blue = fig.add_axes([0.25, 0.92, 0.5, 0.02])
    norm = mcolors.Normalize(vmin=g_num_min, vmax=g_num_max)
    sm_blue = plt.cm.ScalarMappable(cmap=cmap_blue, norm=norm)
    sm_blue.set_array([])
    cbar_blue = fig.colorbar(sm_blue, cax=cax_blue, orientation='horizontal')
    cbar_blue.set_ticks([g_num_min, g_num_max])
    cbar_blue.set_ticklabels([str(int(g_num_min)), str(int(g_num_max))])
    cbar_blue.ax.set_xlabel('g_num', fontsize=10)
    cbar_blue.ax.tick_params(labelsize=9)

    copyright_text = "Copyright (c) 2025. RIKEN All rights reserved. This is for academic and non-commercial research use only.\nThe technology is currently under patent application. Commercial use is prohibited without a separate license agreement. E-mail: akihiro.ezoe@riken.jp"
    plt.figtext(0.5, 0.01, copyright_text, ha='center', fontsize=8, color='black')

    plt.subplots_adjust(bottom=0.15, top=0.88)

    if args.format == 'json':
        export_json(output_filename, boxplot_data, lines_data, stats)
    elif args.format == 'html':
        import io
        svg_buffer = io.StringIO()
        plt.savefig(svg_buffer, format='svg')
        svg_content = svg_buffer.getvalue()
        svg_content = svg_content[svg_content.find('<svg'):]
        export_html(output_filename, svg_content, title)
    else:
        plt.savefig(output_filename, format=args.format, dpi=300 if args.format == 'png' else None)

    plt.close()

    print(f"Log2 transformation: {use_log2}")
    print(f"Show numbers: {args.show_numbers}")
    print(f"The output file name was {output_filename}.")


if __name__ == "__main__":
    main()
