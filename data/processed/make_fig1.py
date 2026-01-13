# make_fig1.py
"""
Generate Figure 1: CTClass Distribution (Overall + by Project)
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
OUTPUT_PDF = os.path.join(OUTPUT_DIR, 'fig1_ctclass.pdf')
OUTPUT_PNG = os.path.join(OUTPUT_DIR, 'fig1_ctclass.png')

# ============================================================================
# LOAD DATA
# ============================================================================

print("Loading data...")

# Check if files exist
required_files = [
    'c_ctclass_overall.csv',
    'd_project_x_ctclass_overall_pct.csv',
    'd_project_x_ctclass_overall_counts.csv'
]

for fname in required_files:
    if not os.path.exists(fname):
        raise FileNotFoundError(f"Required file not found: {fname}")

# Panel A data
df_overall = pd.read_csv('c_ctclass_overall.csv')

# Panel B data
df_pct = pd.read_csv('d_project_x_ctclass_overall_pct.csv')
df_counts = pd.read_csv('d_project_x_ctclass_overall_counts.csv')

# ============================================================================
# QUALITY CHECKS
# ============================================================================

print("Running quality checks...")

# Check 1: Total count should be 196
total_count = df_overall['count'].sum()
expected_total = df_overall['total'].iloc[0]
assert abs(total_count - expected_total) <= 1, \
    f"Total count {total_count} != expected {expected_total}"
print(f"✓ Total count: {total_count}")

# Check 2: Percentages sum to 100 for each project
for idx, row in df_pct.iterrows():
    total_pct = row['A'] + row['B'] + row['C']
    assert 99.8 <= total_pct <= 100.2, \
        f"Project {row['project']}: percentages sum to {total_pct}%"
print(f"✓ All project percentages sum to ~100%")

# ============================================================================
# CREATE FIGURE
# ============================================================================

print("Creating figure...")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Create figure with 2 subplots
fig = plt.figure(figsize=(10, 4))
gs = fig.add_gridspec(1, 2, left=0.08, right=0.95, wspace=0.3)

ax_a = fig.add_subplot(gs[0, 0])
ax_b = fig.add_subplot(gs[0, 1])

# ============================================================================
# PANEL A: Overall CTClass Distribution
# ============================================================================

# Enforce explicit A, B, C order
df_overall['ctclass'] = pd.Categorical(df_overall['ctclass'], 
                                       categories=['A', 'B', 'C'], 
                                       ordered=True)
df_overall = df_overall.sort_values('ctclass')

# X positions
x_pos = np.arange(len(df_overall))

# Create bars
bars = ax_a.bar(x_pos, df_overall['count'], 
                width=0.6,
                color=[COLORS[c] for c in df_overall['ctclass']],
                edgecolor='black',
                linewidth=1,
                zorder=3)

# Add labels on bars (white text for C, black for A and B)
for i, (idx, row) in enumerate(df_overall.iterrows()):
    count = int(row['count'])
    pct = row['percent']
    label = f"{count} ({pct:.1f}%)"
    
    # Use white text for C (dark red), black for A and B
    text_color = 'white' if row['ctclass'] == 'C' else 'black'
    
    ax_a.text(i, count/2, label, 
             ha='center', va='center',
             fontsize=10, color=text_color,
             weight='normal',
             zorder=4)

# Formatting
ax_a.set_xticks(x_pos)
ax_a.set_xticklabels(df_overall['ctclass'], fontsize=10)
ax_a.set_ylabel('Count (N bugs)', fontsize=11)
ax_a.set_ylim(0, df_overall['count'].max() + 10)

# Gridlines
ax_a.yaxis.grid(True, linestyle='--', color='#DDDDDD', linewidth=0.5, zorder=0)
ax_a.set_axisbelow(True)

# Spines
ax_a.spines['top'].set_visible(False)
ax_a.spines['right'].set_visible(False)

# Add N annotation (top left with white background for visibility)
ax_a.text(0.05, 0.95, f'N = {int(total_count)}',
         transform=ax_a.transAxes,
         ha='left', va='top',
         fontsize=10,
         bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                  edgecolor='gray', alpha=0.9))

# Panel letter
ax_a.text(-0.15, 1.05, '(A)',
         transform=ax_a.transAxes,
         fontsize=12, weight='bold')

# ============================================================================
# PANEL B: CTClass by Project (100% Stacked)
# ============================================================================

# Prepare data
projects = df_pct['project'].tolist()
n_projects = len(projects)

# Calculate N for each project
project_n = []
for proj in projects:
    n = df_counts[df_counts['project'] == proj][['A', 'B', 'C']].sum(axis=1).values[0]
    project_n.append(int(n))

# Create X labels with N
x_labels = []
for proj, n in zip(projects, project_n):
    if 'cuda-quantum' in proj.lower():
        label = f"CUDA-Q\n(N={n})"
    elif 'qiskit-aer' in proj.lower():
        label = f"Qiskit Aer (GPU)\n(N={n})"
    else:
        # Fallback: use project name
        proj_short = proj.split('/')[-1] if '/' in proj else proj
        label = f"{proj_short}\n(N={n})"
    x_labels.append(label)

# X positions
x_pos = np.arange(n_projects)

# Stack the bars: A (bottom), B (middle), C (top)
bottom_a = np.zeros(n_projects)
bottom_b = df_pct['A'].values
bottom_c = df_pct['A'].values + df_pct['B'].values

# Draw stacked bars
bar_width = 0.5

bars_a = ax_b.bar(x_pos, df_pct['A'], width=bar_width,
                  bottom=bottom_a, color=COLORS['A'],
                  edgecolor='black', linewidth=1, zorder=3)

bars_b = ax_b.bar(x_pos, df_pct['B'], width=bar_width,
                  bottom=bottom_b, color=COLORS['B'],
                  edgecolor='black', linewidth=1, zorder=3)

bars_c = ax_b.bar(x_pos, df_pct['C'], width=bar_width,
                  bottom=bottom_c, color=COLORS['C'],
                  edgecolor='black', linewidth=1, zorder=3)

# Add percentage labels (only if segment >= 10%)
# A and C: white text, B: black text (for readability on yellow)
for i in range(n_projects):
    # A segment (white text)
    if df_pct.iloc[i]['A'] >= 10:
        y_pos = df_pct.iloc[i]['A'] / 2
        ax_b.text(i, y_pos, f"{df_pct.iloc[i]['A']:.1f}%",
                 ha='center', va='center',
                 fontsize=9, color='white', weight='bold', zorder=4)
    
    # B segment (black text for better contrast on yellow)
    if df_pct.iloc[i]['B'] >= 10:
        y_pos = df_pct.iloc[i]['A'] + df_pct.iloc[i]['B'] / 2
        ax_b.text(i, y_pos, f"{df_pct.iloc[i]['B']:.1f}%",
                 ha='center', va='center',
                 fontsize=9, color='black', weight='bold', zorder=4)
    
    # C segment (white text)
    if df_pct.iloc[i]['C'] >= 10:
        y_pos = df_pct.iloc[i]['A'] + df_pct.iloc[i]['B'] + df_pct.iloc[i]['C'] / 2
        ax_b.text(i, y_pos, f"{df_pct.iloc[i]['C']:.1f}%",
                 ha='center', va='center',
                 fontsize=9, color='white', weight='bold', zorder=4)

# Formatting
ax_b.set_xticks(x_pos)
ax_b.set_xticklabels(x_labels, fontsize=10)
ax_b.set_ylabel('Percentage (%)', fontsize=11)
ax_b.set_ylim(0, 100)

# Gridlines
ax_b.yaxis.grid(True, linestyle='--', color='#DDDDDD', linewidth=0.5, zorder=0)
ax_b.set_axisbelow(True)

# Spines
ax_b.spines['top'].set_visible(False)
ax_b.spines['right'].set_visible(False)

# Panel letter
ax_b.text(-0.15, 1.05, '(B)',
         transform=ax_b.transAxes,
         fontsize=12, weight='bold')

# ============================================================================
# LEGEND
# ============================================================================

# Create legend (smaller font for less dominance)
legend_elements = [
    Patch(facecolor=COLORS['A'], edgecolor='black', label='A – Compile-Time Avoidable'),
    Patch(facecolor=COLORS['B'], edgecolor='black', label='B – Potentially CT'),
    Patch(facecolor=COLORS['C'], edgecolor='black', label='C – Runtime-Only')
]

# Add legend below the panels (horizontal, centered)
fig.legend(handles=legend_elements, 
          loc='upper center',
          bbox_to_anchor=(0.5, -0.05),
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

print("\n✓ Figure 1 complete!")