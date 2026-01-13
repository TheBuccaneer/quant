import pandas as pd

# IMPORTANT: paths must be strings (NOT pd.read_csv(...))
CUDAQ_FILE = r"./Cuda-Q/cudaq_issues_raw.csv"
QISKIT_FILE = r"./qskit/github_issues.csv"


def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=False)  # BOM
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    return df


def drop_embedded_headers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # If a second header row was appended into the data
    if "issueid" in df.columns:
        df = df[df["issueid"].astype(str).str.strip().str.lower() != "issueid"]
    if "project" in df.columns:
        df = df[df["project"].astype(str).str.strip().str.lower() != "project"]
    return df


def dedupe_keep_last(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "issueid" in df.columns:
        df["_row"] = range(len(df))
        df = df.sort_values("_row").drop(columns=["_row"])
        df = df.drop_duplicates(subset=["issueid"], keep="last")
    return df


def parse_common(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["status_norm"] = df.get("status", "").astype(str).str.strip().str.lower()
    df["createdat_parsed"] = pd.to_datetime(df.get("createdat"), errors="coerce", utc=True)
    return df


def parse_gpu_relevant(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "gpu_relevant" not in df.columns:
        df["gpu_relevant_bool"] = True
        return df

    v = df["gpu_relevant"].fillna("").astype(str).str.strip().str.lower()

    # Accept lots of common encodings, incl. "x" marking
    true_set = {"true", "1", "yes", "y", "x", "gpu", "g"}
    false_set = {"false", "0", "no", "n", ""}

    df["gpu_relevant_bool"] = v.map(lambda s: True if s in true_set else (False if s in false_set else False))
    return df


def summarize(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[
            "dataset","project","n_issues","start","end","n_closed","closed_pct","n_open","open_pct"
        ])

    g = df.groupby("project", dropna=False)

    out = g.agg(
        n_issues=("issueid", "nunique"),
        n_closed=("status_norm", lambda s: int((s == "closed").sum())),
        n_open=("status_norm", lambda s: int((s == "open").sum())),
        start=("createdat_parsed", "min"),
        end=("createdat_parsed", "max"),
    ).reset_index()

    # ensure numeric
    for c in ["n_issues", "n_closed", "n_open"]:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0).astype(int)

    out["closed_pct"] = (out["n_closed"] / out["n_issues"] * 100).astype(float).round(1)
    out["open_pct"] = (out["n_open"] / out["n_issues"] * 100).astype(float).round(1)

    out.insert(0, "dataset", dataset_name)
    return out


def main():
    cudaq = pd.read_csv(CUDAQ_FILE, dtype=str, encoding="utf-8-sig")
    qiskit = pd.read_csv(QISKIT_FILE, dtype=str, encoding="utf-8-sig")

    cudaq = parse_common(dedupe_keep_last(drop_embedded_headers(normalize_cols(cudaq))))
    qiskit = parse_common(dedupe_keep_last(drop_embedded_headers(normalize_cols(qiskit))))
    qiskit = parse_gpu_relevant(qiskit)

    qiskit_gpu = qiskit[qiskit["gpu_relevant_bool"] == True].copy()

    # Debug if filter kills everything
    if qiskit_gpu.empty and "gpu_relevant" in qiskit.columns:
        print("WARNING: After filtering gpu_relevant_bool, Qiskit GPU set is empty.")
        print("Unique raw gpu_relevant values (top 20):")
        print(qiskit["gpu_relevant"].fillna("").astype(str).str.strip().value_counts().head(20))

    N_cudaq = cudaq["issueid"].nunique()
    N_qiskit = qiskit_gpu["issueid"].nunique()
    print(f"N CUDA-Q: {N_cudaq}")
    print(f"N Qiskit (GPU): {N_qiskit}")
    print(f"N total: {N_cudaq + N_qiskit}")

    s_cudaq = summarize(cudaq, "CUDA-Q")
    s_qiskit = summarize(qiskit_gpu, "Qiskit (GPU-relevant)")

    summary = pd.concat([s_cudaq, s_qiskit], ignore_index=True)

    cols = ["dataset","project","n_issues","start","end","n_closed","closed_pct","n_open","open_pct"]
    print("\nPer Project/Repo summary (Table 1 draft):")
    print(summary[cols].to_string(index=False))

    summary.to_csv("table1_dataset_overview.csv", index=False)
    print("\nSaved: table1_dataset_overview.csv")


if __name__ == "__main__":
    main()
