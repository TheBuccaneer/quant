
"""
02_core_distributions.py
Berechnet Kern-Deskriptivstatistik für GPU-Bug-Analyse (Schritt C).
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Optional: Wilson CI
try:
    from statsmodels.stats.proportion import proportion_confint
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


def normalize_column_name(col):
    """Normalisiert Spaltennamen: strip, lowercase, spaces->underscore, BOM entfernen."""
    col = col.strip().lower()
    col = col.replace('\ufeff', '')  # BOM
    col = col.replace(' ', '_')
    return col


def find_col(df, candidates):
    """
    Findet die erste passende Spalte aus einer Liste von Kandidaten.
    Gibt den tatsächlichen Spaltennamen zurück oder None.
    """
    norm_cols = {normalize_column_name(c): c for c in df.columns}
    for candidate in candidates:
        norm_candidate = normalize_column_name(candidate)
        if norm_candidate in norm_cols:
            return norm_cols[norm_candidate]
    return None


def load_and_prepare(filepath, required_cols, optional_cols=None, gpu_filter=False):
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
        # "X" bedeutet True
        df = df[df['gpu_relevant'].str.strip().str.upper() == 'X'].copy()
    
    # Nach IssueID deduplizieren (keep="last")
    df = df.drop_duplicates(subset=['issueid'], keep='last')
    
    return df


def wilson_ci(count, total, alpha=0.05):
    """Berechnet Wilson-CI für eine Proportion."""
    if not HAS_STATSMODELS or total == 0:
        return np.nan, np.nan
    ci_low, ci_high = proportion_confint(count, total, alpha=alpha, method='wilson')
    return ci_low * 100, ci_high * 100


def compute_distribution(df, group_col, category_col, output_prefix, by_project=False):
    """
    Berechnet Count + Prozent (+ optional Wilson-CI) für eine Kategorie.
    """
    if by_project:
        grouped = df.groupby(['project', category_col], dropna=False).size().reset_index(name='count')
        totals = df.groupby('project')['uid'].nunique().reset_index(name='total')
        result = grouped.merge(totals, on='project')
        result['percent'] = (result['count'] / result['total'] * 100).round(1)
        
        if HAS_STATSMODELS:
            result['pct_ci_low'] = result.apply(
                lambda r: wilson_ci(r['count'], r['total'])[0], axis=1
            ).round(1)
            result['pct_ci_high'] = result.apply(
                lambda r: wilson_ci(r['count'], r['total'])[1], axis=1
            ).round(1)
        
        filename = f"{output_prefix}_by_project.csv"
    else:
        grouped = df.groupby(category_col, dropna=False).size().reset_index(name='count')
        total = df['uid'].nunique()
        grouped['total'] = total
        grouped['percent'] = (grouped['count'] / total * 100).round(1)
        
        if HAS_STATSMODELS:
            grouped['pct_ci_low'] = grouped.apply(
                lambda r: wilson_ci(r['count'], r['total'])[0], axis=1
            ).round(1)
            grouped['pct_ci_high'] = grouped.apply(
                lambda r: wilson_ci(r['count'], r['total'])[1], axis=1
            ).round(1)
        
        result = grouped
        filename = f"{output_prefix}_overall.csv"
    
    result.to_csv(filename, index=False)
    return filename


def main():
    # Dateipfade
    cudaq_file = Path("./Cuda-Q/cudaq_issues_raw.csv")
    qiskit_file = Path("./qskit/github_issues.csv")
    
    # Required columns (normalisiert)
    required_base = ['project', 'issueid', 'bugtype', 'stacklayer', 'ctclass']
    
    # CUDA-Q: alle Issues
    print("Lade CUDA-Q Daten...")
    cudaq_df = load_and_prepare(
        cudaq_file,
        required_cols=required_base,
        gpu_filter=False
    )
    
    # Qiskit: nur GPU-relevante Issues
    print("Lade Qiskit Daten (GPU-Filter)...")
    qiskit_required = required_base + ['gpu_relevant']
    qiskit_df = load_and_prepare(
        qiskit_file,
        required_cols=qiskit_required,
        gpu_filter=True
    )
    
    # Kombinieren
    df = pd.concat([cudaq_df, qiskit_df], ignore_index=True)
    
    # UID erstellen (project#issueid) für repo-übergreifendes Zählen
    df['uid'] = df['project'].astype(str).str.strip() + '#' + df['issueid'].astype(str).str.strip()
    
    # Data cleaning
    df['ctclass'] = df['ctclass'].astype(str).str.strip().str.upper()
    df['bugtype'] = df['bugtype'].astype(str).str.strip()
    df['stacklayer'] = df['stacklayer'].astype(str).str.strip()
    
    # CTClass validation
    valid_ctclass = {'A', 'B', 'C'}
    invalid_ctclass = df[~df['ctclass'].isin(valid_ctclass)]
    if len(invalid_ctclass) > 0:
        invalid_counts = invalid_ctclass['ctclass'].value_counts()
        print(f"WARNUNG: Ungültige CTClass-Werte gefunden: {invalid_counts.to_dict()}")
    
    # CTSubType-Spalte finden (flexible Namen)
    ctsubtype_candidates = ['ctsubtype', 'ct_subtype', 'subclass', 'subtype', 'b1/b2']
    ctsubtype_col = find_col(df, ctsubtype_candidates)
    
    if ctsubtype_col:
        # B1/B2/Missing Normalisierung
        df['ctsubtype_norm'] = df[ctsubtype_col].fillna('').astype(str).str.strip().str.upper()
        df.loc[df['ctsubtype_norm'].str.startswith('B1'), 'ctsubtype_norm'] = 'B1'
        df.loc[df['ctsubtype_norm'].str.startswith('B2'), 'ctsubtype_norm'] = 'B2'
        df.loc[~df['ctsubtype_norm'].isin(['B1', 'B2']), 'ctsubtype_norm'] = 'Missing'
    else:
        print("WARNUNG: Keine CTSubType-Spalte gefunden. B-SubType-Analysen werden übersprungen.")
        df['ctsubtype_norm'] = 'Missing'
    
    # N unique Issues
    n_cudaq = cudaq_df['issueid'].nunique()
    n_qiskit = qiskit_df['issueid'].nunique()
    n_total = df['uid'].nunique()
    
    print(f"\nN unique Issues:")
    print(f"  CUDA-Q: {n_cudaq}")
    print(f"  Qiskit (GPU): {n_qiskit}")
    print(f"  Total: {n_total}")
    print()
    
    # Auswertungen
    outputs = []
    
    # 1) CTClass
    outputs.append(compute_distribution(df, 'project', 'ctclass', 'c_ctclass', by_project=False))
    outputs.append(compute_distribution(df, 'project', 'ctclass', 'c_ctclass', by_project=True))
    
    # 2) StackLayer
    outputs.append(compute_distribution(df, 'project', 'stacklayer', 'c_stacklayer', by_project=False))
    outputs.append(compute_distribution(df, 'project', 'stacklayer', 'c_stacklayer', by_project=True))
    
    # 3) BugType
    outputs.append(compute_distribution(df, 'project', 'bugtype', 'c_bugtype', by_project=False))
    outputs.append(compute_distribution(df, 'project', 'bugtype', 'c_bugtype', by_project=True))
    
    # 4) B-SubType (nur CTClass == "B")
    if ctsubtype_col:
        df_b = df[df['ctclass'] == 'B'].copy()
        if len(df_b) > 0:
            outputs.append(compute_distribution(df_b, 'project', 'ctsubtype_norm', 'c_b_subtype', by_project=False))
            outputs.append(compute_distribution(df_b, 'project', 'ctsubtype_norm', 'c_b_subtype', by_project=True))
        else:
            print("WARNUNG: Keine Issues mit CTClass == 'B' gefunden.")
    else:
        print("WARNUNG: B-SubType-Analysen übersprungen (Spalte fehlt).")
    
    print("Geschriebene Dateien:")
    for output in outputs:
        print(f"  - {output}")
    
    if not HAS_STATSMODELS:
        print("\nHINWEIS: statsmodels nicht verfügbar. Wilson-CIs wurden nicht berechnet.")


if __name__ == '__main__':
    main()
