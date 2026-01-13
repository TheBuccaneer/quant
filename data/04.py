
"""
04_effect_sizes.py
Step D (optional): χ² / (optional Fisher for 2x2) + Cramér’s V for key cross-tabs.

Inputs (CSV, relative paths):
- ./Cuda-Q/cudaq_issues_raw.csv
- ./qskit/github_issues.csv

Outputs:
- e_effect_sizes.csv
"""

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# --- optional SciPy (for chi2 p-values and Fisher exact) ---
HAS_SCIPY = True
try:
    from scipy.stats import chi2_contingency, chi2 as chi2_dist, fisher_exact
except Exception:
    HAS_SCIPY = False


CUDAQ_FILE = Path("./Cuda-Q/cudaq_issues_raw.csv")
QISKIT_FILE = Path("./qskit/github_issues.csv")

# permutation settings (only used when expected counts are small OR SciPy is missing)
N_PERM = 5000
RNG_SEED = 0


def norm_col(c: str) -> str:
    c = str(c).replace("\ufeff", "").strip().lower()
    c = c.replace(" ", "_")
    return c


def load_and_prepare(path: Path, gpu_filter: bool) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    df.columns = [norm_col(c) for c in df.columns]

    # embedded header rows (targeted)
    if "issueid" in df.columns:
        df = df[df["issueid"].astype(str).str.strip().str.lower() != "issueid"]
    if "project" in df.columns:
        df = df[df["project"].astype(str).str.strip().str.lower() != "project"]

    required = ["project", "issueid", "stacklayer", "bugtype", "ctclass"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"FEHLER in {path}: Missing required columns: {missing}")
        print(f"Available: {list(df.columns)}")
        sys.exit(1)

    if gpu_filter:
        if "gpu_relevant" not in df.columns:
            print(f"FEHLER in {path}: missing 'gpu_relevant' for GPU filter")
            sys.exit(1)
        df = df[df["gpu_relevant"].fillna("").astype(str).str.strip().str.upper() == "X"].copy()

    # clean minimal
    df["project"] = df["project"].astype(str).str.strip()
    df["issueid"] = df["issueid"].astype(str).str.strip()
    df["stacklayer"] = df["stacklayer"].astype(str).str.strip()
    df["bugtype"] = df["bugtype"].astype(str).str.strip()
    df["ctclass"] = df["ctclass"].astype(str).str.strip().str.upper()

    # dedupe within file (safe)
    df = df.drop_duplicates(subset=["project", "issueid"], keep="last")

    # repo-unique key
    df["uid"] = df["project"] + "#" + df["issueid"]
    return df


def expected_counts(table: np.ndarray) -> np.ndarray:
    # expected under independence: (row_sum * col_sum) / N
    n = table.sum()
    if n == 0:
        return np.zeros_like(table, dtype=float)
    rsum = table.sum(axis=1, keepdims=True)
    csum = table.sum(axis=0, keepdims=True)
    return (rsum @ csum) / n


def chi2_stat(table: np.ndarray, exp: np.ndarray) -> float:
    mask = exp > 0
    return float(((table[mask] - exp[mask]) ** 2 / exp[mask]).sum())


def cramers_v(chi2: float, n: int, r: int, c: int) -> float:
    k = min(r, c)
    if n <= 0 or k <= 1:
        return float("nan")
    return float(np.sqrt(chi2 / (n * (k - 1))))


def permutation_pvalue(x: pd.Series, y: pd.Series, r: int, c: int, n_perm: int, seed: int) -> float:
    # Permute y relative to x => valid permutation test for independence
    rng = np.random.default_rng(seed)
    table_obs = pd.crosstab(x, y).to_numpy()
    exp_obs = expected_counts(table_obs)
    chi2_obs = chi2_stat(table_obs, exp_obs)

    y_vals = y.to_numpy(copy=True)
    count_ge = 0
    for _ in range(n_perm):
        rng.shuffle(y_vals)
        tab = pd.crosstab(x, y_vals).to_numpy()
        exp = expected_counts(tab)
        chi2_sim = chi2_stat(tab, exp)
        if chi2_sim >= chi2_obs:
            count_ge += 1
    return (count_ge + 1) / (n_perm + 1)


def analyze_table(df: pd.DataFrame, row_var: str, col_var: str, name: str) -> dict:
    # drop missing values for the two variables
    sub = df[[row_var, col_var, "uid"]].copy()
    sub[row_var] = sub[row_var].replace("", pd.NA)
    sub[col_var] = sub[col_var].replace("", pd.NA)
    sub = sub.dropna(subset=[row_var, col_var])

    n_used = sub["uid"].nunique()
    ct = pd.crosstab(sub[row_var], sub[col_var])
    table = ct.to_numpy()
    r, c = table.shape
    n = int(table.sum())

    exp = expected_counts(table)
    min_exp = float(np.min(exp)) if exp.size else float("nan")
    chi2 = chi2_stat(table, exp)

    p_chi2 = float("nan")
    dof = int((r - 1) * (c - 1))

    if HAS_SCIPY and n > 0 and r > 1 and c > 1:
        # no Yates correction; we want consistent chi2 for V
        chi2_s, p_s, dof_s, exp_s = chi2_contingency(table, correction=False)
        chi2 = float(chi2_s)
        p_chi2 = float(p_s)
        dof = int(dof_s)
        min_exp = float(np.min(exp_s))

    v = cramers_v(chi2, n, r, c)

    # Fisher exact only for 2x2
    p_fisher = float("nan")
    if HAS_SCIPY and r == 2 and c == 2:
        _, p_fisher = fisher_exact(table)

    # permutation p-value if expected counts small OR SciPy missing
    p_perm = float("nan")
    if (not HAS_SCIPY) or (min_exp < 5):
        # build x,y series aligned with sub
        p_perm = float(permutation_pvalue(sub[row_var], sub[col_var], r, c, N_PERM, RNG_SEED))

    return {
        "test": name,
        "row_var": row_var,
        "col_var": col_var,
        "n_used_uid": int(n_used),
        "shape_rxc": f"{r}x{c}",
        "chi2": round(chi2, 4),
        "dof": dof,
        "p_chi2": p_chi2 if np.isnan(p_chi2) else round(p_chi2, 6),
        "p_perm": p_perm if np.isnan(p_perm) else round(p_perm, 6),
        "p_fisher_2x2": p_fisher if np.isnan(p_fisher) else round(p_fisher, 6),
        "cramers_v": round(v, 4) if not np.isnan(v) else float("nan"),
        "min_expected": round(min_exp, 4) if not np.isnan(min_exp) else float("nan"),
    }


def main() -> None:
    print("Loading data...")
    cudaq = load_and_prepare(CUDAQ_FILE, gpu_filter=False)
    qiskit = load_and_prepare(QISKIT_FILE, gpu_filter=True)

    df = pd.concat([cudaq, qiskit], ignore_index=True)

    # keep only valid CTClass
    valid = {"A", "B", "C"}
    invalid = df.loc[~df["ctclass"].isin(valid), "ctclass"].value_counts()
    if len(invalid) > 0:
        print(f"WARNUNG: invalid CTClass values dropped: {invalid.to_dict()}")
        df = df[df["ctclass"].isin(valid)].copy()

    # quick N
    n_cudaq = int(cudaq["uid"].nunique())
    n_qiskit = int(qiskit["uid"].nunique())
    n_total = int(df["uid"].nunique())
    print(f"N (uid unique): CUDA-Q={n_cudaq}, Qiskit(GPU)={n_qiskit}, Total={n_total}")

    results = []
    results.append(analyze_table(df, "project", "ctclass", "Project × CTClass"))
    results.append(analyze_table(df, "stacklayer", "ctclass", "StackLayer × CTClass"))
    results.append(analyze_table(df, "bugtype", "ctclass", "BugType × CTClass"))

    out = pd.DataFrame(results)
    out_file = "e_effect_sizes.csv"
    out.to_csv(out_file, index=False)

    print(f"Wrote: {out_file}")
    if not HAS_SCIPY:
        print("NOTE: SciPy not available -> chi2 p-values are NaN; permutation p-values were computed instead where applicable.")
    else:
        print(f"NOTE: permutation p-values computed when min_expected < 5 (N_PERM={N_PERM}).")


if __name__ == "__main__":
    main()
