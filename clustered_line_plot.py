#Copyright (c) 2025. RIKEN All rights reserved.
#This is for academic and non-commercial research use only.
#The technology is currently under patent application.
#Commercial use is prohibited without a separate license agreement.
#E-mail: akihiro.ezoe@riken.jp

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

cluster_data = pd.read_csv('output_EZ/clustered_data.txt', delim_whitespace=True)
calculated_points = pd.read_csv('output_EZ/calculated_points.txt', delim_whitespace=True)

output_filename = 'output_EZ/boxplot_with_lines.pdf'

plt.figure(figsize=(10, 7))

plt.boxplot(cluster_data['X'], positions=[1], widths=0.6, 
            patch_artist=True, boxprops=dict(facecolor='lightgray', color='gray'),
            whiskerprops=dict(color='gray'), capprops=dict(color='gray'),
            medianprops=dict(color='gray'), flierprops=dict(color='gray', markeredgecolor='gray'))

plt.boxplot(cluster_data['Y'], positions=[2], widths=0.6,
            patch_artist=True, boxprops=dict(facecolor='lightgray', color='gray'),
            whiskerprops=dict(color='gray'), capprops=dict(color='gray'),
            medianprops=dict(color='gray'), flierprops=dict(color='gray', markeredgecolor='gray'))

calculated_points = calculated_points.sort_values(by='g_num', ascending=True)

g_num_min = calculated_points['g_num'].min()
g_num_max = calculated_points['g_num'].max()

for _, row in calculated_points.iterrows():
    norm_g_num = (row['g_num'] - g_num_min) / (g_num_max - g_num_min) if g_num_max > g_num_min else 0.5
    
    color = plt.cm.YlOrRd(norm_g_num)
    
    line_width = 1 + 4 * norm_g_num
    
    plt.plot([1, 2], [row['X_Mean'], row['Y_Calculated_Mean']], 
             color=color, linewidth=line_width, solid_capstyle='round',
             zorder=int(10 + 90 * norm_g_num))

plt.xticks([1, 2], ['X', 'Y'])

plt.title('Boxplot with Calculated Points')
plt.ylabel('Value')

copyright_text = "Copyright (c) 2025. RIKEN All rights reserved. This is for academic and non-commercial research use only.\nThe technology is currently under patent application. Commercial use is prohibited without a separate license agreement. E-mail: akihiro.ezoe@riken.jp"
plt.figtext(0.5, 0.01, copyright_text, ha='center', fontsize=8, color='black')

plt.subplots_adjust(bottom=0.15)

plt.savefig(output_filename)
plt.close()

print(f"The output file name was {output_filename}.")
