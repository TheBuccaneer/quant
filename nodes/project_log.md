# Project Log – GPU Quantum Bugs

## 2025-12-03

- Projektstruktur angelegt (`docs/`, `data/`, `scripts/`, `notes/`).
- Codebook und Konzept nach `docs/` verschoben:
  - `docs/codebook_gpu_quantum_bugs.md`
  - `docs/concept_gpu_quantum_bugs.md`
- Scraper-Skript erstellt und nach `scripts/` gelegt:
  - `scripts/cudaq_issues_scraper.py`
- Erste Datensammlung für CUDA-Q durchgeführt:
  - GitHub-Query: `is:issue label:bug created:2023-01-01..2025-11-19`
  - Issues als CSV gespeichert: `data/cudaq_issues_raw.csv`

  