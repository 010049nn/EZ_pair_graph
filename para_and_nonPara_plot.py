"""
Copyright (c) 2025. RIKEN All rights reserved. This is for academic and non-commercial research use only.
The technology is currently under patent application. Commercial use is prohibited without a separate license agreement. 
E-mail: akihiro.ezoe@riken.jp
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import re
import os
import sys

def read_and_process_data(filepath):
    data = {}
    s1 = []
    s2 = []
    
    with open(filepath, 'r') as f:
        line_num = 0
        for line in f:
            line_num += 1
            line = line.strip()

            match = re.match(r'^(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)', line)
            if match:
                val1 = float(match.group(1))
                val2 = float(match.group(2))
                diff = val2 - val1
                
                data[line_num] = [val1, val2, diff]
                s1.append(val1)
                s2.append(val2)
            else:
                print(f"Cannot read line {line_num}: {line}")
                continue
    
    if len(s1) != len(s2):
        print(f"Error: Different number of values in columns: {len(s1)} vs {len(s2)}")
        return None, None, None, None, None
    
    sabun_up = []
    sabun_tie = []
    sabun_down = []
    
    for line_num, values in sorted(data.items(), key=lambda x: x[1][2], reverse=True):
        if values[2] > 0:
            sabun_up.append(values)
        elif values[2] == 0:
            sabun_tie.append(values)
        else:
            sabun_down.append(values)
    
    sorted_sabun_up = sorted(sabun_up.copy(), key=lambda x: x[0], reverse=True)
    sorted_sabun_down = sorted(sabun_down.copy(), key=lambda x: x[0], reverse=True)
    
    return sabun_up, sabun_tie, sabun_down, sorted_sabun_up, sorted_sabun_down

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

def calculate_iqr(data):

    if not data:
        return 0
    
    sorted_data = sorted(data)
    
    n = len(sorted_data)
    q1_idx = int(n / 4)
    q3_idx = int(3 * n / 4)
    
    q1 = sorted_data[q1_idx]
    q3 = sorted_data[q3_idx]
    
    return q3 - q1

def create_visualization(sabun_up, sabun_tie, sabun_down, sorted_sabun_up, sorted_sabun_down, output_filename):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    all_data = [
        [item[0] for item in sorted_sabun_up + sorted_sabun_down + sabun_tie], 
        [item[1] for item in sorted_sabun_up + sorted_sabun_down + sabun_tie]
    ]
    
    hide_outliers = check_outliers_extent([item for sublist in all_data for item in sublist])
    
    bp = ax.boxplot(all_data, labels=['Group1', 'Group2'], showfliers=not hide_outliers)
    
    num_up = len(sabun_up)
    num_down = len(sabun_down)
    total = num_up + num_down
    
    up_width = 7 * num_up / total if total > 0 else 0
    down_width = 7 * num_down / total if total > 0 else 0
    
    print(f"Line widths - Up: {up_width}, Down: {down_width}")
    print(f"Hiding outliers: {hide_outliers}")
    
    if sabun_up:
        q1_idx, q2_idx, q3_idx = calculate_quartiles(num_up)
        
#        q1_start = sorted_sabun_up[q1_idx][0]
#        q1_end = q1_start + sabun_up[q1_idx][2]
        q1_start = sorted_sabun_up[q1_idx][0]
        q1_end = q1_start + sabun_up[q1_idx][2]
        
        q2_start = sorted_sabun_up[q2_idx][0]
        q2_end = q2_start + sabun_up[q2_idx][2]
        
        q3_start = sorted_sabun_up[q3_idx][0]
        q3_end = q3_start + sabun_up[q3_idx][2]
#        q3_end = q3_start + sabun_up[q1_idx][2]
        
#        ax.plot([1, 2], [q1_start, q1_end], 'gray', linestyle=':', linewidth=2)
        ax.plot([1, 2], [q1_start, q1_end], 'gray', linestyle=':', linewidth=2)
        ax.plot([1, 2], [q2_start, q2_end], 'red', linestyle='-', linewidth=up_width)
#        ax.plot([1, 2], [q3_start, q3_end], 'gray', linestyle=':', linewidth=2)
        ax.plot([1, 2], [q3_start, q3_end], 'gray', linestyle=':', linewidth=2)
        
        x_coords = [1, 2, 2, 1]
        y_coords = [q1_start, q1_end, q3_end, q3_start]
        ax.fill(x_coords, y_coords, color='gray', alpha=0.5)
    
    if sabun_down:
        q1_idx, q2_idx, q3_idx = calculate_quartiles(num_down)
        
        q1_start = sorted_sabun_down[q1_idx][0]
        q1_end = q1_start + sabun_down[q1_idx][2]
#        q1_end = q1_start + sabun_down[q3_idx][2]
        
        q2_start = sorted_sabun_down[q2_idx][0]
        q2_end = q2_start + sabun_down[q2_idx][2]
        
        q3_start = sorted_sabun_down[q3_idx][0]
        q3_end = q3_start + sabun_down[q3_idx][2]
#        q3_end = q3_start + sabun_down[q1_idx][2]
        
        ax.plot([1, 2], [q1_start, q1_end], 'gray', linestyle=':', linewidth=2)
        ax.plot([1, 2], [q2_start, q2_end], 'red', linestyle='-', linewidth=down_width)
        ax.plot([1, 2], [q3_start, q3_end], 'gray', linestyle=':', linewidth=2)
        
        x_coords = [1, 2, 2, 1]
        y_coords = [q1_start, q1_end, q3_end, q3_start]

        ax.fill(x_coords, y_coords, color='gray', alpha=0.5)
        
    plt.title('Boxplot with Calculated Points')
    plt.ylabel('Value')
    
    copyright_text = "Copyright (c) 2025. RIKEN All rights reserved. This is for academic and non-commercial research use only.\nThe technology is currently under patent application. Commercial use is prohibited without a separate license agreement. E-mail: akihiro.ezoe@riken.jp"
    plt.figtext(0.5, 0.01, copyright_text, ha='center', fontsize=8, wrap=True)
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    
    with PdfPages(output_filename) as pdf:
        pdf.savefig(fig)
    
    plt.close()

def create_nonpara_visualization(sabun_up, sabun_tie, sabun_down, sorted_sabun_up, sorted_sabun_down, output_filename):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    all_data = [
        [item[0] for item in sorted_sabun_up + sorted_sabun_down + sabun_tie], 
        [item[1] for item in sorted_sabun_up + sorted_sabun_down + sabun_tie]
    ]
    
    hide_outliers = check_outliers_extent([item for sublist in all_data for item in sublist])
    
    bp = ax.boxplot(all_data, labels=['Group1', 'Group2'], showfliers=not hide_outliers)
    
    num_up = len(sabun_up)
    num_down = len(sabun_down)
    total = num_up + num_down
    
    up_values = [item[0] for item in sabun_up]
    down_values = [item[0] for item in sabun_down]
    
    base_factor = 0.1
    
    max_count = max(num_up, num_down)
    min_count = min(num_up, num_down)

    iqr_up = calculate_iqr(up_values)
    iqr_down = calculate_iqr(down_values)
    iqr_all = iqr_up + iqr_down
    
    if max_count == 0:
        max_count = 1
    
    if sabun_up:
        _, q2_idx, _ = calculate_quartiles(num_up)
        
        med_start = sorted_sabun_up[q2_idx][0]
        med_end = med_start + sabun_up[q2_idx][2]
        
        size_factor = 1 * num_up / max_count
        
        spread = base_factor * size_factor
        
        print(f"Up group: size={num_up}, spread={spread}, iqr_up={iqr_up}, size_factor={size_factor}")
        
        upper_start = med_start + (spread * iqr_all)
        upper_end = med_end + (spread * iqr_all)
        
        lower_start = med_start - (spread * iqr_all)
        lower_end = med_end - (spread * iqr_all)
        
        ax.plot([1, 2], [upper_start, upper_end], 'gray', linestyle=':', linewidth=2)
        ax.plot([1, 2], [med_start, med_end], 'red', linestyle='-', linewidth=3)
        ax.plot([1, 2], [lower_start, lower_end], 'gray', linestyle=':', linewidth=2)
        
        x_coords = [1, 2, 2, 1]
        y_coords = [upper_start, upper_end, lower_end, lower_start]
        ax.fill(x_coords, y_coords, color='gray', alpha=0.5)
    
    if sabun_down:
        _, q2_idx, _ = calculate_quartiles(num_down)
        
        med_start = sorted_sabun_down[q2_idx][0]
        med_end = med_start + sabun_down[q2_idx][2]
        
        size_factor = 1 * num_down / max_count
        
        spread = base_factor * size_factor
        
        print(f"Down group: size={num_down}, spread={spread}, iqr_down={iqr_down}, size_factor={size_factor}")
        
        upper_start = med_start + spread * iqr_all
        upper_end = med_end + spread * iqr_all
        
        lower_start = med_start - spread * iqr_all
        lower_end = med_end - spread * iqr_all
        
        ax.plot([1, 2], [upper_start, upper_end], 'gray', linestyle=':', linewidth=2)
        ax.plot([1, 2], [med_start, med_end], 'red', linestyle='-', linewidth=3)
        ax.plot([1, 2], [lower_start, lower_end], 'gray', linestyle=':', linewidth=2)
        
        x_coords = [1, 2, 2, 1]
        y_coords = [upper_start, upper_end, lower_end, lower_start]
        ax.fill(x_coords, y_coords, color='gray', alpha=0.5)
    
    plt.title('Boxplot with Calculated Points')
    plt.ylabel('Value')
    
    copyright_text = "Copyright (c) 2025. RIKEN All rights reserved. This is for academic and non-commercial research use only.\nThe technology is currently under patent application. Commercial use is prohibited without a separate license agreement. E-mail: akihiro.ezoe@riken.jp"
    plt.figtext(0.5, 0.01, copyright_text, ha='center', fontsize=8, wrap=True)
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    
    with PdfPages(output_filename) as pdf:
        pdf.savefig(fig)
    
    plt.close()

def main():
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "test_dataset.txt"
        
    print(f"Processing data from: {input_file}")
    
    sabun_up, sabun_tie, sabun_down, sorted_sabun_up, sorted_sabun_down = read_and_process_data(input_file)
    
    if sabun_up is None:
        print("Error processing data. Exiting.")
        return
    
    create_visualization(sabun_up, sabun_tie, sabun_down, sorted_sabun_up, sorted_sabun_down, "output_EZ/parametric.pdf")
    
    create_nonpara_visualization(sabun_up, sabun_tie, sabun_down, sorted_sabun_up, sorted_sabun_down, "output_EZ/non_parametric.pdf")
    
    print("Done. PDF files have been created.")

if __name__ == "__main__":
    main()
