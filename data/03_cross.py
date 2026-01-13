
"""
03_cross_tabs.py
Erzeugt Kreuztabellen (Story-Analysen) für GPU-Bug-Analyse (Schritt D).
"""

import pandas as pd
import sys
from pathlib import Path


def normalize_column_name(col):
    """Normalisiert Spaltennamen: strip, lowercase, spaces->underscore, BOM entfernen."""
    col = col.strip().lower()
    col = col.replace('\ufeff', '')  # BOM
    col = col.replace(' ', '_')
    return col


def load_and_prepare(filepath, required_cols, gpu_filter=False):
    """
    Lädt CSV, normalisiert Spalten, entfernt doppelte Header, dedupliziert.
    """
    df = pd.read_csv(filepath, encoding='utf-8-sig', dtype=str)
    
    # Spaltennamen normalisieren
    df.columns = [normalize_column_name(c) for c in df.columns]
    
    # Doppelte Header entfernen (nur für issueid/project prüfen)
    if 'issueid' in df.columns:
        df = df[df['issueid'].str.strip().str.lower() != 'issueid']
    if 'project' in df.columns:
        df = df[df['project'].str.strip().str.lower() != 'project']
    
    df = df.reset_index(drop=True)
    
    # Required columns prüfen
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"FEHLER in {filepath}: Fehlende Required-Spalten: {missing}")
        print(f"Verfügbare Spalten: {list(df.columns)}")
        sys.exit(1)
    
    # GPU-Filter für Qiskit
    if gpu_filter:
        if 'gpu_relevant' not in df.columns:
            print(f"FEHLER in {filepath}: 'gpu_relevant' Spalte für Filter fehlt")
            sys.exit(1)
        df = df[df['gpu_relevant'].str.strip().str.upper() == 'X'].copy()
    
    # Nach (Project, IssueID) deduplizieren (keep="last")
    df = df.drop_duplicates(subset=['project', 'issueid'], keep='last')
    
    return df


def save_crosstab(df, row_var, col_var, prefix, by_project=False):
    """
    Erstellt Kreuztabelle (counts und row-wise percentages) und speichert als CSV.
    """
    if by_project:
        # Gruppieren nach project
        projects = sorted(df['project'].dropna().unique())
        
        all_counts = []
        all_pcts = []
        
        for proj in projects:
            df_proj = df[df['project'] == proj]
            ct_counts = pd.crosstab(df_proj[row_var], df_proj[col_var])
            ct_counts['project'] = proj
            
            row_sums = ct_counts.drop('project', axis=1).sum(axis=1).replace(0, pd.NA)
            ct_pct = ct_counts.drop('project', axis=1).div(row_sums, axis=0) * 100
            ct_pct = ct_pct.round(1)
            ct_pct['project'] = proj
            
            all_counts.append(ct_counts)
            all_pcts.append(ct_pct)
        
        counts_df = pd.concat(all_counts).reset_index()
        pcts_df = pd.concat(all_pcts).reset_index()
        
        counts_file = f"{prefix}_by_project_counts.csv"
        pcts_file = f"{prefix}_by_project_pct.csv"
    else:
        ct_counts = pd.crosstab(df[row_var], df[col_var])
        ct_pct = ct_counts.div(ct_counts.sum(axis=1), axis=0) * 100
        ct_pct = ct_pct.round(1)
        
        counts_df = ct_counts.reset_index()
        pcts_df = ct_pct.reset_index()
        
        counts_file = f"{prefix}_overall_counts.csv"
        pcts_file = f"{prefix}_overall_pct.csv"
    
    counts_df.to_csv(counts_file, index=False)
    pcts_df.to_csv(pcts_file, index=False)
    
    return [counts_file, pcts_file]


def main():
    # Dateipfade
    cudaq_file = Path("./Cuda-Q/cudaq_issues_raw.csv")
    qiskit_file = Path("./qskit/github_issues.csv")
    
    # Required columns (normalisiert)
    required_base = ['project', 'issueid', 'stacklayer', 'bugtype', 'ctclass']
    
    # CUDA-Q: alle Issues
    print("Lade CUDA-Q Daten...")
    cudaq_df = load_and_prepare(cudaq_file, required_cols=required_base, gpu_filter=False)
    
    # Qiskit: nur GPU-relevante Issues
    print("Lade Qiskit Daten (GPU-Filter)...")
    qiskit_required = required_base + ['gpu_relevant']
    qiskit_df = load_and_prepare(qiskit_file, required_cols=qiskit_required, gpu_filter=True)
    
    # Kombinieren
    df = pd.concat([cudaq_df, qiskit_df], ignore_index=True)
    
    # UID erstellen (project#issueid)
    df['uid'] = df['project'].astype(str).str.strip() + '#' + df['issueid'].astype(str).str.strip()
    
    # Labels cleanen
    df['ctclass'] = df['ctclass'].astype(str).str.strip().str.upper()
    df['stacklayer'] = df['stacklayer'].astype(str).str.strip()
    df['bugtype'] = df['bugtype'].astype(str).str.strip()
    df['project'] = df['project'].astype(str).str.strip()
    
    # N unique Issues
    n_cudaq = cudaq_df['issueid'].nunique()
    n_qiskit = qiskit_df['issueid'].nunique()
    n_total = df['uid'].nunique()
    
    print(f"\nN unique Issues:")
    print(f"  CUDA-Q: {n_cudaq}")
    print(f"  Qiskit (GPU): {n_qiskit}")
    print(f"  Total: {n_total}")
    print()
    
    # Outputs
    outputs = []
    
    # 1) StackLayer × CTClass
    outputs.extend(save_crosstab(df, 'stacklayer', 'ctclass', 'd_layer_x_ctclass', by_project=False))
    outputs.extend(save_crosstab(df, 'stacklayer', 'ctclass', 'd_layer_x_ctclass', by_project=True))
    
    # 2) BugType × CTClass
    outputs.extend(save_crosstab(df, 'bugtype', 'ctclass', 'd_bugtype_x_ctclass', by_project=False))
    outputs.extend(save_crosstab(df, 'bugtype', 'ctclass', 'd_bugtype_x_ctclass', by_project=True))
    
    # 3) Project × CTClass
    outputs.extend(save_crosstab(df, 'project', 'ctclass', 'd_project_x_ctclass', by_project=False))
    
    # 4) Audit: Unique Labels
    audit_overall = pd.DataFrame([{
        'project': 'OVERALL',
        'n_unique_stacklayer': df['stacklayer'].nunique(),
        'n_unique_bugtype': df['bugtype'].nunique(),
        'n_issues': df['uid'].nunique()
    }])
    
    audit_by_project = df.groupby('project').agg({
        'stacklayer': 'nunique',
        'bugtype': 'nunique',
        'uid': 'nunique'
    }).reset_index()
    audit_by_project.columns = ['project', 'n_unique_stacklayer', 'n_unique_bugtype', 'n_issues']
    
    audit_df = pd.concat([audit_overall, audit_by_project], ignore_index=True)
    audit_file = 'd_audit_unique_labels.csv'
    audit_df.to_csv(audit_file, index=False)
    outputs.append(audit_file)
    
    print("Geschriebene Dateien:")
    for output in outputs:
        print(f"  - {output}")


if __name__ == '__main__':
    main()
