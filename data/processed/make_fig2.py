# make_fig2.py
"""
Generate Figure 2: CTClass Distribution by Stack Layer
Publication-ready output as PDF and PNG (300 dpi)
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ============================================================================
# CONFIGURATION
# ============================================================================

# Colors (Hex)
COLORS = {
    'A': '#FF9933',  # orange
    'B': '#FFCC00',  # yellow
    'C': '#CC3333'   # red
}

# Font settings
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

# Output settings
OUTPUT_DIR = 'figures'
OUTPUT_PDF = os.path.join(OUTPUT_DIR, 'fig2_layer_x_ctclass.pdf')
OUTPUT_PNG = os.path.join(OUTPUT_DIR, 'fig2_layer_x_ctclass.png')

# ============================================================================
# LOAD DATA
# ============================================================================

print("Loading data...")

# Check if files exist
required_files = [
    'd_layer_x_ctclass_overall_pct.csv',
    'd_layer_x_ctclass_overall_counts.csv'
]

for fname in required_files:
    if not os.path.exists(fname):
        raise FileNotFoundError(f"Required file not found: {fname}")

# Load data
df_pct = pd.read_csv('d_layer_x_ctclass_overall_pct.csv')
df_counts = pd.read_csv('d_layer_x_ctclass_overall_counts.csv')

# ============================================================================
# QUALITY CHECKS
# ============================================================================

print("Running quality checks...")

# Check 1: Percentages sum to 100 for each layer
for idx, row in df_pct.iterrows():
    total_pct = row['A'] + row['B'] + row['C']
    assert 99.8 <= total_pct <= 100.2, \
        f"Layer {row['stacklayer']}: percentages sum to {total_pct}%"
print(f"✓ All layer percentages sum to ~100%")

# Check 2: Total count consistency
total_count = df_counts[['A', 'B', 'C']].sum().sum()
print(f"✓ Total count across all layers: {total_count}")

# ============================================================================
# PREPARE DATA
# ============================================================================

# Sort by C-dominance (descending)
df_pct = df_pct.sort_values('C', ascending=False).reset_index(drop=True)
df_counts = df_counts.set_index('stacklayer').loc[df_pct['stacklayer']].reset_index()

# Calculate N for each layer
df_pct['N'] = df_counts[['A', 'B', 'C']].sum(axis=1)

# Create Y labels with N
y_labels = [f"{row['stacklayer']} (N={int(row['N'])})" 
            for _, row in df_pct.iterrows()]

# ============================================================================
# CREATE FIGURE
# ============================================================================

print("Creating figure...")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Create figure
fig, ax = plt.subplots(figsize=(8, 4))

# Y positions
n_layers = len(df_pct)
y_pos = np.arange(n_layers)
bar_height = 0.6

# Stack the bars: A (left), B (middle), C (right)
left_a = np.zeros(n_layers)
left_b = df_pct['A'].values
left_c = df_pct['A'].values + df_pct['B'].values

# Draw stacked horizontal bars
bars_a = ax.barh(y_pos, df_pct['A'], height=bar_height,
                 left=left_a, color=COLORS['A'],
                 edgecolor='black', linewidth=1, zorder=3)

bars_b = ax.barh(y_pos, df_pct['B'], height=bar_height,
                 left=left_b, color=COLORS['B'],
                 edgecolor='black', linewidth=1, zorder=3)

bars_c = ax.barh(y_pos, df_pct['C'], height=bar_height,
                 left=left_c, color=COLORS['C'],
                 edgecolor='black', linewidth=1, zorder=3)

# Add percentage labels (only if segment >= 10%)
# A: black, B: black, C: white
for i in range(n_layers):
    # A segment (black text)
    if df_pct.iloc[i]['A'] >= 10:
        x_pos = df_pct.iloc[i]['A'] / 2
        ax.text(x_pos, i, f"{df_pct.iloc[i]['A']:.1f}%",
                ha='center', va='center',
                fontsize=9, color='black', weight='bold', zorder=4)
    
    # B segment (black text)
    if df_pct.iloc[i]['B'] >= 10:
        x_pos = df_pct.iloc[i]['A'] + df_pct.iloc[i]['B'] / 2
        ax.text(x_pos, i, f"{df_pct.iloc[i]['B']:.1f}%",
                ha='center', va='center',
                fontsize=9, color='black', weight='bold', zorder=4)
    
    # C segment (white text)
    if df_pct.iloc[i]['C'] >= 10:
        x_pos = df_pct.iloc[i]['A'] + df_pct.iloc[i]['B'] + df_pct.iloc[i]['C'] / 2
        ax.text(x_pos, i, f"{df_pct.iloc[i]['C']:.1f}%",
                ha='center', va='center',
                fontsize=9, color='white', weight='bold', zorder=4)

# Formatting
ax.set_yticks(y_pos)
ax.set_yticklabels(y_labels, fontsize=10)
ax.set_xlabel('Percentage (%)', fontsize=11)
ax.set_xlim(0, 100)

# Vertical gridlines
ax.xaxis.grid(True, linestyle='--', color='#DDDDDD', linewidth=0.5, zorder=0)
ax.set_axisbelow(True)

# Spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Invert y-axis so highest C is on top
ax.invert_yaxis()

# ============================================================================
# LEGEND
# ============================================================================

# Create legend
legend_elements = [
    Patch(facecolor=COLORS['A'], edgecolor='black', label='A – Compile-Time Avoidable'),
    Patch(facecolor=COLORS['B'], edgecolor='black', label='B – Potentially CT'),
    Patch(facecolor=COLORS['C'], edgecolor='black', label='C – Runtime-Only')
]

# Add legend below the chart
ax.legend(handles=legend_elements,
         loc='upper center',
         bbox_to_anchor=(0.5, -0.15),
         ncol=3,
         fontsize=9,
         frameon=True,
         edgecolor='black')

# ============================================================================
# SAVE FIGURE
# ============================================================================

print("Saving figure...")

# Save as PDF
plt.savefig(OUTPUT_PDF, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {OUTPUT_PDF}")

# Save as PNG
plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {OUTPUT_PNG}")

plt.close()

print("\n✓ Figure 2 complete!")