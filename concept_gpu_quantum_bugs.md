# Empirical Study: Bugs in GPU-Accelerated Quantum Stacks

## 1. Research Questions

RQ1: Welche Arten von Bugs treten in GPU-beschleunigten Quantum-Stacks 
(z.B. cuQuantum, CUDA-Q, PennyLane Lightning GPU) auf?

Motivation: Wir wollen ein klares Bug-Profil für GPU-basierte Quantum-Stacks
erstellen und später mit existierenden Studien zu Qiskit, Cirq & Co. vergleichen.
So sehen wir, ob GPU-Stacks andere oder ähnliche Bugmuster haben.


RQ2: In welchen Schichten des Stacks (Backend-Library, Framework-Integration, 
High-Level-API, Build/Deploy/Environment) treten diese Bugs auf?

Motivation: Die verschiedenen Schichten des Stacks (Low-Level-Library,
Framework-Integration, High-Level-API, Build/Deploy/Environment) haben sehr
unterschiedliche Verantwortlichkeiten. Wir wollen verstehen, wo sich Probleme
konzentrieren, um gezielt Verbesserungen und Tools ansetzen zu können.


RQ3: Welcher Anteil dieser Bugs ist prinzipiell zur Compile-Time vermeidbar 
(z.B. durch stärkere Typen, Typstate oder statische Analysen)?

Motivation: Diese Frage verbindet die empirische Analyse direkt mit
Compile-Time-Safety (z.B. Typen, Typstate, statische Analysen). Wir wollen
abschätzen, welches Potenzial es überhaupt gibt, Bugs schon vor der Ausführung
abzufangen.
Zusätzlich werden wir alle Bugs in drei CTClass-Kategorien einteilen:
A (direkt compile-time vermeidbar), B (nur mit fortgeschrittener statischer
Analyse potenziell vermeidbar) und C (nicht compile-time vermeidbar).


RQ4: Welcher Anteil der Bugs in GPU-beschleunigten Quantum-Stacks ist 
Configuration-/Environment-bedingt im Vergleich zu Logik-/Programmanomaly-Bugs, 
wie sie in bestehenden Studien zu Quantum-Frameworks dominieren?

Motivation: Bisherige Studien zu Quantum-Frameworks fokussieren stark auf
Logik- und Algorithmus-Bugs. GPU-beschleunigte Stacks sind jedoch stark von
Konfiguration, Treibern und Umgebung abhängig. Wir wollen quantifizieren, wie
groß der Anteil von Config-/Environment-Bugs im Vergleich zu „klassischen“
Programmfehlern ist.
Außerdem vergleichen wir den Anteil von Config-/Environment-Bugs explizit mit
Ergebnissen aus existierenden Studien zu High-Level-Frameworks (z.B. Qiskit,
Cirq), um zu prüfen, ob GPU-Stacks hier deutlich anfälliger sind.


## 2. Systems / Projects

Wir betrachten in dieser Studie drei zentrale Systeme aus dem Bereich
GPU-beschleunigter Quantum-Stacks:

### System 1 – cuQuantum / cuStateVec (NVIDIA)

cuQuantum (insbesondere cuStateVec und cuTensorNet) ist eine Low-Level-GPU-
Bibliothek für das Simulieren von Quantenzuständen und -schaltungen. Sie
stellt vorrangig C- und Python-APIs bereit, die in verschiedene Frameworks
integriert werden können.

Für unsere Studie ist cuQuantum relevant als Beispiel für eine
Backend-Library, in der Bugs typischerweise GPU-nahe Funktionalität betreffen,
z.B. Speicherverwaltung, CUDA-Kernel-Aufrufe, Performance- und
Numerikprobleme oder spezielle Hardware-Konfigurationen.

### System 2 – CUDA-Q (cuda-quantum)

CUDA-Q (ehemals cuda-quantum) ist ein Framework für Quantum Programming mit
C++- und Python-Frontends und mehreren Backends (u.a. CPU-Simulatoren und
GPU-basierte Backends wie cuStateVec). Es verbindet High-Level-Programmierung
mit der Ausführung auf unterschiedlichen Targets.

Für unsere Studie ist CUDA-Q ein Beispiel für ein Framework auf der
Framework-Integrationsschicht. Relevante Bugs betreffen hier u.a. die
Anbindung an Backends, API-Contracts, Typen und Parameter, Build- und
Compile-Probleme sowie das Zusammenspiel von Host-Code und Quantum-Kernels.

### System 3 – PennyLane Lightning GPU

Lightning GPU ist ein PennyLane-Backend, das GPU-beschleunigte Simulation über
cuQuantum/custatevec ermöglicht. Es wird typischerweise über PennyLane als
„Device“ angesprochen und in Python-Workflows integriert.

Für unsere Studie repräsentiert Lightning GPU die Kombination aus
Framework-Integration und High-Level-API, bei der Bugs häufig mit
Device-Konfiguration, Backend-Auswahl, Bibliotheksversionen, Gradienten-
Berechnung oder der Einbettung in größere Machine-Learning-Workflows
zusammenhängen.


## 3. Timeframe & Sample Size

In dieser Studie betrachten wir Bugs aus einem klar begrenzten Zeitraum und
verwenden eine feste Stichprobengröße, um die Analyse überschaubar und
replizierbar zu halten.

### Timeframe

Geplanter Betrachtungszeitraum:

- Bugs, die im Zeitraum **01.01.2023 – 19.11.2025** erstellt wurden.
- Fokus auf moderne Versionen von cuQuantum, CUDA-Q und Lightning GPU, in
  denen GPU-Unterstützung bereits etabliert ist.
- Der genaue Stichtag (Datum des Datenpulls) wird im Methodik-Teil dokumentiert,
  falls er leicht vom hier genannten Zeitraum abweicht.

### Sample Size

Ziel ist eine Stichprobe von insgesamt ca. **100–120 Bugs**, die als
„GPU-relevant“ eingestuft werden (siehe Definitions-Abschnitt).

Grobe Zielverteilung über die drei Systeme:

- ca. 35–40 % Bugs aus cuQuantum / cuStateVec,
- ca. 35–40 % Bugs aus CUDA-Q,
- ca. 20–30 % Bugs aus PennyLane Lightning GPU.

Diese Verteilung kann bei der tatsächlichen Datensammlung leicht angepasst
werden (z.B. wenn einzelne Repositories deutlich weniger passende Bugs im
Zeitraum enthalten), die **Gesamtgröße** der Stichprobe (≈ 100–120 Bugs)
soll jedoch beibehalten werden.

Die Stichprobe wird später mittels eines klar definierten Sampling-Protokolls
(z.B. stratifiziert nach Projekt und Zeitraum, mit dokumentiertem Zufallsseed)
gezogen und anschließend „eingefroren“, bevor das systematische Coding beginnt.


## 4. Out-of-Scope

In dieser Studie betrachten wir bewusst nur einen Ausschnitt des gesamten
Ökosystems. Folgende Aspekte sind ausdrücklich **nicht** Teil des Scopes:

1. Klassische CPU-only-Simulatoren
   - Bugs, die ausschließlich reine CPU-Simulatoren oder Backends ohne
     GPU-Bezug betreffen, werden nicht berücksichtigt.
   - Beispiel: Bugs in rein CPU-basierten PennyLane- oder Qiskit-Backends
     ohne Verwendung von cuQuantum oder vergleichbaren GPU-Libraries.

2. Reine Feature Requests und Design-Diskussionen
   - Issues, in denen keine Fehlfunktion, sondern nur neue Features, API-
     Erweiterungen oder allgemeine Designvorschläge diskutiert werden,
     zählen nicht als Bugs im Sinne dieser Studie.

3. Dokumentations- und Schreibfehler
   - Issues, die ausschließlich Dokumentationsfehler, Typos oder fehlende
     Beispiele in der Doku betreffen, werden ausgeschlossen, sofern keine
     tatsächliche Laufzeit-Fehlfunktion beschrieben wird.

4. Hardware-/Treiberprobleme ohne klaren Softwarebezug
   - Fälle, in denen Probleme ausschließlich auf spezifische Hardwaredefekte
     oder externe Treiber-/Systemkonfigurationen zurückgeführt werden und
     kein sinnvoller Bezug zu den untersuchten Libraries/Frameworks
     hergestellt werden kann, werden nicht in die Stichprobe aufgenommen.

5. Duplicate-Issues ohne eigenen inhaltlichen Mehrwert
   - Reine Duplikate anderer Issues, die keine zusätzlichen technischen
     Details enthalten, werden verworfen. Stattdessen wird das jeweils
     informativere Original-Issue betrachtet.


## 5. Definitions

In diesem Abschnitt definieren wir zentrale Begriffe, die für die Auswahl und
spätere Klassifikation der Bugs wichtig sind.

### Definition: Bug

Für diese Studie verstehen wir unter einem „Bug“ ein Issue oder einen Report,
in dem mindestens einer der folgenden Punkte erfüllt ist:

- Es wird ein falsches Verhalten, ein Crash oder eine Fehlermeldung im
  Zusammenhang mit einem der betrachteten Systeme beschrieben, oder
- es wird ein konkreter Fix, Workaround oder Patch diskutiert, der eine
  Fehlfunktion adressiert.

Reine Verbesserungsvorschläge, Designideen oder Dokumentationswünsche zählen
nicht als Bug (siehe Out-of-Scope).

### Definition: GPU-relevanter Bug

Ein Bug wird als „GPU-relevant“ eingestuft, wenn mindestens eine der folgenden
Bedingungen erfüllt ist:

- Das Issue erwähnt explizit GPU-/CUDA-Begriffe (z.B. „GPU“, „CUDA“, „device“,
  „kernel“, „stream“, „GPU backend“), oder
- das Problem tritt nur bei Verwendung eines GPU-Backends oder eines
  GPU-spezifischen Devices auf, oder
- der Bug ist klar an die Konfiguration oder Verfügbarkeit von GPU-Ressourcen
  (z.B. CUDA-Version, Treiber, GPU-Speicher) gekoppelt.

### Definition: Compile-Time-vermeidbarer Bug (CTClass A/B/C – Arbeitsversion)

Wir verwenden eine grobe Dreiteilung, um das Potenzial für Compile-Time-
Vermeidbarkeit zu klassifizieren:

- **CTClass A – direkt compile-time vermeidbar**  
  Bugs, die durch stärkere Typen, Typstate oder einfache statische Checks
  mit hoher Wahrscheinlichkeit verhindert we


## 6. Planned Workflow (High-Level)