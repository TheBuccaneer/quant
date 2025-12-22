# Codebook – GPU-Accelerated Quantum Stack Bugs

## 1. Bug-Typen (What)

+----+--------------------------------------+-------------------------------------------+---------------------------+
| ID | Bug-Typ                              | Kurzbeschreibung                           | Typische CTClass-Tendenz  |
+----+--------------------------------------+-------------------------------------------+---------------------------+
| 1  | Config-/Environment-Bug             | Falsche / inkompatible Umgebung,          | Häufig C, manchmal B      |
|    |                                      | Treiber, CUDA-Versionen, fehlende         | (z.B. wenn bessere        |
|    |                                      | Libraries, Container-/Cluster-Config.     | Checks im Build helfen).  |
+----+--------------------------------------+-------------------------------------------+---------------------------+
| 2  | Build-/Install-/Packaging-Bug       | Fehler in Build-Skripten, Installer,      | Oft B, gelegentlich A oder|
|    |                                      | Paket-Setup, Dependency-Deklarationen     | C (je nach Natur des      |
|    |                                      | (pip/uv/conda/Wheels, Linker-Probleme).   | Problems).                |
+----+--------------------------------------+-------------------------------------------+---------------------------+
| 3  | Backend-/Framework-Integrations-Bug | Probleme im Zusammenspiel von Framework   | Häufig B (A/B-Grenzfälle),|
|    |                                      | und Backends (falsche Target-Selection,   | z.T. C, wenn stark von    |
|    |                                      | Initialisierung von GPU-Backends,         | Runtime-Hardware abhängig.|
|    |                                      | Inkompatible Schnittstellen).             |                           |
+----+--------------------------------------+-------------------------------------------+---------------------------+
| 4  | API-/Usage-/Logic-Bug (High-Level)  | Fehlgebrauch von High-Level-APIs,         | Eher A oder B, da viele   |
|    |                                      | falsche Vorbedingungen, typische          | Fehler durch Typen/       |
|    |                                      | Logik-/Algorithmusfehler im User-Code.    | Contracts auffindbar sind.|
+----+--------------------------------------+-------------------------------------------+---------------------------+
| 5  | Performance-/Numerik-Bug            | Performance-Degradation, falsche          | Meist B oder C: häufig    |
|    |                                      | Komplexität, numerische Instabilität,     | Analyse-/Design- oder     |
|    |                                      | Precision-/Rundungsprobleme.              | Runtime-Fragen.           |
+----+--------------------------------------+-------------------------------------------+---------------------------+
| 6  | Sonstige / Uncategorized            | Fälle, die nicht gut in die obigen        | Hängt vom konkreten Fall  |
|    |                                      | Kategorien passen; werden genutzt,        | ab; zunächst offen lassen.|
|    |                                      | um das Codebook weiterzuentwickeln.       |                           |
+----+--------------------------------------+-------------------------------------------+---------------------------+


### Überblick der Bug-Kategorien (Arbeitsversion)

Die folgenden Bug-Kategorien sind eine erste Arbeitsversion und werden im
Rahmen des Pilot-Codings (Phase 1) getestet und ggf. angepasst:

1. Config-Environment-Bug  
   → Probleme durch falsche oder inkompatible Umgebung, Treiber, CUDA-Versionen,
   fehlende Bibliotheken, fehlerhafte Container-/Cluster-Configs, etc.

2. Build-Install-Packaging-Bug  
   → Fehler im Build-System, bei der Installation oder im Packaging
   (z.B. falsche oder dynamische Dependency-Deklarationen, Probleme mit
   `pip`/`uv`/Wheels, falsch verlinkte Bibliotheken).

3. Backend-Framework-Integrations-Bug  
   → Probleme im Zusammenspiel zwischen Framework und Backend(s), z.B.
   falsche Auswahl von Targets/Simulators, fehlerhafte Initialisierung von
   GPU-Backends, Inkonsistenzen zwischen Python-/C++-API und internen
   Implementierungen.

4. API-Usage-Logic-Bug (High-Level)  
   → Fehlgebrauch von High-Level-APIs, falsche Annahmen über Semantik,
   typische Logik- oder Algorithmusfehler in Quantum-Programmen, die nicht
   primär von der Umgebung abhängen.

5. Performance-Numerik-Bug  
   → Bugs, bei denen die Hauptursache in Performance-Degradierung, falscher
   Komplexität oder numerischen Problemen (z.B. Instabilitäten, Overflow,
   unerwarteter Precision-Loss) liegt.

6. Sonstige - Uncategorized  
   → Fälle, die nicht gut in die obigen Kategorien passen; werden im Verlauf
   des Pilot-Codings genutzt, um zu entscheiden, ob neue Kategorien nötig sind
   oder bestehende erweitert werden müssen.


### 1.1 Config-Environment-Bug

**Arbeitsdefinition:**  
Ein Bug, bei dem die Hauptursache in der Systemumgebung, Installation oder
Konfiguration liegt – z.B. inkompatible CUDA-/Treiber-Versionen, fehlende
Bibliotheken, falsch gewählte Container-Images oder nicht aktivierte Features
(MPI, GPU-Support, etc.).

**Typische Indikatoren:**
- Fehlermeldungen nennen explizit CUDA-/Treiber-/Runtime-Versionen
  (z.B. „unsatisfied condition: cuda>=…“, fehlende `libcublas.so.X` etc.). :contentReference[oaicite:1]{index=1}  
- Das Problem tritt nur in bestimmten Umgebungen / Images / Installationspfaden
  auf (z.B. Docker-Image, bestimmtes Linux-Release). :contentReference[oaicite:2]{index=2}  
- Workarounds bestehen aus „Environment fixen“ (Treiber updaten, andere CUDA-
  Version verwenden, anderes Paket/Install-Tool wählen). :contentReference[oaicite:3]{index=3}  

**Beispiele (Pilot-Issues):**
- #3523 – CUDA-Q Docker-Image mit GPU-Support verlangt CUDA >= 12.6, Treiber ist älter → Container-Start schlägt fehl. :contentReference[oaicite:4]{index=4}  
- #1718 – Installer baut gegen CUDA 11, aber System hat nur CUDA 12 Runtime → `libcublas.so.11` fehlt zur Laufzeit. :contentReference[oaicite:5]{index=5}  
- #920 – MPI ist in den Python-Wheels nicht aktiviert, `cudaq.mpi`-APIs sind nur Stubs (fehlende Build-/Env-Konfiguration). :contentReference[oaicite:6]{index=6}  

**Hinweis für Coding:**  
Wenn unklar ist, ob es sich um einen reinen Config-/Env-Bug oder um einen
Build-/Install-Bug handelt, wird zunächst geprüft, ob das Problem allein durch
Anpassen der Umgebung (Treiber, CUDA-Version, Paketwahl, Flags) lösbar ist.
Falls ja, wird es als Config-/Environment-Bug kodiert.

### 1.2 Build-Install-Packaging-Bug

**Arbeitsdefinition:**  
Ein Bug, bei dem die Hauptursache im Build- oder Installationsprozess oder im
Packaging liegt – z.B. fehlerhafte oder dynamisch ermittelte Dependency-
Deklarationen, Probleme mit Paket-Managern (`pip`, `uv`, `conda`, …),
inkonsistente Binary-/Library-Versionen oder Metapackages, die nicht alle
benötigten Komponenten installieren.

**Typische Indikatoren:**
- Der Fehler tritt bereits bei Installation oder erstem Import eines Pakets auf
  (z.B. fehlende Module/Bibliotheken, unvollständige Wheels/SDists).
- Unterschiedliche Paketmanager oder Installationswege (z.B. `pip` vs. `uv`,
  `pip` vs. `conda`) führen zu unterschiedlichen oder kaputten Installationen.
- Workarounds bestehen aus „anders installieren“ (anderer Paketmanager, explizite
  Dependencies nachinstallieren, alternative Channel/Index verwenden), ohne die
  eigentliche Programmlogik zu verändern.

**Beispiele (Pilot-Issues):**
- CUDA-Q + uv (`uv pip install cudaq`): Beim ersten Aufruf wird nur `cudaq`
  installiert, Dependencies fehlen; erst ein zweiter Aufruf installiert die
  vollständige Abhängigkeitsmenge.
- CUDA-Q #3616 (sinngemäß): Dynamische `install_requires` im `setup.py`
  interagieren schlecht mit modernen Tools, die statische Metadaten erwarten.
- Fälle, in denen Python-Wheels bzw. Installer bestimmte Komponenten nicht
  mitbringen, obwohl die Doku etwas anderes suggeriert.

**Abgrenzung zu 1.1 Config-/Environment-Bug:**  
Wenn das Problem primär daher rührt, dass die *Umgebung* nicht zu den
Anforderungen passt (Treiber zu alt, falsche CUDA-Version, fehlende System-
Library), kodieren wir es als Config-/Environment-Bug (1.1).  
Wenn hingegen der *Build-/Install-Prozess selbst* kaputt oder unvollständig
ist (Metapackage falsch geschnürt, dynamische Dependencies, kaputte Wheels),
kodieren wir es als Build-/Install-/Packaging-Bug (1.2).

### 1.3 Backend-Framework-Integrations-Bug

**Arbeitsdefinition:**  
Ein Bug, bei dem die Hauptursache im Zusammenspiel zwischen Framework und
Backend(s) liegt. Typischerweise funktioniert jede Komponente für sich
genommen „korrekt“, aber die Integration – also wie Backends ausgewählt,
initialisiert, konfiguriert oder aufgerufen werden – schlägt fehl. Beispiele
sind falsche Default-Targets, inkonsistente Schnittstellen zwischen Python-
und C++-Layer oder Fehler bei der Initialisierung von GPU-Backends.

**Typische Indikatoren:**
- Der Fehler tritt nur auf, wenn ein bestimmtes Backend (z.B. GPU-Simulator,
  Hardware-Backend, custatevec) aktiv ist, nicht aber mit einem anderen
  Backend (z.B. CPU-/qpp-Simulator).
- Workarounds bestehen aus „anderes Backend wählen“ oder „Environment-Variable
  setzen, um ein anderes Target zu erzwingen“, ohne den eigentlichen
  Algorithmus zu ändern.
- Fehlermeldungen stammen aus der Backend-Schicht, werden aber durch das
  Framework ausgelöst (z.B. bei Backend-Selection oder -Initialisierung).

**Beispiele (Pilot-Issues):**
- CUDA-Q #977: Python-Backend-Tests schlagen nur dann mit `custatevec`-Errors
  fehl, wenn ein GPU-Backend verwendet wird; setzt man dagegen
  `CUDAQ_DEFAULT_SIMULATOR=qpp-cpu`, laufen die Tests durch.  
- CUDA-Q #2357: `cudaq.kernels.uccsd` funktioniert auf Simulator-Backends,
  scheitert aber auf bestimmten Hardware-Backends mit einem MLIR-
  Unrolling-Fehler, was auf Unterschiede in den Backend-Fähigkeiten und
  deren Anbindung hindeutet.

**Abgrenzung:**  
- Wenn die Ursache in der Umgebung oder Installation liegt (Treiber, CUDA,
  fehlende Bibliotheken), wird der Bug als Config-/Environment- oder Build-/
  Install-Bug kodiert (1.1 / 1.2).
- Wenn die Ursache in der reinen User-Logik oder API-Nutzung liegt (falsche
  Parameter, falsche Verwendung von Gradienten-APIs etc.), fällt der Bug
  in die Kategorie 1.4 „API-/Usage-/Logic-Bug (High-Level)“.
- 1.3 wird verwendet, wenn das Problem im „Dazwischen“ liegt: das Framework
  delegiert an ein Backend, aber die Integration (Target-Auswahl,
  Initialisierung, Schnittstelle) ist fehlerhaft oder unzureichend
  abgestimmt.

### 1.4 API-Usage-Logic-Bug (High-Level)

**Arbeitsdefinition:**  
Ein Bug, bei dem die Hauptursache in der Verwendung von High-Level-APIs oder
in der Programmlogik des Quantum-Programms liegt. Dazu gehören typische
Fehlbedienungen von Funktionen (z.B. falsche Rückgabetypen, fehlende
`expval`-Aufrufe), missverstandene Semantiken (z.B. Broadcast-Verhalten,
Shape-Konventionen von Gradienten) oder klassische Logik-/Algorithmusfehler
im (hybriden) Quantum-Code.

**Typische Indikatoren:**
- Der Fehler lässt sich auf falsche oder unpassende Nutzung einer API
  zurückführen (z.B. falsche Kombination von Messungen, Gradienten, Interfaces
  oder Rückgabetypen).
- Die Umgebung/Installation ist korrekt; der Fehler tritt auch in „sauberen“
  Setups reproduzierbar auf, solange der gleiche Code/Workflow verwendet wird.
- Fehlermeldungen weisen explizit auf API-Verträge hin (z.B. „Grad only applies
  to real scalar-output functions“) oder auf Shape-/Typ-Mismatches im User-
  Code (z.B. unerwartete Tensor-Formen bei Gradienten/Jacobians).

**Beispiele (Pilot-Issues):**
- PennyLane #4462: Gradient-Berechnung für einen broadcasted QNode führt zu
  einem Shape-Mismatch zwischen erwarteter und tatsächlicher Jacobian-Form;
  das Problem liegt in der Kombination aus API-Semantik (Broadcast) und
  Gradient-Transform-Implementierung.
- PennyLane Discuss „Grad only applies to real scalar-output functions“:
  Ein QNode gibt einen Vektor von Erwartungswerten zurück, `grad` erwartet
  jedoch eine skalare Ausgabe – ein typischer Misuse der Differentiations-API.
- PennyLane Discuss „TypeError while computing the gradient“ (nested grads):
  Verschachtelte `grad`-Aufrufe führen zu Typkonflikten (AutoDiff-Typen vs.
  erwartete Floats) und zeigen ein fortgeschrittenes API-Usage-Problem.

**Abgrenzung:**  
- Wenn der gleiche Code mit einem anderen Backend (oder auf anderer Hardware)
  zwar langsamer oder instabiler, aber semantisch korrekt ist, kann es sich
  eher um einen Performance-/Numerik-Bug handeln (1.5), nicht um einen
  API-/Usage-Bug.
- Wenn der Fehler auch ohne jeden Quantum-spezifischen Kontext als „klassischer
  Logic-/API-Fehler“ erkennbar wäre (falscher Rückgabetyp, Shape-Fehler,
  falsche Funktion verwendet), ist 1.4 in der Regel angemessen.
- Wenn hingegen ausschließlich das Zusammenspiel zwischen Framework und
  Backend fehlschlägt (z.B. nur bestimmtes Target betroffen, andere Targets
  funktionieren), sollte eher 1.3 „Backend-/Framework-Integrations-Bug“
  gewählt werden.

### 1.5 Performance-Numerik-Bug

**Arbeitsdefinition:**  
Ein Bug, bei dem die Hauptursache in Performance- oder numerikbezogenen
Eigenschaften des Systems liegt – z.B. starke Verlangsamungen, Memory Leaks,
unerwartet hohe Ressourcen-Nutzung oder numerisch instabile bzw. ungenaue
Ergebnisse (z.B. durch Floating-Point-Grenzen, Mixed Precision, Rundungsfehler).

**Typische Indikatoren:**
- Metriken wie Laufzeit, Speicherverbrauch, Throughput oder Skalierung
  verhalten sich deutlich schlechter als erwartet (z.B. Regression zu einer
  früheren Version, exponentielles Wachstum statt linearem).
- Wiederholte Ausführung eines Codes führt zu ständig wachsender
  Speichernutzung (Memory Leak), bis ein Out-of-Memory-/Allocation-Fehler
  auftritt.
- Ergebnisse sind numerisch instabil oder offensichtlich falsch, obwohl die
  Logik an sich korrekt scheint (z.B. nur bei sehr kleinen Winkeln, bei
  bestimmten Qubit-Zahlen, bei Mixed-Precision-Training).

**Beispiele (Pilot-Issues):**
- CUDA-Q #1909: `cudaq.observe` führt in einem VQE-artigen Loop zu einem
  stetigen Anstieg der Speichernutzung (Memory Leak) und gefährdet lange
  Optimierungsläufe.
- CUDA-Q #1770: Wiederholte `cudaq.sample`-Aufrufe führen nach vielen
  Iterationen zu „Cannot allocate memory“ / Kernel-Shutdown.
- CUDA-Q #2437: Zwischen zwei Versionen von CUDA-Q werden `SpinOperator`-
  Erzeugung und `cudaq.observe` für große Hamiltonians massiv langsamer
  (Performance-Regression).
- PennyLane Mixed-Precision-Thread: Training mit FP16 führt zu numerischer
  Instabilität bei bestimmten Operationen / Winkeln.

**Abgrenzung:**
- Wenn der Hauptfokus auf „läuft überhaupt vs. läuft gar nicht“ liegt, und die
  Ursache klar Installation/Config ist, eher 1.1 / 1.2.
- Wenn die Ursache in API-Misuse oder Logik liegt (falscher Algorithmus,
  falsche Formel), eher 1.4.
- 1.5 wird verwendet, wenn der Code im Prinzip „funktioniert“, aber
  Performance-/Ressourcen- oder Numerik-Eigenschaften das Problem sind.

### 1.6 Sonstige - Uncategorized

**Arbeitsdefinition:**  
Auffang-Kategorie für Bugs, die nicht sinnvoll in eine der vorherigen
Bug-Typen (1.1–1.5) passen. Diese Kategorie wird vor allem in der frühen
Phase des Codings genutzt, um Grenzfälle zu markieren und später zu
entscheiden, ob neue Kategorien nötig sind oder bestehende erweitert werden
sollten.

**Typische Indikatoren:**
- Das Issue betrifft vor allem Themen wie Debugging-/Logging-Infrastruktur,
  Testframeworks, sehr framework-spezifische Edge Cases oder exotische
  Tooling-Probleme, die keine klare Zuordnung zu Config, Build, Integration,
  API/Usage oder Performance/Numerik erlauben.
- Der Bug ist extrem speziell (z.B. nur bei exakt einer bestimmten
  Qubit-Zahl oder nur in Kombination mit einem speziellen externen Tool)
  und würde eine eigene Kleinst-Kategorie erfordern.

**Beispiele (Pilot-Fälle):**
- Framework-spezifische „Edge Cases“, bei denen z.B. nur eine ganz bestimmte
  Qubit-Zahl oder Backend-Kombination zu inkonsistenten Gradienten führt,
  ohne dass klar ist, ob es primär ein Performance-, API- oder Integrations-
  problem ist.
- Bugs, die sich fast ausschließlich in Hilfs-Tools (Visualizer, Logger,
  Debugger) manifestieren, ohne direkten Bezug zur Kernrechenlogik.

**Abgrenzung und Nutzungshinweis:**
- 1.6 sollte **sparsam** verwendet werden: nur dann, wenn eine sinnvolle
  Zuordnung zu 1.1–1.5 auch nach genauer Betrachtung nicht möglich ist.
- Fälle in 1.6 sind besonders interessant für die Weiterentwicklung des
  Codebooks: Häufen sich ähnliche „Sonstige“-Bugs, kann daraus eine neue
  reguläre Kategorie entstehen.



## 2. Stack-Schicht (Where)

### 2.1 Build-Deploy-Environment

**Arbeitsdefinition:**  
Diese Schicht umfasst alles rund um Installation, Packaging, Build-System,
Container, Treiber-Setup und Laufzeitumgebung (z.B. Docker-Images, Installer,
Python-Wheels, Systembibliotheken, Umgebungsvariablen).

**Typische Artefakte:**
- Installer-Skripte, Dockerfiles, Container-Images
- Paketmanager-Konfiguration (pip, uv, conda, apt, ...)
- Systembibliotheken und Laufzeitumgebung (CUDA-Runtimes, Treiber, MPI)

**Fragen beim Codieren:**
- Geht es primär darum, wie CUDA-Q/cuQuantum installiert oder gestartet wird?
- Dreht sich der Fehler um fehlende oder inkompatible Bibliotheken/Versionen
  (z.B. bestimmte CUDA- oder Treiberversionen)?
- Tritt der Fehler auf, bevor ein konkreter Quantum-Kernel oder eine
  High-Level-API-Funktion ausgeführt wird?

**Beispiele (Pilot-Issues):**
- #3523 – Container mit GPU-Support kann nicht gestartet werden, weil die
  installierte CUDA-/Treiber-Version das geforderte Minimum nicht erfüllt.
- #1718 – Installer wurde gegen CUDA 11 gebaut, das System stellt nur eine
  CUDA-12-Runtime bereit; eine benötigte Bibliothek fehlt zur Laufzeit.
- #3616 – Installation von `cudaq` mit `uv` schlägt fehl, weil das Packaging
  bzw. die Dependency-Deklaration nicht mit dem Tool kompatibel ist.
- #920 – MPI-Unterstützung ist in den Python-Wheels nicht aktiviert; die
  entsprechenden `cudaq.mpi`-APIs sind nur Stubs.

**Abgrenzung:**  
Wenn der eigentliche Fehler erst während der Ausführung eines spezifischen
Kernels oder einer Algorithmus-Logik auftritt und nicht primär durch Setup
oder Installation ausgelöst wird, wird eher eine andere Schicht gewählt
(z.B. Framework-Integration oder High-Level-API).


### 2.2 Backend-Library

**Definition:**  
Diese Kategorie umfasst Bugs, deren primäre Ursache in der **Backend-nahen Implementierung** liegt – also Bibliotheken, die eigentliche Rechenkerne, Lineare Algebra, Statevector-/Tensor-Operationen oder Code-Generierung bereitstellen. Beispiele sind u.a. **cuStateVec, cuTensorNet, qpp, MLIR/LLVM-Codegen-Pfade** oder vergleichbare Low-Level-Backends.

**Typische Indikatoren:**

- Der Fehler tritt **unabhängig von der High-Level-API** auf, sobald ein bestimmtes Backend verwendet wird.
- Das Issue bezieht sich explizit auf eine Backend-Komponente (z.B. `custatevec`, „statevector backend“, „tensornet backend“, „MLIR lowering“).
- Es geht um falsche Resultate, Crashes oder Exceptions, die auf **numerische Kerne, Low-Level-Kernels oder Code-Generierung** zurückzuführen sind.

**Abgrenzung:**

- Wenn das Problem nur bei **einem bestimmten Backend** auftritt, obwohl die High-Level-Aufrufe korrekt sind → eher **Backend-Library** als High-Level-API.
- Wenn die Ursache in falscher Backend-Auswahl oder -Initialisierung liegt (z.B. falsches Device, Backend nicht geladen), ist das eher **2.3 Framework-Integration**.

**Beispiele (schematisch):**

- Falsche Simulationsergebnisse nur im `custatevec`-Backend, andere Backends liefern korrekte Werte.
- Crash in einem bestimmten MLIR-Lowering-Pass bei validem Input.

---

### 2.3 Framework-Integration

**Definition:**  
Diese Kategorie umfasst Bugs im **Zusammenspiel zwischen High-Level-Framework (Python-/C++-API)** und den darunterliegenden Backends. Es geht um Fehler in **Backend-Selection, Initialisierung, Konfiguration und Aufruf der Backends** durch das Framework.

**Typische Indikatoren:**

- Der Bug tritt nur auf, wenn ein **bestimmtes Backend über die Framework-API ausgewählt** wird (z.B. `--target`, `set_backend(...)`).
- Fehlermeldungen deuten auf **fehlgeschlagene Initialisierung**, falsche Geräteselektion oder mismatchende Optionen zwischen Framework und Backend.
- Das Backend selbst arbeitet korrekt, aber das Framework reicht **falsche Parameter, Optionen oder Datentypen** an das Backend weiter.

**Abgrenzung:**

- Liegt das Problem direkt in der User-facing API-Semantik (Kernel-Aufruf, Parameter-Checking, Messlogik), ist es eher **2.4 High-Level-API / Framework-Logik**.
- Wenn Treiber, CUDA-Versionen, Pfade oder System-Umgebung nicht stimmen → eher **2.1 Build/Deploy/Environment**.

**Beispiele (schematisch):**

- Das Framework versucht, ein GPU-Backend zu verwenden, obwohl nur CPU verfügbar ist, und behandelt den Fehler nicht robust.
- Falsche Übersetzung von Framework-Optionen (`shots`, `qubits`, `precision`) in Backend-spezifische Flags, was zu Runtime-Errors führt.

---

### 2.4 High-Level-API - Framework-Logic

**Definition:**  
Diese Kategorie umfasst Bugs in der **User-facing API und Framework-Logik** – also in Kernel-Semantik, Parametervalidierung, Typ-/Shape-Handling, Ergebnisverarbeitung, Transformations- und Messungslogik. Die Ursache liegt typischerweise im **Frontend** (z.B. Python-API, Dekoratoren, High-Level-Konstrukte).

**Typische Indikatoren:**

- Die API erfüllt ihren **eigenen Vertrag** nicht (laut Doku sollte etwas funktionieren, tut es aber nicht).
- Fehler im Umgang mit **Typen, Shapes, Containern oder Standardwerten** von Parametern.
- Falsche oder irreführende High-Level-Ergebnisse (z.B. falsche Messungsindizes, falsche Aggregation von Shots), obwohl das Backend korrekt arbeitet.
- Bugs in Transformations-Pipelines (z.B. QNode-Transforms, Pass-Pipelines), die direkt von Usern verwendet werden.

**Abgrenzung:**

- Wenn das Problem durch **falsche Nutzung** der API entsteht, die API sich aber korrekt gemäß Spezifikation verhält, kann es ein **Usage-/User-Error** sein (falls separat codiert).
- Wenn die API korrekt ist, aber ein bestimmtes Backend intern falsch rechnet → eher **2.2 Backend-Library**.
- Wenn die Ursache in der Umgebung/Installation liegt → **2.1 Build/Deploy/Environment**.

**Beispiele (schematisch):**

- `list[list[int]]` wird laut Doku als Kernel-Argument unterstützt, führt aber zu einem internen Typ-Inferenz-Fehler.
- Eine High-Level-Funktion zur Messungsaggregation gibt ein falsch sortiertes oder falsch indiziertes Ergebnis zurück.

---

### 2.5 Runtime-Framework-Runtime

**Definition:**  
Diese Kategorie deckt Bugs ab, die sich primär in der **Laufzeitphase des Frameworks** zeigen, typischerweise im Bereich **Ressourcenmanagement, Caching, Scheduling und Performance**. Dazu gehören z.B. Memory-Leaks, ineffiziente JIT-Caches, fehlerhaftes Lazy-Evaluation-Verhalten oder starke Performance-Regressionen bei ansonsten korrekten Ergebnissen.

**Typische Indikatoren:**

- Das Programm liefert zwar **korrekte Resultate**, zeigt aber **Memory-Leaks**, ungewöhnlich hohe GPU-/CPU-Auslastung oder inkonsistentes Laufzeitverhalten.
- JIT-/Cache-Mechanismen verhalten sich falsch (z.B. falsches Reuse von kompilierten Kernels, nicht invalidierte Caches).
- Performance-Probleme sind klar auf **Framework-Laufzeitlogik** zurückzuführen, nicht auf generelle Hardware-Limitierungen.

**Abgrenzung:**

- Wenn das Problem primär durch falsche Konfiguration/Installation (z.B. falsche BLAS-/CUDA-Version) entsteht → **2.1 Build/Deploy/Environment**.
- Wenn falsche Resultate (nicht nur Performance/Resource-Verhalten) betroffen sind, kann es **2.2 Backend-Library** oder **2.4 High-Level-API / Framework-Logik** sein – je nach Lokalisierung.

**Beispiele (schematisch):**

- Wiederholte Ausführung desselben Kernels führt zu ständig wachsender GPU-Memory-Nutzung (Leak im Runtime-Layer).
- Ein JIT-Cache speichert zu viele Varianten und wird nie bereinigt → stark wachsende Compile-Time und/oder RAM-Verbrauch.



## 3. Compile-Time-Vermeidbarkeit (CTClass A/B/C)

Zur Einordnung, inwieweit ein Bug prinzipiell durch Compile-Time-Mechanismen
(z.B. Typen, Typstate, statische Analysen) vermeidbar wäre, verwenden wir eine
dreistufige Skala CTClass A/B/C. Diese Einordnung ist eine informierte
Einschätzung, kein Beweis.

### 3.1 CTClass A – direkt compile-time vermeidbar

**Definition:**  
Bugs, die mit hoher Wahrscheinlichkeit durch vergleichsweise „einfache“
Compile-Time-Mechanismen verhindert werden könnten, z.B. durch stärkere Typ-
systeme, präzisere API-Verträge oder grundlegende statische Checks
(Null-/Option-Checks, Dimensions-/Shape-Checks, Pflichtparameter).

**Typische Beispiele:**
- Falsche Typen oder Dimensionen von Parametern, die zu sofortigen
  Fehlermeldungen führen („Grad nur für skalare Outputs“, Shape-Mismatches
  bei Gradients).
- Klare API-Contract-Verletzungen (z.B. „diese Funktion erwartet genau einen
  Erwartungswert, nicht eine Liste“), die sich durch stärkere Typen oder
  Contracts ausdrücken lassen.

**Heuristische Fragen:**
- Könnte ein statischer Typchecker mit ausreichend aussagekräftigen Typen
  diesen Fehler finden?
- Würde ein statischer API-Contract („Function f: Input → Output“) bereits
  verletzte Vorbedingungen anzeigen, bevor der Code läuft?
- Wenn ja, ist A eine plausible Einstufung.

### 3.2 CTClass B – potenziell compile-time vermeidbar (fortgeschrittene Analyse)

**Definition:**  
Bugs, bei denen eine compile-time-basierte Vermeidung grundsätzlich möglich
erscheint, die aber fortgeschrittene Analysen benötigen würden – z.B.
Ressourcen- und Lebensdaueranalyse, komplexe Datenflussanalysen, Inter-
procedural Analysis, Domain-spezifische statische Checks.

**Typische Beispiele:**
- Bestimmte Build-/Install-/Packaging-Probleme, bei denen eine Analyse der
  Dependency-Graphen oder Packaging-Metadaten Inkonsistenzen erkennen könnte.
- Integrationsfehler zwischen Framework und Backend, bei denen bestimmte
  Sequenzen von API-Calls oder Konfigurationen statisch als „inkompatibel“
  erkannt werden könnten.
- Performance-Regressions, die aus klar identifizierbaren strukturellen
  Änderungen resultieren (z.B. ineffiziente Datenstrukturen, offensichtliche
  Komplexitäts-Sprünge).

**Heuristische Fragen:**
- Könnte ein sehr „smarter“ statischer Analyse-/Verification-Tool (mit
  Domänenwissen) diesen Fehler erkennen, ohne das Programm auszuführen?
- Braucht man dafür Wissen über mehrere Module, Datenflüsse oder spezielle
  Invarianten (z.B. Loop-Unrolling-Beschränkungen bei Hardware-Backends)?
- Wenn ja, tendiert die Einstufung eher zu B als zu A.


### 3.2.1 Subtypen innerhalb von CTClass B (B1/B2)

**Motivation (kurz):** CTClass B fasst Fälle zusammen, die prinzipiell vor Ausführung vermeidbar sind,
aber nicht „trivial“ wie A. Zur Präzisierung unterscheiden wir zwei Mechanismen.

**B1 – statisch/metadata-basiert vermeidbar (Compatibility/Constraints)**
Definition: Vermeidbarkeit durch Checks über *statische Artefakte* (Build-/Install-Metadaten, Versions- und Feature-Matrizen,
Architektur/Compute-Capability, deklarierte Limits, Konfigurationsflags).
Typische Mechanismen: Dependency-Resolver-Regeln, Kompatibilitäts-Audits, Build-Time Guards, Capability-Matrix-Checks.

Heuristische Fragen:
- Liegt die nötige Information in Metadaten/Constraints/Support-Matrix vor (Versionen, Arch, Flags, Limits)?
- Könnte ein Preflight/Resolver ohne Ausführung des Workloads „fail-fast“ korrekt entscheiden?

**B2 – vertraglich/guard-basiert vermeidbar (Contracts/Feature-Gating/Typestate-Idee)**
Definition: Vermeidbarkeit durch *API-/Framework-Verträge*, Guards oder Feature-Gates, die unsichere Zustände un-erreichbar machen
(z.B. verbotene Kombinationszustände, result-typed error propagation, safe/unsafe modes).
Typische Mechanismen: Preflight-Validatoren in der API, explizite „unsafe“-Modi, State-Machine/Typestate-Design, Result/Option-Contracts.

Heuristische Fragen:
- Entsteht der Fehler, weil das Framework einen „unsicheren Zustand“ überhaupt zulässt?
- Könnte ein Contract/Guard die fehlerhafte Kombination vor dem Start verhindern oder deterministisch blocken?

**Coding-Regel:** Subtyp nur vergeben, wenn CTClass=B; sonst leer.
Optional: Konfidenz {hoch/mittel/niedrig} bei unsicheren Reports.


### 3.3 CTClass C – nicht sinnvoll compile-time vermeidbar

**Definition:**  
Bugs, die primär von Laufzeitumgebung, Hardware, Treibern, externer
Konfiguration oder hochdynamischen Bedingungen abhängen und für die eine
compile-time-basierte Prävention realistisch nicht machbar ist (oder nur mit
unverhältnismäßigem Aufwand).

**Typische Beispiele:**
- GPU-/Treiber-/CUDA-Versionskonflikte (z.B. Container verlangt CUDA >= X,
  Treiber ist älter; bestimmte GPU-Architektur wird von einer Backend-Library
  nicht unterstützt).
- Numerische Stabilitätsprobleme, die stark von konkreten Hardwareeigenschaften,
  Floating-Point-Implementierungen oder Mixed-Precision-Pfaden abhängen.
- Memory Leaks und Ressourcenprobleme, die aus komplexem Runtime-Verhalten
  (JIT-Caches, Allocator-Strategien, Interaktion mehrerer Libraries) entstehen.

**Heuristische Fragen:**
- Hängt der Bug wesentlich von konkreter Hardware, Treiberversion, Cluster-
  Konfiguration oder Laufzeit-Load ab?
- Wäre selbst ein extrem starkes Typsystem nicht in der Lage, die relevanten
  Umweltparameter zur Compile-Time zu kennen?
- Wenn ja, ist C die naheliegende Einstufung.


## 4. Beispiele

### 4.1 Pilot-Issues (CUDA-Q, Convenience Sample für Phase 1)

Die folgenden Issues aus NVIDIA/cuda-quantum dienen als erste Pilot-Menge für
Exploration und Codebook-Entwurf. Sie sind nicht repräsentativ, sondern nur
Beispiele für verschiedene Kombinationen aus Bug-Typ, Stack-Schicht und
CTClass.

- #3523 – Not able to download latest CUDA Q version with GPU enabled support  
  Link: https://github.com/NVIDIA/cuda-quantum/issues/3523

- #2503 – ImportError: [custatevec] unknown error in check_gpu_compatibility  
  Link: https://github.com/NVIDIA/cuda-quantum/issues/2503

- #1718 – Installer not working as documented with CUDA 12  
  Link: https://github.com/NVIDIA/cuda-quantum/issues/1718

- #3616 – `uv pip install cudaq` fails first time due to dynamic install_requires  
  Link: https://github.com/NVIDIA/cuda-quantum/issues/3616

- #977 – Some Python backend tests fail by reporting `custatevec` errors  
  Link: https://github.com/NVIDIA/cuda-quantum/issues/977

- #2564 – `cudaq.set_target("nvidia")` silently falls back to qpp if custatevec not built  
  Link: https://github.com/NVIDIA/cuda-quantum/issues/2564

- #920 – MPI support not enabled in Python wheels, `cudaq.mpi` APIs act as stubs  
  Link: https://github.com/NVIDIA/cuda-quantum/issues/920

- #2357 – `cudaq.kernels.uccsd` fails on hardware backends (MLIR unroll error)  
  Link: https://github.com/NVIDIA/cuda-quantum/issues/2357

- #1681 – cuStateVec initialization error on Grace Hopper (ARM64)  
  Link: https://github.com/NVIDIA/cuda-quantum/issues/1681



### 4.2 Ausgearbeitetes Beispiel: Issue #3523

**Issue:** #3523 – Not able to download latest CUDA Q version with GPU enabled support  
**Link:** https://github.com/NVIDIA/cuda-quantum/issues/3523

**Kurzbeschreibung:**  
User versucht, das CUDA-Q Docker-Image mit GPU-Unterstützung zu starten. Der
Container bricht ab mit der Fehlermeldung, dass die Bedingung
`cuda>=12.6` nicht erfüllt ist (installierter Treiber ist älter). Der Fehler
tritt auf, bevor irgendein Quantum-Kernel ausgeführt wird.

**Bug-Typ (Codebook-Kategorie):**  
- Config-/Environment-Bug (Typ 1.1)  
  → Hauptursache ist eine nicht passende CUDA-/Treiber-Version in der Umgebung.

**Stack-Schicht:**  
- Build/Deploy/Environment (Schicht 2.1)  
  → Problem liegt beim Start des Containers bzw. beim Abgleich von Treiber- und
  Container-Anforderungen, nicht in der eigentlichen Programmlogik.

**CTClass (erste Einordnung):**  
- CTClass C – nicht sinnvoll compile-time vermeidbar  
  → Die Inkompatibilität ergibt sich aus der Kombination aus installiertem
  NVIDIA-Treiber auf dem Host und den Anforderungen des Container-Images.
  Diese Information ist erst zur Laufzeit/Deployment-Zeit sichtbar; ein
  typischer Compiler-Typcheck der Anwendung würde das nicht abfangen.

**Notizen:**  
- Gutes Prototyp-Beispiel für RQ4 (Config-/Environment-Bug im GPU-Stack).
- Kann später als Referenzbeispiel in Paper/Artefakt dienen, um
  Config/Env-Kategorie zu illustrieren.


### 4.3 Ausgearbeitetes Beispiel: Issue #2503

**Issue:** #2503 – unknown error when importing cudaq from python  
**Link:** https://github.com/NVIDIA/cuda-quantum/issues/2503

**Kurzbeschreibung:**  
Ein minimaler Python-Test (`import cudaq`) schlägt sofort fehl. Die
Fehlermeldung lautet:

`ImportError: [custatevec] %unknown error in check_gpu_compatibility`

Der Fehler entsteht beim Laden der MLIR-/custatevec-Komponenten und deutet
darauf hin, dass der interne GPU-Kompatibilitätscheck von cuStateVec scheitert
(z.B. abhängig von Treiber, Compute Capability der GPU, etc.).

**Bug-Typ (Codebook-Kategorie, vorläufig):**  
- Config-/Environment-Bug (Typ 1.1), Schwerpunkt GPU-Kompatibilität  
  → Das Problem hängt stark von der konkreten GPU-/Treiber-/Runtime-Kombination
  ab und äußert sich als Import-Fehler ohne Änderung am Nutzer-Code.

**Stack-Schicht (vorläufig):**  
- Backend-Library (geplante Schicht 2.x)  
  → Der Fehler entsteht in der Backend-Library (custatevec / cuStateVec), die
  beim Import ihre GPU-Kompatibilität prüft, bevor ein eigentlicher
  Quantum-Workflow startet.

**CTClass (erste Einordnung):**  
- CTClass C – nicht sinnvoll compile-time vermeidbar  
  → Ob eine bestimmte GPU/Treiber-Kombination von custatevec unterstützt wird,
  hängt von Hardware- und Laufzeitumgebung ab. Diese Informationen liegen
  typischerweise nicht im Zuständigkeitsbereich eines Compile-Time-Typ- oder
  Datenflusschecks der Anwendungslogik.

**Notizen:**  
- Eignet sich als Beispiel für GPU-/Hardware-gebundene Bugs in Backend-
  Libraries.
- Gute Ergänzung zu #3523: Beide sind Environment-/Kompatibilitätsprobleme,
  aber #3523 im Container/Deploy-Kontext, #2503 beim Backend-Init.


### 4.4 Ausgearbeitetes Beispiel: Issue #977

**Issue:** #977 – Some Python backend tests fail by reporting `custatevec` errors when running on a machine with GPUs  
**Link:** https://github.com/NVIDIA/cuda-quantum/issues/977

**Kurzbeschreibung:**  
Mehrere Python-Backend-Tests (`python/tests/backends/*.py`) schlagen fehl, wenn
sie auf einer Maschine mit GPU ausgeführt werden. Die Fehlermeldung lautet u.a.:

`RuntimeError: [custatevec] %initialization error in addQubitsToState`

Setzt man jedoch die Umgebungsvariable `CUDAQ_DEFAULT_SIMULATOR=qpp-cpu`, laufen
die Tests durch. Das Problem tritt also in der Kombination aus Python-Backend,
Backend-Selection und custatevec-Initialisierung auf.

**Bug-Typ (Codebook-Kategorie, vorläufig):**  
- Backend-/Framework-Integrations-Bug  
  → Das Problem entsteht im Zusammenspiel zwischen CUDA-Qs Python-Backends,
  der Auswahl des Default-Simulators und der Initialisierung von custatevec.

**Stack-Schicht (vorläufig):**  
- Framework-Integration  
  → Es geht nicht „nur“ um die reine Backend-Library oder die Systemumgebung,
  sondern darum, wie CUDA-Q die verschiedenen Backend-Implementierungen
  (GPU vs. qpp-cpu) auswählt und anspricht.

**CTClass (erste Einordnung):**  
- CTClass B (A/B-Grenzfall)  
  → Teile des Problems könnten durch stärkere Verträge/Typen zwischen
  Backend-Interface und Implementation sowie klarere Checks bei der
  Backend-Selection besser abgefangen werden (z.B. Validierung der
  Initialisierungsbedingungen). Vollständig statisch überprüfbar ist die
  korrekte GPU-Initialisierung aber vermutlich nicht.

**Notizen:**  
- Gutes B

### 4.5 Ausgearbeitetes Beispiel: PennyLane #4462

**Issue:** PennyLane #4462 – Differentiation of broadcasted QNode via gradient transforms  
**Link:** https://github.com/PennyLaneAI/pennylane/issues/4462

**Kurzbeschreibung:**  
Ein QNode wird mit einem gebatchten/broadcasted Parametervektor aufgerufen
(z.B. zwei Parameterwerte auf einmal). Die Berechnung des Gradienten mit
Gradient-Transforms (z.B. `qml.jacobian` / parameter-shift) führt zu einem
Shape-Mismatch: Die Gradient-Transformation liefert eine Ausgabe der Form
`(2,)`, während die nachgelagerte JVP-/Jacobian-Logik eine Form `(2, 2)`
erwartet. Dadurch entsteht ein Fehler beim Versuch, die Jacobian weiterzu-
verarbeiten.

**Bug-Typ (Codebook-Kategorie, vorläufig):**  
- API-/Usage-/Logic-Bug (High-Level)  
  → Es geht um die Definition und Umsetzung der Semantik eines broadcasted
  QNode und die Frage, welche Form die zugehörige Jacobian haben soll. Der
  Fehler entsteht auf der Ebene der API- und Transformationslogik, nicht
  durch die Umgebung oder Installation.

**Stack-Schicht (vorläufig):**  
- High-Level-API / Framework-Logik  
  → Der Bug liegt in der Interaktion zwischen QNode-API, Gradient-Transforms
  und interner JVP-/Jacobian-Implementierung in PennyLane.

**CTClass (erste Einordnung):**  
- CTClass A/B (Grenzfall)  
  → Ein Teil des Problems könnte durch stärkere Shape-/Typprüfungen an der
  Schnittstelle (z.B. klare Verträge über Input-/Output-Shape für broadcasted
  QNodes) frühzeitig abgefangen werden (A-Tendenz). Gleichzeitig hängt die
  konkrete Ausprägung des Fehlers von der Kombination aus Interface,
  Transform und verwendeter Backend-Logik ab, was in Richtung B (erweiterte
  statische Analyse) weist.

**Notizen:**  
- Gutes Beispiel für einen Bug, der nicht durch CUDA-/Treiber-Config oder
  Installation erklärt wird, sondern durch eine nicht sauber spezifizierte
  API-Semantik (broadcast + Gradient).
- Kann als Referenzfall dienen, wenn im Codebook die Kategorie
  „API-/Usage-/Logic-Bug (High-Level)“ erläutert und von reinen
  Config-/Environment-Bugs abgegrenzt wird.


### 4.6 Ausgearbeitetes Beispiel: CUDA-Q #1909

**Issue:** #1909 – cudaq.observe causes a memory leak  
**Link:** https://github.com/NVIDIA/cuda-quantum/issues/1909

**Kurzbeschreibung:**  
Ein einfacher VQE-artiger Loop ruft wiederholt `cudaq.observe` auf. Dabei wird
die Speichernutzung schrittweise immer höher (z.B. ca. 1.2 GB nach 100.000
Iterationen), ohne dass der Speicher nach den Aufrufen wieder freigegeben
wird. Der Nutzer misst den RSS-Speicherverbrauch des Prozesses und beobachtet
einen kontinuierlichen Anstieg über viele Iterationen.

**Bug-Typ (Codebook-Kategorie, vorläufig):**  
- Performance-/Numerik-Bug  
  → Das Problem manifestiert sich als Memory Leak / Ressourcenproblem bei
  länger laufenden Optimierungsschleifen und betrifft die Laufzeitperformance
  und Stabilität, nicht die korrekte Installation oder API-Semantik.

**Stack-Schicht (vorläufig):**  
- Runtime-/Framework-Laufzeit (zwischen Kernel-Execution und Host-Code)  
  → Der Fehler liegt in der Art, wie die JIT-/Runtime-Komponenten von CUDA-Q
  Speicher für beobachtete Kernele allokieren und verwalten, nicht in der
  User-Logik oder Umgebungskonfiguration.

**CTClass (erste Einordnung):**  
- CTClass C – nicht sinnvoll compile-time vermeidbar  
  → Ob Speicher tatsächlich freigegeben wird, hängt hier von der konkreten
  Implementierung des Runtimesystems, JIT-Caches und Garbage Collection ab.
  Ein statischer Typ- oder Shape-Check der Kernel-Signaturen würde dieses
  Problem nicht verhindern; es ist primär eine Laufzeit-/Implementierungsfrage.

**Notizen:**  
- Gutes Beispiel für Performance-/Ressourcen-Bugs in langen Optimierungs- oder
  Trainingsloops (z.B. VQE).
- Kann später genutzt werden, um zu diskutieren, dass nicht alle relevanten
  Bugs in GPU-Stacks sinnvoll durch Compile-Time-Safety adressierbar sind.

### 4.7 Ausgearbeitetes Beispiel: Build-/Install-Bug (cudaq mit uv)

**Issue:** uv #12759 – `uv pip install cudaq` fails the first time (missing dependencies)  
**Link:** https://github.com/astral-sh/uv/issues/12759

**Kurzbeschreibung:**  
In einem frischen virtuellen Environment führt der Befehl

`uv pip install cudaq`

beim ersten Aufruf nur zur Installation von `cudaq==0.10.0`, ohne die
eigentlichen GPU- und cuQuantum-Abhängigkeiten. Erst ein zweiter Aufruf von
`uv pip install cudaq` installiert die vollständige Menge an Dependencies
(cuQuantum, custatevec, cutensornet, CUDA-Runtime-Pakete, etc.). Das Problem
tritt in Kombination von `uv` und dem aktuellen Packaging von `cudaq` auf.

**Bug-Typ (Codebook-Kategorie, vorläufig):**  
- Build-/Install-/Packaging-Bug  
  → Die Ursache liegt in der Art, wie `cudaq` als sdist mit einem dynamischen
  `setup.py` ausgeliefert wird, das `install_requires` zur Laufzeit ermittelt.
  Dieses Verhalten interagiert schlecht mit dem Resolver/Build-Prozess von `uv`.

**Stack-Schicht (vorläufig):**  
- Build/Deploy/Environment  
  → Der Fehler tritt während der Installation auf, bevor überhaupt ein Quantum-
  Programm ausgeführt oder ein Backend initialisiert wird. Es geht um Metapackage-
  Definition und Dependency-Management.

**CTClass (erste Einordnung):**  
- CTClass B  
  → In der Theorie könnte ein strengeres Packaging-Modell (z.B. statische
  `pyproject.toml` mit vollständigen Dependencies, Verzicht auf dynamisches
  `install_requires`) den Fehler verhindern. Dafür wären aber Analyse/Checks
  des Build- und Packaging-Prozesses nötig, nicht nur einfache Typprüfungen
  im User-Code (daher eher B als A).

**Notizen:**  
- Gutes Beispiel für Bugs, die aus der Interaktion mehrerer Werkzeuge entstehen
  (hier: `cudaq`-Metapackage + `uv`-Resolver), ohne dass die Nutzer-Logik oder
  die Hardware-Konfiguration falsch wäre.
- Eignet sich gut, um die Kategorie „Build-/Install-/Packaging-Bug“ von reinen
  Config-/Environment-Problemen (z.B. falsche CUDA-Treiber-Version) abzugrenzen.


## 5. Coding-Regeln (Erweiterung)

1) CTClass (A/B/C) vergeben.
2) Falls CTClass = B: CTSubType vergeben:
   - B1, wenn Vermeidbarkeit über Metadaten/Constraints/Support-Matrix plausibel ist.
   - B2, wenn Vermeidbarkeit über Contracts/Guards/Feature-Gating plausibel ist.
3) Falls unklar: CTClass bleibt wie entschieden, CTSubType optional mit niedriger Konfidenz markieren.

## 6. Meta-Informationen

<!-- Version des Codebooks, Datum, Notizen zu Anpassungen -->
