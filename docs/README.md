# Analysis scripts

## Requirements
- Python 3.x
- pandas

## Input data
- ./Cuda-Q/cudaq_issues_raw.csv
- ./qskit/github_issues.csv

## Scripts

### 01_amount_of_issues.py
Purpose: Create dataset overview statistics (Table 1).
Inputs:
- cudaq_issues_raw.csv
- github_issues.csv
Processing:
- Normalizes column names (lowercase, strip spaces)
- Removes accidental duplicated header rows (caused by appended exports)
- Deduplicates by IssueID (keeps last occurrence)
- Parses CreatedAt timestamps
- Normalizes Status (open/closed)
- Filters Qiskit issues to gpu_relevant == True (accepts variants like True/1/yes/X)
Outputs:
- Console summary (N total, N per repo, createdAt range, open/closed counts)
- table1_dataset_overview.csv


## 02.py — Core distributions (Step C)

**Purpose:**  
Compute the core descriptive statistics used in the paper (Step C), based on the manually coded GitHub issue datasets.

**Inputs (CSV):**
- `./Cuda-Q/cudaq_issues_raw.csv`
- `./qskit/github_issues.csv`

**Inclusion rules:**
- CUDA-Q: include all issues.
- Qiskit Aer: include only GPU-relevant issues (filtered via `gpu_relevant`, e.g., marked with `X`).

**Processing (high-level):**
- Normalizes column names (strip/BOM removal, lowercase, spaces → underscores).
- Removes accidental embedded header rows (e.g., `IssueID == "IssueID"`).
- Deduplicates by issue ID (keeps the last occurrence if files were appended).
- Creates a repo-unique issue key (`project#issueid`) to avoid collisions across repositories.
- Cleans label strings (strip/uppercase for CTClass).
- Normalizes B-subtypes to `B1`/`B2` (and handles missing values if present).
- Optionally computes 95% Wilson confidence intervals for proportions (if `statsmodels` is installed).

**Outputs (CSV):**
- `c_ctclass_overall.csv`, `c_ctclass_by_project.csv`
- `c_stacklayer_overall.csv`, `c_stacklayer_by_project.csv`
- `c_bugtype_overall.csv`, `c_bugtype_by_project.csv`
- `c_b_subtype_overall.csv`, `c_b_subtype_by_project.csv`

**How to run:**
```bash
python 02.py

### 03_cross_tabs.py — Cross tabs / story analyses (Step D)

**Purpose:**  
Generate the main cross-tabulations used for the paper’s “story” analysis (Step D), i.e., how CTClass varies across stack layers, bug types, and projects.

**Inputs (CSV):**
- `./Cuda-Q/cudaq_issues_raw.csv`
- `./qskit/github_issues.csv`

**Inclusion rules:**
- CUDA-Q: include all issues.
- Qiskit Aer: include only GPU-relevant issues (`gpu_relevant == "X"`).

**Processing (high-level):**
- Normalizes column names (strip, lowercase, BOM removal, spaces → underscores).
- Removes embedded header rows (checks `issueid == "IssueID"` and `project == "Project"`).
- Deduplicates by `(project, issueid)` (keeps last occurrence).
- Creates a repo-unique issue key `uid = project#issueid`.
- Cleans labels (`ctclass` uppercased; `stacklayer`, `bugtype`, `project` stripped).
- Produces cross-tabs as **counts** and **row-wise percentages** (percentages sum to ~100 per row, rounding to 1 decimal).

**Outputs (CSV):**
- StackLayer × CTClass:
  - `d_layer_x_ctclass_overall_counts.csv`
  - `d_layer_x_ctclass_overall_pct.csv`
  - `d_layer_x_ctclass_by_project_counts.csv`
  - `d_layer_x_ctclass_by_project_pct.csv`
- BugType × CTClass:
  - `d_bugtype_x_ctclass_overall_counts.csv`
  - `d_bugtype_x_ctclass_overall_pct.csv`
  - `d_bugtype_x_ctclass_by_project_counts.csv`
  - `d_bugtype_x_ctclass_by_project_pct.csv`
- Project × CTClass:
  - `d_project_x_ctclass_overall_counts.csv`
  - `d_project_x_ctclass_overall_pct.csv`
- Label audit (sanity check):
  - `d_audit_unique_labels.csv` (unique label counts for stacklayer/bugtype overall and per project)

**How to run:**
```bash
python 03_cross_tabs.py




### 04.py — Effect sizes for key cross-tabs (Step D, optional)

**Purpose:**  
Compute effect sizes (Cramér’s V) and significance estimates for the three main cross-tabulations used in the paper:
- Project × CTClass  
- StackLayer × CTClass  
- BugType × CTClass

**Inputs (CSV):**
- `./Cuda-Q/cudaq_issues_raw.csv`
- `./qskit/github_issues.csv`

**Inclusion rules:**
- CUDA-Q: include all issues.
- Qiskit Aer: include only GPU-relevant issues (`gpu_relevant == "X"`).

**Processing (high-level):**
- Normalizes column names and removes embedded header rows.
- Deduplicates by `(project, issueid)` and creates a repo-unique key (`project#issueid`).
- Builds the three contingency tables and computes:
  - χ² statistic (uncorrected) and expected cell counts
  - **Cramér’s V** as effect size
  - Permutation p-value (5,000 permutations, seed=0) when expected counts are small (or when SciPy is not available)
  - Fisher’s exact test for 2×2 tables (only when applicable)

**Output (CSV):**
- `e_effect_sizes.csv` (one row per test, incl. `cramers_v`, `p_perm`, and `min_expected`)

**How to run:**
```bash
python 04.py


### make_fig1.py — Figure 1 (CTClass distribution)

**Purpose:**  
Generate *Figure 1* as a publication-ready 2-panel plot:
- (A) Overall CTClass distribution (counts + percentages)
- (B) CTClass distribution by project as 100% stacked bars (percentages + per-project N)

**Inputs (CSV):**  
(Produced by prior analysis steps)
- `c_ctclass_overall.csv` (from Step C / `02.py`)
- `d_project_x_ctclass_overall_pct.csv` (from Step D / `03_cross_tabs.py`)
- `d_project_x_ctclass_overall_counts.csv` (from Step D / `03_cross_tabs.py`)

**Processing (high-level):**
- Validates totals (overall count matches `total` column within tolerance).
- Validates that per-project percentages sum to ~100%.
- Enforces fixed CTClass order A/B/C.
- Applies consistent color mapping and panel labels.

**Outputs:**
- `figures/fig1_ctclass.pdf`
- `figures/fig1_ctclass.png` (300 dpi)

**How to run:**
```bash
python make_fig1.py
