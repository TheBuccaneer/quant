## Projektstruktur

Dieses Repository ist wie folgt organisiert:

- `docs/` – Projektbeschreibung und Codebook  
  - `concept_gpu_quantum_bugs.md` – Kurzkonzept / Studienbeschreibung  
  - `codebook_gpu_quantum_bugs.md` – Codebook für Bug-Typen und CTClass
- `data/` – Rohdaten aus GitHub  
  - `cudaq_issues_raw.csv` – Export der CUDA-Q-Bug-Issues (GitHub-Scraper)
- `scripts/` – Hilfsskripte zur Datenerhebung und -aufbereitung  
  - `cudaq_issues_scraper.py` – Skript zum Abruf der CUDA-Q-Issues
- `notes/` – Laufende Projektnotizen  
  - `project_log.md` – Chronologisches Projektlog

Derzeit fokussiert sich das Projekt auf Bug-Issues in GPU-basierten Quantum-Frameworks (z.B. CUDA-Q) und deren Klassifikation anhand eines eigenen Codebooks.
