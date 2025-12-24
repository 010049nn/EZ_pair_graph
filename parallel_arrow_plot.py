import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.patches import Polygon
from matplotlib.backends.backend_pdf import PdfPages

clustered_data = pd.read_csv('output_EZ/clustered_data.txt', sep=' ')
calculated_points = pd.read_csv('output_EZ/calculated_points.txt', sep='\t')

pdf_filename = 'output_EZ/arrow_boxplot_chart.pdf'

with PdfPages(pdf_filename) as pdf:
    fig, ax = plt.subplots(figsize=(11.7, 9.0))

    calculated_points_sorted = calculated_points.sort_values('g_num', ascending=False)

    max_g_num = calculated_points['g_num'].max()
    min_g_num = calculated_points['g_num'].min()

    x_box_pos = 0.3
    y_box_pos = 0.7
    box_positions = [x_box_pos, y_box_pos]
    labels = ['X Values', 'Y Values']

    boxplot = ax.boxplot([clustered_data['X'], clustered_data['Y']],
                        positions=box_positions,
                        widths=0.15,
                        patch_artist=True,
                        labels=labels,
                        showfliers=False,
                        zorder=1)

    for box in boxplot['boxes']:
        box.set(facecolor='lightgray', alpha=0.3)

    for component in ['whiskers', 'caps', 'medians']:
        for item in boxplot[component]:
            item.set(color='gray', alpha=0.5, linewidth=1)

    for item in boxplot['fliers']:
        item.set(marker='o', markerfacecolor='gray', markeredgecolor='gray', alpha=0.5, markersize=4)

    arrow_center_pos = (x_box_pos + y_box_pos) / 2
    arrow_width = 0.15

    num_arrows = len(calculated_points_sorted)

    if num_arrows > 1:
        arrow_positions = np.linspace(
            arrow_center_pos - arrow_width/2,
            arrow_center_pos + arrow_width/2,
            num_arrows
        )
    else:
        arrow_positions = [arrow_center_pos]

    arrow_min = min(calculated_points['X_Mean'].min(), calculated_points['Y_Calculated_Mean'].min())
    arrow_max = max(calculated_points['X_Mean'].max(), calculated_points['Y_Calculated_Mean'].max())

    whisker_values = []
    for whisker in boxplot['whiskers']:
        whisker_data = whisker.get_ydata()
        whisker_values.extend(whisker_data)

    if whisker_values:
        boxplot_min = min(whisker_values)
        boxplot_max = max(whisker_values)
    else:
        boxplot_min = min(clustered_data['X'].quantile(0.25), clustered_data['Y'].quantile(0.25))
        boxplot_max = max(clustered_data['X'].quantile(0.75), clustered_data['Y'].quantile(0.75))

    overall_min = min(arrow_min, boxplot_min)
    overall_max = max(arrow_max, boxplot_max)

    data_range = overall_max - overall_min

    bottom_padding = data_range * 0.1
    top_padding = data_range * 0.1

    y_min = overall_min - bottom_padding
    y_max = overall_max + top_padding

    for i, (_, row) in enumerate(calculated_points_sorted.iterrows()):
        x_mean = row['X_Mean']
        y_mean = row['Y_Calculated_Mean']
        g_num = row['g_num']

        line_width = 1 + 7 * (g_num - min_g_num) / (max_g_num - min_g_num) if max_g_num != min_g_num else 4

        color_val = (g_num - min_g_num) / (max_g_num - min_g_num) if max_g_num != min_g_num else 0.5
        color = mcolors.to_rgba(plt.cm.YlOrRd(color_val))

        z_val = 10 + int(g_num)

        arrow_x = arrow_positions[i]

        triangle_height = data_range * 0.03 
        triangle_width = 0.007 * line_width

        ax.plot([arrow_x, arrow_x], [x_mean, y_mean],
                color=color, linewidth=line_width, zorder=z_val)

        if y_mean > x_mean:
            triangle = Polygon([
                (arrow_x - triangle_width/2, y_mean - triangle_height/2),
                (arrow_x + triangle_width/2, y_mean - triangle_height/2),
                (arrow_x, y_mean + triangle_height/2)
            ], closed=True, facecolor=color, edgecolor=color, zorder=z_val)
            ax.add_patch(triangle)

        else:
            triangle = Polygon([
                (arrow_x - triangle_width/2, y_mean + triangle_height/2),
                (arrow_x + triangle_width/2, y_mean + triangle_height/2),
                (arrow_x, y_mean - triangle_height/2)
            ], closed=True, facecolor=color, edgecolor=color, zorder=z_val)
            ax.add_patch(triangle)

    ax.set_ylim(y_min, y_max)
    ax.set_xlim(0, 1)
    ax.set_xlabel('', fontsize=12)
    ax.set_ylabel('Value', fontsize=12)
    ax.set_title('Changes from X to Y Values with Boxplots', fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.4)

    ax.set_xticks(box_positions)
    ax.set_xticklabels(labels, fontsize=12)

    legend_g_vals = [min_g_num, int((min_g_num + max_g_num) / 2), max_g_num]
    for g_val in legend_g_vals:
        norm_g = (g_val - min_g_num) / (max_g_num - min_g_num) if max_g_num != min_g_num else 0.5
        line_width = 1 + 7 * norm_g
        color = mcolors.to_rgba(plt.cm.YlOrRd(norm_g))
        ax.plot([], [], color=color, linewidth=line_width, label=f'g_num = {g_val}')

    ax.legend(loc='upper right', fontsize=10)

    copyright_text = """Copyright (c) 2025. RIKEN All rights reserved. This is for academic and non-commercial research use only.\nThe technology is currently
under patent application. Commercial use is prohibited without a separate license agreement. E-mail: akihiro.ezoe@riken.jp"""

    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)

    plt.figtext(0.5, 0.02, copyright_text, ha='center', fontsize=8, color='black')

    pdf.savefig(fig, dpi=300, bbox_inches='tight')

    d = pdf.infodict()
    d['Title'] = 'X-Y Value Changes with Boxplots'
    d['Author'] = 'Generated by Python'
    d['Subject'] = 'Data Visualization'
    d['Keywords'] = 'boxplot, arrows, data visualization'
    d['CreationDate'] = pd.Timestamp.now()

plt.show()

print(f"Output file: '{pdf_filename}'")
print(f"\nDebug information:")
print(f"Number of arrows: {len(calculated_points_sorted)}")
print(f"Arrow data range: {arrow_min:.2f} to {arrow_max:.2f}")
print(f"Boxplot range: {boxplot_min:.2f} to {boxplot_max:.2f}")
print(f"Y-axis range: {y_min:.2f} to {y_max:.2f}")
print(f"Triangle height: {data_range * 0.03:.2f}")
