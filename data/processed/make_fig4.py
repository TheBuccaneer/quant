# make_fig4.py
"""
Generate Figure 4: B1 vs B2 Subtype Distribution
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
    'B1': '#FFEB99',  # light yellow
    'B2': '#FFD966'   # darker yellow
}

# Font settings
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

# Output settings
OUTPUT_DIR = 'figures'
OUTPUT_PDF = os.path.join(OUTPUT_DIR, 'fig4_b_subtype.pdf')
OUTPUT_PNG = os.path.join(OUTPUT_DIR, 'fig4_b_subtype.png')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def detect_format_and_parse(df, has_project=False):
    """
    Detect if CSV is LONG or WIDE format and parse accordingly.
    Returns: dict with keys 'B1' and 'B2' (and optionally 'project')
    """
    cols = df.columns.tolist()
    
    # Check if WIDE format (has B1 and B2 columns)
    if 'B1' in cols and 'B2' in cols:
        # WIDE format
        if has_project:
            # by_project WIDE
            result = []
            for _, row in df.iterrows():
                proj = row['project']
                b1_val = float(row['B1'])
                b2_val = float(row['B2'])
                s = b1_val + b2_val
                
                # Robust check: percentages only if sum ≈ 100
                if 99.5 <= s <= 100.5:  # percentages
                    b1_pct = b1_val
                    b2_pct = b2_val
                    n = None
                else:  # counts
                    total = s
                    b1_pct = (b1_val / total * 100) if total > 0 else 0
                    b2_pct = (b2_val / total * 100) if total > 0 else 0
                    n = int(total)
                
                result.append({
                    'project': proj,
                    'B1': b1_pct,
                    'B2': b2_pct,
                    'N': n
                })
            return result
        else:
            # overall WIDE
            b1_val = float(df['B1'].iloc[0])
            b2_val = float(df['B2'].iloc[0])
            s = b1_val + b2_val
            
            if 99.5 <= s <= 100.5:  # percentages
                b1_pct = b1_val
                b2_pct = b2_val
                n = None
            else:  # counts
                total = s
                b1_pct = (b1_val / total * 100) if total > 0 else 0
                b2_pct = (b2_val / total * 100) if total > 0 else 0
                n = int(total)
            
            return {'B1': b1_pct, 'B2': b2_pct, 'N': n}
    
    # LONG format - detect columns
    subtype_col = None
    for col_name in ['ctsubtype_norm', 'b_subtype', 'subtype', 'b1b2', 'b_subtype_clean']:
        if col_name in cols:
            subtype_col = col_name
            break
    
    count_col = 'count' if 'count' in cols else 'n'
    
    if subtype_col is None:
        raise ValueError("Could not detect subtype column in LONG format")
    
    if has_project:
        # by_project LONG
        result = []
        for proj in df['project'].unique():
            df_proj = df[df['project'] == proj]
            b1_count = df_proj[df_proj[subtype_col] == 'B1'][count_col].sum()
            b2_count = df_proj[df_proj[subtype_col] == 'B2'][count_col].sum()
            total = b1_count + b2_count
            
            result.append({
                'project': proj,
                'B1': (b1_count / total * 100) if total > 0 else 0,
                'B2': (b2_count / total * 100) if total > 0 else 0,
                'N': int(total)
            })
        return result
    else:
        # overall LONG
        b1_count = df[df[subtype_col] == 'B1'][count_col].sum()
        b2_count = df[df[subtype_col] == 'B2'][count_col].sum()
        total = b1_count + b2_count
        
        return {
            'B1': (b1_count / total * 100) if total > 0 else 0,
            'B2': (b2_count / total * 100) if total > 0 else 0,
            'N': int(total)
        }

# ============================================================================
# LOAD DATA
# ============================================================================

print("Loading data...")

# Check if files exist
required_files = [
    'c_b_subtype_overall.csv',
    'c_b_subtype_by_project.csv'
]

for fname in required_files:
    if not os.path.exists(fname):
        raise FileNotFoundError(f"Required file not found: {fname}")

# Load and parse data
df_overall_raw = pd.read_csv('c_b_subtype_overall.csv')
df_project_raw = pd.read_csv('c_b_subtype_by_project.csv')

overall_data = detect_format_and_parse(df_overall_raw, has_project=False)
project_data = detect_format_and_parse(df_project_raw, has_project=True)

# ============================================================================
# QUALITY CHECKS
# ============================================================================

print("Running quality checks...")

# Check 1: Percentages sum to 100
overall_sum = overall_data['B1'] + overall_data['B2']
assert 99.8 <= overall_sum <= 100.2, \
    f"Overall: B1+B2 = {overall_sum}%"
print(f"✓ Overall percentages sum to ~100%")

for proj in project_data:
    proj_sum = proj['B1'] + proj['B2']
    assert 99.8 <= proj_sum <= 100.2, \
        f"Project {proj['project']}: B1+B2 = {proj_sum}%"
print(f"✓ All project percentages sum to ~100%")

# Check 2: N consistency (if available)
if overall_data['N'] is not None:
    project_n_sum = sum(p['N'] for p in project_data if p['N'] is not None)
    if project_n_sum > 0:
        if abs(overall_data['N'] - project_n_sum) > 1:
            print(f"⚠ Warning: Overall N={overall_data['N']} != Sum of project Ns={project_n_sum}")
        else:
            print(f"✓ N consistency check passed")

# ============================================================================
# PREPARE DATA
# ============================================================================

# Enforce project order: CUDA-Q first, then Qiskit Aer
ordered_projects = []
for proj_data in project_data:
    proj = proj_data['project']
    if 'cuda-quantum' in proj.lower():
        n = proj_data['N'] if proj_data['N'] is not None else '?'
        ordered_projects.insert(0, {
            'label': f"CUDA-Q\n(N={n})",
            'B1': proj_data['B1'],
            'B2': proj_data['B2']
        })
    elif 'qiskit-aer' in proj.lower():
        n = proj_data['N'] if proj_data['N'] is not None else '?'
        ordered_projects.append({
            'label': f"Qiskit Aer (GPU)\n(N={n})",
            'B1': proj_data['B1'],
            'B2': proj_data['B2']
        })

# Fallback: if project strings didn't match, use original order
if not ordered_projects:
    ordered_projects = [{
        'label': p['project'],
        'B1': p['B1'],
        'B2': p['B2']
    } for p in project_data]

# ============================================================================
# CREATE FIGURE
# ============================================================================

print("Creating figure...")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Create figure with 2 subplots
fig = plt.figure(figsize=(10, 4))
gs = fig.add_gridspec(1, 2, left=0.08, right=0.95, wspace=0.5)

ax_a = fig.add_subplot(gs[0, 0])
ax_b = fig.add_subplot(gs[0, 1])

# ============================================================================
# PANEL A: Overall
# ============================================================================

bar_height = 0.6

# Overall bar
n_label = f"\n(N={overall_data['N']})" if overall_data['N'] is not None else ""
y_label_overall = f"Overall{n_label}"

# Draw stacked bar
ax_a.barh(0, overall_data['B1'], height=bar_height,
          left=0, color=COLORS['B1'],
          edgecolor='black', linewidth=1, zorder=3)

ax_a.barh(0, overall_data['B2'], height=bar_height,
          left=overall_data['B1'], color=COLORS['B2'],
          edgecolor='black', linewidth=1, zorder=3)

# Add percentage labels (only if >= 10%)
if overall_data['B1'] >= 10:
    ax_a.text(overall_data['B1']/2, 0, f"{overall_data['B1']:.1f}%",
              ha='center', va='center',
              fontsize=9, color='black', weight='bold', zorder=4)

if overall_data['B2'] >= 10:
    ax_a.text(overall_data['B1'] + overall_data['B2']/2, 0, f"{overall_data['B2']:.1f}%",
              ha='center', va='center',
              fontsize=9, color='black', weight='bold', zorder=4)

# Formatting
ax_a.set_yticks([0])
ax_a.set_yticklabels([y_label_overall], fontsize=10)
ax_a.set_xlabel('Percentage (%)', fontsize=11)
ax_a.set_xlim(0, 100)
ax_a.set_ylim(-0.5, 0.5)

# Vertical gridlines
ax_a.xaxis.grid(True, linestyle='--', color='#DDDDDD', linewidth=0.5, zorder=0)
ax_a.set_axisbelow(True)

# Spines
ax_a.spines['top'].set_visible(False)
ax_a.spines['right'].set_visible(False)

# Panel letter
ax_a.text(-0.15, 1.05, '(A)',
         transform=ax_a.transAxes,
         fontsize=12, weight='bold')

# ============================================================================
# PANEL B: By Project
# ============================================================================

n_projects = len(ordered_projects)
y_pos = np.arange(n_projects)

# Draw stacked bars for each project
for i, proj in enumerate(ordered_projects):
    ax_b.barh(i, proj['B1'], height=bar_height,
              left=0, color=COLORS['B1'],
              edgecolor='black', linewidth=1, zorder=3)
    
    ax_b.barh(i, proj['B2'], height=bar_height,
              left=proj['B1'], color=COLORS['B2'],
              edgecolor='black', linewidth=1, zorder=3)
    
    # Add percentage labels (only if >= 10%)
    if proj['B1'] >= 10:
        ax_b.text(proj['B1']/2, i, f"{proj['B1']:.1f}%",
                  ha='center', va='center',
                  fontsize=9, color='black', weight='bold', zorder=4)
    
    if proj['B2'] >= 10:
        ax_b.text(proj['B1'] + proj['B2']/2, i, f"{proj['B2']:.1f}%",
                  ha='center', va='center',
                  fontsize=9, color='black', weight='bold', zorder=4)

# Formatting
ax_b.set_yticks(y_pos)
ax_b.set_yticklabels([p['label'] for p in ordered_projects], fontsize=10)
ax_b.set_xlabel('Percentage (%)', fontsize=11)
ax_b.set_xlim(0, 100)

# Vertical gridlines
ax_b.xaxis.grid(True, linestyle='--', color='#DDDDDD', linewidth=0.5, zorder=0)
ax_b.set_axisbelow(True)

# Spines
ax_b.spines['top'].set_visible(False)
ax_b.spines['right'].set_visible(False)

# Invert y-axis
ax_b.invert_yaxis()

# Panel letter
ax_b.text(-0.15, 1.05, '(B)',
         transform=ax_b.transAxes,
         fontsize=12, weight='bold')

# ============================================================================
# LEGEND
# ============================================================================

# Create legend
legend_elements = [
    Patch(facecolor=COLORS['B1'], edgecolor='black', label='B1 – Config/Metadata Constraints'),
    Patch(facecolor=COLORS['B2'], edgecolor='black', label='B2 – Contracts/Typestate')
]

# Add legend below the figure
fig.legend(handles=legend_elements,
          loc='upper center',
          bbox_to_anchor=(0.5, -0.05),
          ncol=2,
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

print("\n✓ Figure 4 complete!")