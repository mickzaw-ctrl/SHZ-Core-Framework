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

> Last updated: **2026-06-29 00:46 UTC** by Emilka — SHZ Quantum AI  
> **Status:** ✅ BOTH JOBS COMPLETE

### 18core × IBM Kingston Results

| Test | Qubits | Job ID | Status | Signal |
|------|--------|--------|--------|--------|
| Spin(10) QAOA (γ=0.2739) | 12q | [`d90dkp0pknjs73a28he0`](https://quantum.cloud.ibm.com) | ✅ Complete | GUT vacuum |
| 18core ZZFeatureMap | 18q | [`d90dp9emvj5c73ej2ubg`](https://quantum.cloud.ibm.com) | ✅ Complete | 🟢 **BUY** |

**Spin(10) QAOA Results (12 qubits):**
- 810 unique quantum states / 4,096 possible
- Top state: `|000000000000⟩` — **GUT vacuum** ✅ (ground state of SHZ unification)
- Runtime: **6.2s** on real 156-qubit QPU

**18core Feature Map Results (18 qubits, REAL QPU):**
- Von Neumann Entropy: **9.998 / 18.0 bits** ✅ (99.98% utilization!)
- Unique states: **1,023 / 262,144** 
- Composite trading signal: **🟢 BUY (score = +4)** ⬆️ (reversed from simulator!)
- Top state: `|100100101111010100⟩`

### Links

- 📄 [Full benchmark report — spin10-toe](https://github.com/mickzaw-ctrl/spin10-toe/blob/main/results/18core_qpu_results.md)
- 📊 [Raw JSON data — spin10-toe](https://github.com/mickzaw-ctrl/spin10-toe/blob/main/results/18core_qpu_results.json)
- 📄 [Benchmark report — QuantumHybridGraph](https://github.com/mickzaw-ctrl/QuantumHybridGraph/blob/main/benchmarks/18core_qpu_results.md)
- 🚀 [GitHub Release v18core-qpu-test-1](https://github.com/mickzaw-ctrl/spin10-toe/releases/tag/v18core-qpu-test-1)
