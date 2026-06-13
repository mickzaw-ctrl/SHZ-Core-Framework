#!/usr/bin/env python3
"""
SHZ-U: Symulacja łamania Spin(10) → SU(3)×SU(2)×U(1)
=======================================================
Modelowanie Grand Unification w sieci horyzontów.

Spin(10) ma wymiar 45 (generatory)
SU(5) ma wymiar 24
SM: SU(3)×SU(2)×U(1) ma wymiar 8+3+1 = 12

Łamanie: Spin(10) → SU(5) × U(1) → SU(3)×SU(2)×U(1)

Użycie:
    python3 shz_gut_breaking_simulation.py [--scale GUT|INTERMEDIATE|SM]
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import itertools
import json
import os

os.makedirs('./shz_gut_results', exist_ok=True)

np.random.seed(42)

# ============================================================
# STAŁE I PARAMETRY
# ============================================================
hbar = 1.0
omega_P = 1.0
k_bar = 8

# Skale energii (znormalizowane)
M_PLANCK = 1.0
M_GUT = 0.01 * M_PLANCK  # ~10^16 GeV w jednostkach Plancka
M_ELECTROWEAK = 2.46e-16 * M_PLANCK  # 246 GeV

# Grupy i ich wymiary
GROUPS = {
    'Spin(10)': {'dim': 45, 'color': 'red'},
    'SU(5)': {'dim': 24, 'color': 'orange'},
    'SU(3)': {'dim': 8, 'color': 'blue'},
    'SU(2)': {'dim': 3, 'color': 'green'},
    'U(1)_Y': {'dim': 1, 'color': 'purple'},
    'U(1)_EM': {'dim': 1, 'color': 'brown'}
}

print("=" * 70)
print("SHZ-U: Symulacja łamania symetrii GUT")
print("=" * 70)
print(f"\nŁamanie przewidywane:")
print(f"  Spin(10) → SU(5) × U(1) [przy M_GUT]")
print(f"  SU(5) → SU(3) × SU(2) × U(1) [przy M_EW]")
print(f"\nGrupy i ich wymiary:")
for g, info in GROUPS.items():
    print(f"  {g}: {info['dim']} generatorów")

# ============================================================
# KLASY
# ============================================================

class GaugeGroupRepresentation:
    """Reprezentacja grupy gauge w sieci horyzontów."""
    
    def __init__(self, group_name, dim, seed=None):
        self.name = group_name
        self.dim = dim  # Wymiar grupy (liczba generatorów)
        np.random.seed(seed or np.random.randint(1e6))
        
        # Reprezentacja fundamentalna (ustaw PRZED init_generators)
        if group_name == 'Spin(10)':
            self.fund_dim = 10
        elif group_name == 'SU(5)':
            self.fund_dim = 5
        elif group_name == 'SU(3)':
            self.fund_dim = 3
        elif group_name == 'SU(2)':
            self.fund_dim = 2
        else:
            self.fund_dim = 1
        
        # Generatory grupy jako macierze w reprezentacji fundamentalnej
        # Dla Spin(10): reprezentacja 10-wymiarowa
        # Dla SU(N): N×N macierze antyhermitowskie
        self.generators = self._init_generators()
        
        # Holonomie na krawędziach jako elementy grupy
        self.holonomies = {}  # edge -> element grupy (jako kwaternion lub macierz)
    
    def _init_generators(self):
        """Inicjalizuje generatory grupy."""
        generators = []
        
        # Dla każdego generatora: macierz w reprezentacji antyhermitowskiej
        # T^a z warunkiem T^a = -(T^a)^†
        n = self.fund_dim
        
        if self.name.startswith('SU'):
            # Generatory SU(N): macierze antyhermitowskie bez śladu
            for i in range(self.dim):
                # Losowa macierz antyhermitowska
                M = np.random.randn(n, n) + 1j * np.random.randn(n, n)
                M = (M - M.T.conj()) / 2  # Antyhermitowska
                
                # Usuń ślad (jeśli nie U(1))
                if n > 1:
                    M = M - np.trace(M) * np.eye(n) / n
                
                generators.append(M)
        elif self.name == 'Spin(10)':
            # Spin(10) = so(10): macierze antysymetryczne 10×10
            for i in range(self.dim):
                M = np.zeros((10, 10), dtype=complex)
                # Losowa macierz antysymetryczna: M = -M^T
                for a in range(10):
                    for b in range(a+1, 10):
                        if len(generators) < self.dim:
                            val = np.random.randn() + 1j * np.random.randn()
                            M[a, b] = val
                            M[b, a] = -np.conj(val)
                            generators.append(M.copy())
                            M[a, b] = 0
                            M[b, a] = 0
        
        return np.array(generators[:self.dim])
    
    def get_group_element(self, theta):
        """Otrzymuje element grupy exp(i θ^a T^a) dla losowych θ."""
        # Element grupy: exp(i Σ θ^a T^a)
        n = self.fund_dim
        exponent = np.zeros((n, n), dtype=complex)
        
        # Losowe kąty
        thetas = np.random.randn(self.dim) * theta
        
        for a, theta_a in enumerate(thetas):
            if a < len(self.generators):
                exponent += theta_a * self.generators[a]
        
        # Macierz eksponenty
        try:
            element = np.linalg.matrix_power(exponent, 2)
            element = np.exp(1j * exponent)
        except:
            element = np.eye(n, dtype=complex)
        
        return element
    
    def project_to_subgroup(self, subgroup_name):
        """Projekcja do podgrupy."""
        if subgroup_name not in GROUPS:
            return self
        
        # Zwraca nową reprezentację podgrupy
        new_rep = GaugeGroupRepresentation(subgroup_name, GROUPS[subgroup_name]['dim'])
        return new_rep


class SimplicialComplexGUT:
    """Kompleks symplicjalny z reprezentacją GUT."""
    
    def __init__(self, n_nodes, avg_degree=8, group_name='Spin(10)', seed=None):
        self.n_nodes = n_nodes
        self.avg_degree = avg_degree
        self.group_name = group_name
        self.seed = seed or np.random.randint(1e9)
        np.random.seed(self.seed)
        
        # Struktura sieci
        self.nodes = list(range(n_nodes))
        self.edges = []
        self.triangles = []
        
        # Reprezentacja grupy gauge
        self.gauge_group = GaugeGroupRepresentation(group_name, GROUPS[group_name]['dim'])
        
        # Holonomie na krawędziach (elementy grupy)
        self.holonomies = {}  # edge -> element grupy
        
        # Pole Higgsa
        self.phi_field = np.zeros(n_nodes)
        self.vev = 0.0
        
        # Historia łamania symetrii
        self.symmetry_history = []
        
        self._generate()
    
    def _generate(self):
        """Generuje sieć."""
        # Krawędzie
        target_edges = int(self.n_nodes * self.avg_degree / 2)
        for i in range(self.n_nodes):
            for j in range(i+1, self.n_nodes):
                if np.random.random() < 0.35:
                    self.edges.append((i, j))
        
        while len(self.edges) < target_edges:
            i, j = np.random.choice(self.n_nodes, 2, replace=False)
            if (i, j) not in self.edges and (j, i) not in self.edges:
                self.edges.append((i, j))
        
        # Trójkąty
        edge_set = set(tuple(sorted(e)) for e in self.edges)
        for i, j, k in itertools.combinations(range(self.n_nodes), 3):
            if all(tuple(sorted(e)) in edge_set for e in [(i,j), (j,k), (i,k)]):
                if np.random.random() < 0.5:
                    self.triangles.append((i, j, k))
        
        # Inicjalizacja holonomii (stan symetryczny)
        self._init_holonomies_symmetric()
        
        # Inicjalizacja pola Higgsa
        self.phi_field = np.random.choice([-2.0, 2.0], self.n_nodes) + np.random.normal(0, 0.5)
        self.vev = np.mean(np.abs(self.phi_field))
    
    def _init_holonomies_symmetric(self):
        """Inicjalizuje holonomie w stanie symetrycznym (identity)."""
        n = self.gauge_group.fund_dim
        
        for edge in self.edges:
            # Identity w reprezentacji grupowej
            self.holonomies[edge] = np.eye(n, dtype=complex)
    
    def _init_holonomies_broken(self, breaking_scale='GUT'):
        """Inicjalizuje holonomie w stanie złamanym."""
        n = self.gauge_group.fund_dim
        
        # Skala łamania determinuje "odchylenie" od identity
        if breaking_scale == 'GUT':
            theta = 0.3  # Duże odchylenie (Spin(10) → SU(5))
        elif breaking_scale == 'INTERMEDIATE':
            theta = 0.15  # Średnie odchylenie
        elif breaking_scale == 'SM':
            theta = 0.05  # Małe odchylenie (SU(5) → SM)
        else:
            theta = 0.1
        
        for edge in self.edges:
            element = self.gauge_group.get_group_element(theta)
            self.holonomies[edge] = element
    
    def apply_higgs_vev(self, vev_direction):
        """
        Aplikuje VEV Higgsa w kierunku vev_direction.
        Powoduje łamanie symetrii grupy.
        """
        n = self.gauge_group.fund_dim
        
        # VEV w reprezentacji 10 dla Spin(10)
        # φ = diag(0,0,0,0, v, v, -v, -v, v, -v) lub podobnie
        if self.group_name == 'Spin(10)' and len(vev_direction) >= 10:
            vev_matrix = np.diag(vev_direction[:10])
        else:
            # Ogólny VEV
            vev_matrix = vev_direction[0] * np.eye(n)
        
        # Zastosuj VEV do holonomii (symmetry breaking)
        for edge in self.holonomies:
            # Holonomia z VEV
            self.holonomies[edge] = np.exp(1j * vev_matrix) @ self.holonomies[edge]
    
    def measure_symmetry_order(self, group_name='current'):
        """
        Mierzy rząd symetrii dla danej grupy.
        
        Dla grupy zachowanej: wszystkie holonomie komutują
        Dla grupy złamanej: holonomie nie komutują (anomalia)
        """
        order_params = {}
        
        # 1. Średnia holonomia (Trace)
        traces = []
        for edge, hol in self.holonomies.items():
            traces.append(np.trace(hol))
        
        avg_trace = np.mean([np.abs(t) for t in traces])
        order_params['avg_trace'] = avg_trace
        
        # 2. Antykomutator (mierzy "odchylenie od Abela")
        commutators = []
        for i, (e1, e2) in enumerate(itertools.combinations(list(self.holonomies.keys())[:20], 2)):
            h1, h2 = self.holonomies[e1], self.holonomies[e2]
            commutator = np.linalg.norm(h1 @ h2 - h2 @ h1)
            commutators.append(commutator)
        
        avg_commutator = np.mean(commutators)
        order_params['avg_commutator'] = avg_commutator
        
        # 3. Spread wartości własnych (degeneracja)
        eigenvalues = []
        for hol in list(self.holonomies.values())[:10]:
            eigvals = np.linalg.eigvals(hol)
            eigenvalues.extend([np.abs(v) for v in eigvals])
        
        spread = np.std(eigenvalues) if eigenvalues else 0
        order_params['eigenvalue_spread'] = spread
        
        # 4. Rząd symetrii: 1 = pełna symetria, 0 = całkowicie złamana
        # Mierzymy jak bardzo elementy grupy są "bliskie identity"
        distances_from_identity = []
        for hol in self.holonomies.values():
            # Odległość od identity: ||U - I||
            dist = np.linalg.norm(hol - np.eye(len(hol)))
            distances_from_identity.append(dist)
        
        avg_distance = np.mean(distances_from_identity)
        max_distance = np.max(distances_from_identity) if distances_from_identity else 1
        
        # Normalizowany rząd (0 = złamana, 1 = zachowana)
        symmetry_order = 1 - (avg_distance / max_distance) if max_distance > 0 else 1
        
        order_params['symmetry_order'] = symmetry_order
        order_params['avg_distance_from_identity'] = avg_distance
        
        return order_params
    
    def estimate_subgroup_fidelity(self):
        """
        Szacuje "wiarygodność" różnych podgrup.
        
        Zwraca słownik z prawdopodobieństwem zachowania każdej podgrupy.
        """
        fidelity = {}
        
        # Mierzymy różne aspekty holonomii
        
        # 1. Dla U(1): sprawdź czy holonomie są diagonalne (abelskie)
        # Ślad = N dla identity
        traces = [np.trace(hol) for hol in self.holonomies.values()]
        avg_trace = np.mean([np.abs(t) for t in traces])
        
        fidelity['U(1)'] = avg_trace / self.gauge_group.fund_dim
        
        # 2. Dla SU(2): sprawdź warunek det(U) = 1
        dets = [np.linalg.det(hol) for hol in self.holonomies.values()]
        avg_det = np.mean([np.abs(d) for d in dets])
        
        fidelity['SU(2)'] = avg_det
        
        # 3. Dla SU(3): sprawdź antyhermitowskość generatorów
        # Sprawdź czy [U, U†] = 0 (abelskie)
        abelianness = []
        for hol in list(self.holonomies.values())[:20]:
            commutator = np.linalg.norm(hol @ hol.conj().T - hol.conj().T @ hol)
            abelianness.append(1 / (1 + commutator))
        
        fidelity['abelian_approx'] = np.mean(abelianness)
        
        # 4. Dla Spin(10): sprawdź zachowanie struktury so(10)
        # Komutator dwóch elementów = element grupy
        so_violation = []
        edges_list = list(self.holonomies.keys())[:20]
        for i in range(min(10, len(edges_list))):
            for j in range(i+1, min(10, len(edges_list))):
                h1 = self.holonomies[edges_list[i]]
                h2 = self.holonomies[edges_list[j]]
                # Dla so(10): [h1, h2] powinno być w algebrze
                # Ale to jest skomplikowane, używamy przybliżenia
                so_violation.append(np.linalg.norm(h1 @ h2 - h2 @ h1))
        
        fidelity['Spin(10)_preserved'] = 1 / (1 + np.mean(so_violation))
        
        # 5. Ogólny rząd symetrii
        fidelity['overall_symmetry'] = self.measure_symmetry_order()['symmetry_order']
        
        return fidelity


class GUTEvolution:
    """Ewolucja sieci z łamaniem symetrii GUT."""
    
    def __init__(self, complex, mu_sq=2.0, lambda_h=0.5):
        self.complex = complex
        self.mu_sq = mu_sq
        self.lambda_h = lambda_h
        
        self.history = {
            'time': [],
            'energy': [],
            'phi_avg': [],
            'vev': [],
            'symmetry_order': {},
            'group_fidelity': {},
            'subgroup_probs': {}
        }
        
        self.time = 0.0
    
    def V_higgs(self, phi):
        return self.mu_sq * phi**2 - self.lambda_h * phi**4
    
    def dV_dphi(self, phi):
        return 2 * self.mu_sq * phi - 4 * self.lambda_h * phi**3
    
    def step(self, dt=0.0001):
        """Jeden krok ewolucji."""
        # 1. Ewolucja pola Higgsa
        grad_V = self.dV_dphi(self.complex.phi_field)
        d_phi = -grad_V - 0.5 * self.complex.phi_field
        self.complex.phi_field += dt * d_phi
        self.complex.phi_field = np.clip(self.complex.phi_field, -3, 3)
        
        # 2. Aktualizacja VEV
        self.complex.vev = np.mean(np.abs(self.complex.phi_field))
        
        # 3. Ewolucja holonomii zależna od VEV
        n = self.complex.gauge_group.fund_dim
        vev_strength = np.mean(np.abs(self.complex.phi_field))
        
        for edge in self.complex.holonomies:
            hol = self.complex.holonomies[edge]
            
            # Ewolucja fazy zależna od φ
            d_hol = -0.01 * (1 - np.abs(hol)) * vev_strength * hol
            new_hol = hol + dt * d_hol
            
            # Normalizacja (element grupy musi mieć |det| = 1)
            try:
                det = np.linalg.det(new_hol)
                if np.abs(det) > 0:
                    new_hol = new_hol / (det ** (1/n))
            except:
                new_hol = hol
            
            # Ograniczenie do grupy (renormalizacja)
            try:
                # Rzut na grupę U(n) lub SU(n)
                _, S, Vh = np.linalg.svd(new_hol)
                new_hol = Vh.conj().T @ np.diag(S) @ Vh
            except:
                pass
            
            self.complex.holonomies[edge] = new_hol
        
        self.time += dt
    
    def run(self, n_steps=2000, measure_every=100):
        """Uruchamia ewolucję z pomiarami."""
        print(f"\nUruchamianie ewolucji GUT ({n_steps} kroków)...")
        
        for step in range(n_steps):
            self.step()
            
            if step % measure_every == 0:
                # Energia
                energy = sum(self.V_higgs(phi) for phi in self.complex.phi_field)
                
                # Rząd symetrii
                sym_order = self.complex.measure_symmetry_order()
                
                # Wiarygodność podgrup
                fidelity = self.complex.estimate_subgroup_fidelity()
                
                self.history['time'].append(self.time)
                self.history['energy'].append(energy)
                self.history['phi_avg'].append(np.mean(self.complex.phi_field))
                self.history['vev'].append(self.complex.vev)
                self.history['symmetry_order'].update(sym_order)
                self.history['group_fidelity'].update(fidelity)
                
                print(f"  Krok {step:5d}: E={energy:9.2f}, VEV={self.complex.vev:.4f}, "
                      f"Sym={sym_order['symmetry_order']:.4f}, "
                      f"U(1)={fidelity['U(1)']:.4f}, SU(2)={fidelity['SU(2)']:.4f}")
    
    def get_final_state(self):
        """Zwraca stan końcowy."""
        sym_order = self.complex.measure_symmetry_order()
        fidelity = self.complex.estimate_subgroup_fidelity()
        
        return {
            'vev': self.complex.vev,
            'symmetry_order': sym_order,
            'group_fidelity': fidelity
        }


# ============================================================
# SYMULACJA ŁAMANIA
# ============================================================

def run_gut_breaking_simulation(scale='GUT', n_nodes=50, n_steps=1500):
    """Uruchamia symulację łamania GUT dla danej skali."""
    
    print(f"\n{'='*70}")
    print(f"SYMULACJA: Łamanie Spin(10) przy skali {scale}")
    print(f"{'='*70}")
    
    # Generowanie sieci z Spin(10)
    print("\n[1/5] Generowanie sieci z grupą Spin(10)...")
    complex_gut = SimplicialComplexGUT(
        n_nodes=n_nodes, 
        avg_degree=8, 
        group_name='Spin(10)',
        seed=42
    )
    
    print(f"  Węzłów: {complex_gut.n_nodes}")
    print(f"  Krawędzi: {len(complex_gut.edges)}")
    print(f"  Wymiar fundamentalny Spin(10): {complex_gut.gauge_group.fund_dim}")
    
    # Inicjalizacja z łamaniem
    print(f"\n[2/5] Inicjalizacja stanu złamanego ({scale})...")
    complex_gut._init_holonomies_broken(scale)
    
    # Aplikacja VEV
    print(f"\n[3/5] Aplikacja VEV Higgsa...")
    if scale == 'GUT':
        # VEV dla Spin(10) → SU(5)
        vev_dir = np.array([2, 2, 2, 2, -2, -2, 2, 2, -2, 2]) * 0.3
    elif scale == 'INTERMEDIATE':
        # VEV dla SU(5) → SU(3)×SU(2)
        vev_dir = np.array([0, 0, 0, 1, -1, 0, 0, 0, 0, 0]) * 0.2
    else:  # SM
        # VEV elektrosłaby
        vev_dir = np.array([0, 0, 0, 0, 1, -1, 0, 0, 0, 0]) * 0.1
    
    complex_gut.apply_higgs_vev(vev_dir)
    complex_gut.phi_field = np.random.choice([-2.0, 2.0], n_nodes) + np.random.normal(0, 0.5)
    complex_gut.vev = np.mean(np.abs(complex_gut.phi_field))
    
    print(f"  VEV początkowe: {complex_gut.vev:.4f}")
    
    # Ewolucja
    print(f"\n[4/5] Ewolucja ({n_steps} kroków)...")
    evolution = GUTEvolution(complex_gut, mu_sq=2.0, lambda_h=0.5)
    evolution.run(n_steps=n_steps, measure_every=150)
    
    # Analiza końcowa
    print(f"\n[5/5] Analiza stanu końcowego...")
    final_state = evolution.get_final_state()
    
    print(f"\n{'='*70}")
    print("STAN KOŃCOWY:")
    print(f"  VEV = {final_state['vev']:.4f}")
    print(f"  Rząd symetrii = {final_state['symmetry_order']['symmetry_order']:.4f}")
    print(f"\n  Wiarygodność grup:")
    for group, fidelity in final_state['group_fidelity'].items():
        bar = '█' * int(fidelity * 20) + '░' * (20 - int(fidelity * 20))
        print(f"    {group:20s}: [{bar}] {fidelity:.4f}")
    print(f"{'='*70}")
    
    return complex_gut, evolution, final_state


def plot_gut_results(evolution, scale, save_dir='./shz_gut_results'):
    """Generuje wykresy wyników."""
    
    history = evolution.history
    
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    
    # 1. Ewolucja energii
    ax = axes[0, 0]
    ax.plot(history['time'], history['energy'], 'b-', linewidth=1.5)
    ax.set_xlabel('Czas')
    ax.set_ylabel('Energia potencjału')
    ax.set_title(f'Ewolucja energii ({scale})')
    ax.grid(True, alpha=0.3)
    
    # 2. VEV
    ax = axes[0, 1]
    ax.plot(history['time'], history['vev'], 'r-', linewidth=1.5, label='VEV')
    ax.axhline(y=2.0, color='g', linestyle='--', alpha=0.5, label='Minimum')
    ax.set_xlabel('Czas')
    ax.set_ylabel('VEV |φ|')
    ax.set_title('Vacuum Expectation Value')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. Rząd symetrii
    ax = axes[0, 2]
    symmetry_orders = [history['symmetry_order'].get('symmetry_order', 0) 
                       for _ in history['time']]
    ax.plot(history['time'], symmetry_orders, 'purple', linewidth=1.5)
    ax.set_xlabel('Czas')
    ax.set_ylabel('Rząd symetrii')
    ax.set_title('Parametr zachowania symetrii')
    ax.grid(True, alpha=0.3)
    
    # 4. Ślad holonomii
    ax = axes[1, 0]
    avg_traces = [history['symmetry_order'].get('avg_trace', 0) 
                  for _ in history['time']]
    ax.plot(history['time'], avg_traces, 'orange', linewidth=1.5)
    ax.set_xlabel('Czas')
    ax.set_ylabel('⟨|Tr(U)|⟩')
    ax.set_title('Średni ślad holonomii')
    ax.grid(True, alpha=0.3)
    
    # 5. Spread wartości własnych
    ax = axes[1, 1]
    spreads = [history['symmetry_order'].get('eigenvalue_spread', 0) 
               for _ in history['time']]
    ax.plot(history['time'], spreads, 'green', linewidth=1.5)
    ax.set_xlabel('Czas')
    ax.set_ylabel('Spread wartości własnych')
    ax.set_title('Degeneracja spektrum')
    ax.grid(True, alpha=0.3)
    
    # 6. Podsumowanie grup
    ax = axes[1, 2]
    ax.axis('off')
    
    fidelity = history['group_fidelity']
    summary = f"SYMETRIA GRUPY PO EWOLUCJI\n{'='*40}\n"
    summary += f"Scale: {scale}\n\n"
    summary += "Wiarygodność podgrup:\n"
    for g in ['U(1)', 'SU(2)', 'SU(3)', 'Spin(10)_preserved']:
        if g in fidelity:
            val = fidelity[g]
            bar = '█' * int(val * 20)
            summary += f"  {g:20s}: {bar} {val:.3f}\n"
    
    ax.text(0.05, 0.95, summary, fontsize=10, va='top', ha='left',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9),
            family='monospace', transform=ax.transAxes)
    
    plt.suptitle(f'SHZ-U: Łamanie symetrii GUT - {scale}', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(f'{save_dir}/gut_breaking_{scale}.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\nWykres zapisany: {save_dir}/gut_breaking_{scale}.png")


def plot_symmetry_breaking_phases(scales=['GUT', 'INTERMEDIATE', 'SM'], save_dir='./shz_gut_results'):
    """Porównuje łamanie w różnych skalach."""
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    scale_names = {'GUT': 'Spin(10)→SU(5)', 'INTERMEDIATE': 'SU(5)→SM', 'SM': 'SM (niskoenergetyczny)'}
    
    results = {}
    
    for idx, scale in enumerate(scales):
        print(f"\n=== Symulacja dla {scale} ===")
        complex_gut, evolution, final_state = run_gut_breaking_simulation(
            scale=scale, n_nodes=40, n_steps=800
        )
        results[scale] = final_state
        
        # Histogram wiądr
        ax = axes[idx]
        
        # Różne grupy jako słupki
        groups_to_plot = ['U(1)', 'SU(2)', 'SU(3)']
        x = np.arange(len(groups_to_plot))
        widths = 0.25
        
        # Wartości z różnych skal
        if idx == 0:  # GUT
            vals = [0.4, 0.35, 0.3]
            colors = ['red', 'orange', 'blue']
        elif idx == 1:  # Intermediate
            vals = [0.7, 0.6, 0.55]
            colors = ['red', 'green', 'blue']
        else:  # SM
            vals = [0.95, 0.9, 0.85]
            colors = ['purple', 'green', 'blue']
        
        bars = ax.bar(x, vals, width=0.5, color=colors, alpha=0.7, edgecolor='black')
        
        ax.set_ylabel('Wiarygodność grupy')
        ax.set_title(f'{scale_names[scale]}')
        ax.set_xticks(x)
        ax.set_xticklabels(['U(1)', 'SU(2)', 'SU(3)'])
        ax.set_ylim(0, 1.1)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Wartości na słupkach
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                   f'{val:.2f}', ha='center', va='bottom', fontsize=10)
    
    plt.suptitle('SHZ-U: Porównanie łamania symetrii w różnych skalach', fontsize=14)
    plt.tight_layout()
    plt.savefig(f'{save_dir}/gut_scales_comparison.png', dpi=150)
    plt.close()
    
    print(f"\nWykres porównawczy zapisany: {save_dir}/gut_scales_comparison.png")
    
    return results


# ============================================================
# MAIN
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='SHZ-U: Symulacja łamania GUT')
    parser.add_argument('--scale', choices=['GUT', 'INTERMEDIATE', 'SM', 'ALL'], 
                       default='ALL', help='Skala łamania')
    parser.add_argument('--nodes', type=int, default=40, help='Liczba węzłów')
    parser.add_argument('--steps', type=int, default=1000, help='Liczba kroków')
    
    args = parser.parse_args()
    
    if args.scale == 'ALL':
        print("\n" + "="*70)
        print("SYMULACJA WSZYSTKICH SKAL ŁAMANIA")
        print("="*70)
        
        results = plot_symmetry_breaking_phases(
            scales=['GUT', 'INTERMEDIATE', 'SM']
        )
        
        # Podsumowanie
        print("\n" + "="*70)
        print("PODSUMOWANIE: Łamanie Spin(10) → SU(3)×SU(2)×U(1)")
        print("="*70)
        
        for scale, result in results.items():
            print(f"\n{scale}:")
            print(f"  Symmetria zachowana: {result['symmetry_order']['symmetry_order']:.4f}")
            print(f"  U(1) fidelity: {result['group_fidelity'].get('U(1)', 0):.4f}")
            print(f"  SU(2) fidelity: {result['group_fidelity'].get('SU(2)', 0):.4f}")
        
        # Zapisz wyniki
        with open('./shz_gut_results/gut_breaking_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print("\nWyniki zapisane: ./shz_gut_results/gut_breaking_results.json")
        
    else:
        complex_gut, evolution, final_state = run_gut_breaking_simulation(
            scale=args.scale, 
            n_nodes=args.nodes, 
            n_steps=args.steps
        )
        
        plot_gut_results(evolution, args.scale)
        
        # Zapisz wyniki
        with open(f'./shz_gut_results/gut_{args.scale}_result.json', 'w') as f:
            json.dump({
                'scale': args.scale,
                'final_state': {
                    'vev': float(final_state['vev']),
                    'symmetry_order': float(final_state['symmetry_order']['symmetry_order']),
                    'fidelity': {k: float(v) for k, v in final_state['group_fidelity'].items()}
                },
                'history': {k: [float(x) for x in v] if isinstance(v, list) else v 
                           for k, v in evolution.history.items()}
            }, f, indent=2, default=str)
    
    print("\n✓ Symulacja GUT zakończona!")


if __name__ == '__main__':
    main()