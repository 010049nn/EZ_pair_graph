#!/usr/bin/env python3
# Copyright (c) 2025. RIKEN All rights reserved.
# This is for academic and non-commercial research use only.
# The technology is currently under patent application.
# Commercial use is prohibited without a separate license agreement.
# E-mail: akihiro.ezoe@riken.jp

import sys
import os

def calculate_quartile_indices(n):
    if n == 0:
        return None, None, None

    q1_idx = int(n / 4)
    q2_idx = int(n / 2)
    q3_idx = int(n * 3 / 4)

    return q1_idx, q2_idx, q3_idx

def calculate_stats(values):
    n = len(values)
    if n == 0:
        return 0, 0, 0, 0, 0

    sorted_values = sorted(values)

    mean = sum(sorted_values) / n

    q1_idx, q2_idx, q3_idx = calculate_quartile_indices(n)

    q1 = sorted_values[q1_idx]
    q2 = sorted_values[q2_idx]
    q3 = sorted_values[q3_idx]

    return mean, q1, q2, q3, n

def main():
    input_file = 'output_EZ/clustered_data.txt'
    stats_file = 'output_EZ/group_statistics.txt'
    calc_file = 'output_EZ/calculated_points.txt'

    data = []
    try:
        with open(input_file, 'r') as f:
            header = f.readline()
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    data.append([float(parts[0]), float(parts[1]), int(parts[2])])
    except FileNotFoundError:
        print(f"Error: Cannot open file: {input_file}")
        sys.exit(1)

    groups = {}
    for row in data:
        cluster = row[2]
        if cluster not in groups:
            groups[cluster] = []
        x_val = row[0]
        y_val = row[1]
        diff = y_val - x_val
        groups[cluster].append([x_val, y_val, diff])

    stats_results = {}

    for cluster in sorted(groups.keys()):
        group_data = groups[cluster]
        x_values = [p[0] for p in group_data]
        y_values = [p[1] for p in group_data]
        diff_values = [p[2] for p in group_data]

        m = len(group_data)

        x_mean, x_q1, x_q2, x_q3, _ = calculate_stats(x_values)
        y_mean, y_q1, y_q2, y_q3, _ = calculate_stats(y_values)

        sorted_by_x = sorted(group_data, key=lambda item: item[0], reverse=True)

        sorted_by_diff = sorted(group_data, key=lambda item: item[2], reverse=True)

        q1_idx, q2_idx, q3_idx = calculate_quartile_indices(m)

        if q2_idx is not None:
            q2_start = sorted_by_x[q2_idx][0]

            q2_diff = sorted_by_diff[q2_idx][2]

            calc_y_q2 = q2_start + q2_diff

            q1_start = sorted_by_x[q1_idx][0]
            q1_diff = sorted_by_diff[q1_idx][2]

            q3_start = sorted_by_x[q3_idx][0]
            q3_diff = sorted_by_diff[q3_idx][2]
        else:
            q2_start = x_q2
            q2_diff = y_q2 - x_q2
            calc_y_q2 = q2_start + q2_diff
            q1_start = x_q1
            q1_diff = y_q1 - x_q1
            q3_start = x_q3
            q3_diff = y_q3 - x_q3

        diff_mean, diff_q1, diff_q2, diff_q3, _ = calculate_stats(diff_values)

        stats_results[cluster] = {
            'x': {'mean': x_mean, 'q1': x_q1, 'q2': x_q2, 'q3': x_q3},
            'y': {'mean': y_mean, 'q1': y_q1, 'q2': y_q2, 'q3': y_q3},
            'diff': {
                'mean': diff_mean,
                'q1': diff_q1,
                'q2': diff_q2,
                'q3': diff_q3,
                'q1_trapezoid': q1_diff,
                'q2_trapezoid': q2_diff,
                'q3_trapezoid': q3_diff
            },
            'calculated': {
                'mean_point': [q2_start, calc_y_q2],
                'median_point': [q2_start, calc_y_q2],
                'n': m,
                'q2_start': q2_start,
                'q2_diff': q2_diff
            }
        }

    try:
        with open(stats_file, 'w') as f:
            for cluster in sorted(stats_results.keys()):
                s = stats_results[cluster]
                f.write(f"Statistics for Group {cluster}:\n")
                f.write(f"X: Mean={s['x']['mean']:.4f}, Q1={s['x']['q1']:.4f}, Q2={s['x']['q2']:.4f}, Q3={s['x']['q3']:.4f}\n")
                f.write(f"Y: Mean={s['y']['mean']:.4f}, Q1={s['y']['q1']:.4f}, Q2={s['y']['q2']:.4f}, Q3={s['y']['q3']:.4f}\n")
                f.write(f"Diff: Mean={s['diff']['mean']:.4f}, Q1={s['diff']['q1']:.4f}, Q2={s['diff']['q2']:.4f}, Q3={s['diff']['q3']:.4f}\n")
                f.write(f"Diff(trapezoid): Q1={s['diff']['q1_trapezoid']:.4f}, Q2={s['diff']['q2_trapezoid']:.4f}, Q3={s['diff']['q3_trapezoid']:.4f}\n")
                f.write(f"Calculated: Q2s={s['calculated']['q2_start']:.4f}, Q2d={s['calculated']['q2_diff']:.4f}\n")
                f.write("\n")
    except IOError as e:
        print(f"Error writing to {stats_file}: {e}")
        sys.exit(1)

    try:
        with open(calc_file, 'w') as f:
            f.write("Group\tX_Mean\tY_Calculated_Mean\tX_Median\tY_Calculated_Median\tg_num\n")
            for cluster in sorted(stats_results.keys()):
                s = stats_results[cluster]
                c = s['calculated']
                f.write(f"{cluster}\t{c['mean_point'][0]:.4f}\t{c['mean_point'][1]:.4f}\t{c['median_point'][0]:.4f}\t{c['median_point'][1]:.4f}\t{c['n']}\n")
    except IOError as e:
        print(f"Error writing to {calc_file}: {e}")
        sys.exit(1)

    print(f"Input file: {input_file}")
    print(f"Output files: {stats_file}, {calc_file}")
    print(f"\nCalculation method: trapezoid (Q2s, Q2s + Q2d)")
    print(f"  Q2s = Median of X values (sorted by X, descending)")
    print(f"  Q2d = Median of diff values (sorted by diff, descending)")

if __name__ == "__main__":
    main()
