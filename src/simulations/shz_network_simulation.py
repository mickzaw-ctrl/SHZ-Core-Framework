#!/usr/bin/env python3
"""
SHZ-U: Symulacja numeryczna sieci horyzontów
=============================================
Program do generowania i badania ewolucji sieci pod wpływem Hamiltonianu SHZ-U.
Analiza spontanicznego łamania symetrii: Spin(10) → SU(3)×SU(2)×U(1)

Autor: Michał Ślusarczyk
Data: 13 czerwca 2026
Wersja: 1.0

Użycie:
    python3 shz_network_simulation.py [--nodes N] [--edges-per-node K] [--steps S]
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy import sparse
from scipy.sparse.linalg import eigs
from collections import defaultdict
import itertools
import argparse
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# STAŁE FIZYCZNE (w jednostkach naturalnych)
# ============================================================
hbar = 1.0
c = 1.0
G_N = 1.0 / 16  # Stała grawitacyjna (normalizowana dla numeryki)
omega_P = 1.0   # Częstotliwość Plancka
k_bar = 8       # Warunek stabilności dla d=4

# Parametry symulacji
alpha_GUT = 1/25  # Stała sprzężenia przy skali GUT
M_GUT = 1e16      # Skala GUT w GeV (znormalizowana)

class SimplicialComplex:
    """Klasa reprezentująca kompleks symplicjalny sieci horyzontów."""
    
    def __init__(self, n_nodes, avg_degree, dimension=4, seed=None):
        """
        Inicjalizacja kompleksu symplicjalnego.
        
        Args:
            n_nodes: Liczba węzłów (wierzchołków)
            avg_degree: Średni stopień węzła (k̄)
            dimension: Wymiar kompleksu
            seed: Seed dla generatora losowego
        """
        self.n_nodes = n_nodes
        self.avg_degree = avg_degree
        self.dimension = dimension
        self.seed = seed or np.random.randint(1e9)
        np.random.seed(self.seed)
        
        # Struktury danych
        self.nodes = list(range(n_nodes))
        self.edges = []       # Lista krawędzi (1-sympleksów)
        self.triangles = []   # Lista trójkątów (2-sympleksów)
        self.tetrahedra = []  # Lista tetraedrów (3-sympleksów)
        
        # Atrybuty węzłów
        self.node_energies = np.zeros(n_nodes)
        self.edge_lengths = {}
        self.holonomies = {}  # Holonomie na krawędziach
        
        # Macierze incydencji
        self.incidence_1 = None  # ∂_1: C_1 → C_0
        self.incidence_2 = None  # ∂_2: C_2 → C_1
        self.incidence_3 = None  # ∂_3: C_3 → C_2
        
        self._generate_complex()
    
    def _generate_complex(self):
        """Generuje losowy kompleks symplicjalny."""
        # Krok 1: Generowanie grafu (krawędzi)
        self._generate_edges()
        
        # Krok 2: Generowanie wyższych sympleksów
        self._generate_higher_simplices()
        
        # Krok 3: Inicjalizacja energii i długości
        self._initialize_attributes()
        
        # Krok 4: Budowanie macierzy incydencji
        self._build_incidence_matrices()
    
    def _generate_edges(self):
        """Generuje krawędzie grafu z zadanym średnim stopniem."""
        target_edges = int(self.n_nodes * self.avg_degree / 2)
        
        # Inicjalizacja losowego grafu
        for i in range(self.n_nodes):
            for j in range(i + 1, self.n_nodes):
                if np.random.random() < 0.3:  # Prawdopodobieństwo krawędzi
                    self.edges.append((i, j))
        
        # Dopasowanie do docelowej liczby krawędzi
        while len(self.edges) < target_edges:
            i, j = np.random.choice(self.n_nodes, 2, replace=False)
            if (i, j) not in self.edges and (j, i) not in self.edges:
                self.edges.append((i, j))
        
        # Usunięcie nadmiarowych krawędzi
        while len(self.edges) > target_edges:
            idx = np.random.randint(len(self.edges))
            self.edges.pop(idx)
    
    def _generate_higher_simplices(self):
        """Generuje wyższe sympleksy (trójkąty, tetraedry)."""
        # Znajdowanie trójkątów (cliques rozmiaru 3)
        edge_set = set(tuple(sorted(e)) for e in self.edges)
        
        for i, j, k in itertools.combinations(self.nodes, 3):
            if (i, j) in edge_set and (j, k) in edge_set and (i, k) in edge_set:
                # Sprawdzenie geometrii (kąt < π dla sympleksu)
                if np.random.random() < 0.5:  # 50% szansa na 2-sympleks
                    self.triangles.append((i, j, k))
        
        # Znajdowanie tetraedrów (cliques rozmiaru 4)
        for i, j, k, l in itertools.combinations(self.nodes, 4):
            if all(tuple(sorted(edge)) in edge_set 
                   for edge in [(i,j), (i,k), (i,l), (j,k), (j,l), (k,l)]):
                if np.random.random() < 0.3:  # 30% szansa na 3-sympleks
                    self.tetrahedra.append((i, j, k, l))
    
    def _initialize_attributes(self):
        """Inicjalizuje energia i długości krawędzi."""
        # Energię węzłów z rozkładem Boltzmanna
        self.node_energies = np.abs(np.random.normal(1.0, 0.1, self.n_nodes))
        
        # Długości krawędzi
        for edge in self.edges:
            self.edge_lengths[edge] = np.abs(np.random.normal(1.0, 0.05))
        
        # Holonomie (losowe macierze U(1) lub SU(N))
        self.holonomies = {}
        for edge in self.edges:
            phase = np.random.uniform(0, 2 * np.pi)
            self.holonomies[edge] = np.exp(1j * phase)
    
    def _build_incidence_matrices(self):
        """Buduje macierze incydencji ∂_p."""
        n_edges = len(self.edges)
        n_triangles = len(self.triangles)
        n_tetrahedra = len(self.tetrahedra)
        
        # ∂_1: krawędzie → węzły
        self.incidence_1 = sparse.lil_matrix((self.n_nodes, n_edges))
        for e_idx, (i, j) in enumerate(self.edges):
            self.incidence_1[i, e_idx] = -1
            self.incidence_1[j, e_idx] = 1
        
        # ∂_2: trójkąty → krawędzie
        if n_triangles > 0:
            self.incidence_2 = sparse.lil_matrix((n_edges, n_triangles))
            for t_idx, tri in enumerate(self.triangles):
                edges_in_tri = []
                for e_idx, edge in enumerate(self.edges):
                    if all(v in tri for v in edge):
                        edges_in_tri.append(e_idx)
                        self.incidence_2[e_idx, t_idx] = 1
        
        # ∂_3: tetraedry → trójkąty
        if n_tetrahedra > 0 and n_triangles > 0:
            self.incidence_3 = sparse.lil_matrix((n_triangles, n_tetrahedra))
            for th_idx, tetrah in enumerate(self.tetrahedra):
                for t_idx, tri in enumerate(self.triangles):
                    if all(v in tetrah for v in tri):
                        self.incidence_3[t_idx, th_idx] = 1
        
        # Konwersja do CSR dla efektywności
        self.incidence_1 = self.incidence_1.tocsr()
        if self.incidence_2 is not None:
            self.incidence_2 = self.incidence_2.tocsr()
        if self.incidence_3 is not None:
            self.incidence_3 = self.incidence_3.tocsr()
    
    def get_star(self, node):
        """Zwraca gwiazdę węzła (wszystkie sympleksy zawierające węzeł)."""
        star = {'edges': [], 'triangles': [], 'tetrahedra': []}
        for e_idx, (i, j) in enumerate(self.edges):
            if node in (i, j):
                star['edges'].append(e_idx)
        for t_idx, tri in enumerate(self.triangles):
            if node in tri:
                star['triangles'].append(t_idx)
        for th_idx, tetrah in enumerate(self.tetrahedra):
            if node in tetrah:
                star['tetrahedra'].append(th_idx)
        return star
    
    def get_degree(self, node):
        """Zwraca stopień węzła."""
        return len(self.get_star(node)['edges'])
    
    def compute_deficit_angle(self, node):
        """
        Oblicza kąt deficytu w węźle.
        ε(v) = 2π - Σ θ_e(v)
        """
        star = self.get_star(node)
        n_edges = len(star['edges'])
        
        if n_edges < 3:
            return 0.0
        
        # Średni kąt dla sieci symplicjalnej
        avg_angle = np.pi - 2 * np.pi / n_edges
        deficit = 2 * np.pi - n_edges * avg_angle
        
        return deficit
    
    def compute_laplacian(self):
        """Oblicza Laplace'a na grafie."""
        n = self.n_nodes
        L = np.zeros((n, n))
        
        for i in range(n):
            neighbors = [j for j, e in enumerate(self.edges) if i in e]
            L[i, i] = len(neighbors)
            for j in neighbors:
                L[i, j] = -1
        
        return L


class SHZ_Hamiltonian:
    """Hamiltonian sieci horyzontów SHZ-U."""
    
    def __init__(self, complex, coupling_strength=1.0):
        """
        Inicjalizacja Hamiltonianu.
        
        Args:
            complex: Obiekt SimplicialComplex
            coupling_strength: Stała sprzężenia λ
        """
        self.complex = complex
        self.lambda_coupling = coupling_strength
        
        # Parametry z SHZ-U
        self.hbar_omega0 = hbar * omega_P / 2
        self.k_bar_over_4 = k_bar / 4
    
    def compute_kinetic_term(self):
        """
        Oblicza człon kinetyczny Hamiltonianu.
        H_kin = Σ⟨i,j⟩ (ħω₀/2)(a†_i a_j + a†_j a_i)
        """
        H_kin = 0.0
        
        for edge in self.complex.edges:
            i, j = edge
            # Dla uproszczenia, używamy clasycznego przybliżenia
            # H_kin += (ħω₀/2) * (E_i * E_j) / (E_i + E_j)
            # gdzie E_i, E_j są energiami węzłów
            E_i = self.complex.node_energies[i]
            E_j = self.complex.node_energies[j]
            
            # Symulacja operatorów kreacji/anihilacji
            if E_i + E_j > 0:
                H_kin += self.hbar_omega0 * (E_i * E_j) / (E_i + E_j)
        
        return H_kin
    
    def compute_potential_term(self):
        """
        Oblicza człon potencjałowy z kątów deficytu.
        H_pot = (k̄/4) Σ (E_i + E_j - E_k)²
        """
        H_pot = 0.0
        
        # Iteracja po trójkątach (2-sympleksach)
        for triangle in self.complex.triangles:
            i, j, k = triangle
            E_i = self.complex.node_energies[i]
            E_j = self.complex.node_energies[j]
            E_k = self.complex.node_energies[k]
            
            # (E_i + E_j - E_k)²
            diff = E_i + E_j - E_k
            H_pot += self.k_bar_over_4 * diff ** 2
        
        return H_pot
    
    def compute_holonomy_term(self):
        """
        Oblicza człon z holonomii (pętli Wilsona).
        """
        H_hol = 0.0
        
        for triangle in self.complex.triangles:
            # Oblicz pętlę Wilsona na trójkącie
            product = 1.0 + 0j
            for edge in self._get_edges_in_triangle(triangle):
                product *= self.complex.holonomies.get(edge, 1.0 + 0j)
            
            # Ślad (dla U(1) to just the complex number)
            trace = np.real(product)
            H_hol += (1 - trace)  # Energia rośnie gdy holonomia ≠ 1
        
        return H_hol
    
    def _get_edges_in_triangle(self, triangle):
        """Zwraca krawędzie w trójkącie."""
        edges = []
        for e_idx, edge in enumerate(self.complex.edges):
            if all(v in triangle for v in edge):
                edges.append(edge)
        return edges
    
    def compute_total_energy(self):
        """Oblicza całkowitą energię Hamiltonianu."""
        return (self.compute_kinetic_term() + 
                self.compute_potential_term() + 
                self.compute_holonomy_term())
    
    def gradient(self, node):
        """Oblicza gradient Hamiltonianu względem energii węzła."""
        # Numeryczny gradient
        eps = 1e-8
        E_orig = self.complex.node_energies[node]
        
        self.complex.node_energies[node] = E_orig + eps
        E_plus = self.compute_total_energy()
        
        self.complex.node_energies[node] = E_orig - eps
        E_minus = self.compute_total_energy()
        
        self.complex.node_energies[node] = E_orig
        
        return (E_plus - E_minus) / (2 * eps)
    
    def hessian(self, node):
        """Oblicza Hesjan (drugą pochodną) względem energii węzła."""
        eps = 1e-8
        grad_plus = self.gradient(node)
        
        E_orig = self.complex.node_energies[node]
        self.complex.node_energies[node] = E_orig + eps
        grad_plus2 = self.gradient(node)
        
        self.complex.node_energies[node] = E_orig
        
        return (grad_plus2 - grad_plus) / eps


class NetworkEvolution:
    """Ewolucja sieci pod wpływem Hamiltonianu SHZ-U."""
    
    def __init__(self, complex_obj, hamiltonian, dt=0.01, damping=0.1):
        """
        Inicjalizacja ewolucji.
        
        Args:
            complex_obj: Obiekt SimplicialComplex
            hamiltonian: Obiekt SHZ_Hamiltonian
            dt: Krok czasowy
            damping: Współczynnik tłumienia
        """
        self.complex = complex_obj
        self.H = hamiltonian
        self.dt = dt
        self.damping = damping
        
        self.energy_history = []
        self.holonomy_history = []
        self.symmetry_order_params = []
        
        self.time = 0.0
    
    def step(self):
        """Wykona jeden krok ewolucji."""
        # Oblicz gradienty
        gradients = np.array([self.H.gradient(i) for i in range(self.complex.n_nodes)])
        
        # Dynamika z tłumieniem
        # dE/dt = -∇H - γ E
        dE = -gradients - self.damping * self.complex.node_energies
        
        # Aktualizacja energii
        self.complex.node_energies += self.dt * dE
        
        # Ewolucja holonomii (zależna od energii)
        for edge in self.complex.edges:
            i, j = edge
            d_phase = (self.complex.node_energies[i] + self.complex.node_energies[j]) / 2
            self.complex.holonomies[edge] *= np.exp(1j * self.dt * d_phase)
        
        # Normalizacja holonomii
        for edge in self.complex.holonomies:
            self.complex.holonomies[edge] /= np.abs(self.complex.holonomies[edge])
        
        self.time += self.dt
        
        # Zapis historii
        self.energy_history.append(self.H.compute_total_energy())
        self.holonomy_history.append(self._compute_average_holonomy())
        self.symmetry_order_params.append(self._compute_symmetry_order_params())
    
    def _compute_average_holonomy(self):
        """Oblicza średnią holonomię (wskaźnik łamania symetrii)."""
        if not self.complex.holonomies:
            return 0.0
        
        avg_trace = np.mean([np.abs(self.complex.holonomies[e]) 
                             for e in self.complex.holonomies])
        return avg_trace
    
    def _compute_symmetry_order_params(self):
        """
        Oblicza parametry rzędu dla symetrii gauge.
        """
        # Dla GUT → SM, parametr rzędu mierzy "odległość" od stanu symetrycznego
        params = {}
        
        # Parametr dla SU(N) symetrii
        triangle_traces = []
        for tri in self.complex.triangles:
            product = 1.0 + 0j
            for edge in self.H._get_edges_in_triangle(tri):
                product *= self.complex.holonomies.get(edge, 1.0 + 0j)
            triangle_traces.append(np.abs(product))
        
        params['triangle_order'] = np.mean(triangle_traces) if triangle_traces else 0.0
        
        # Parametr dla Spin(10) → SU(3)×SU(2)×U(1)
        # Mierzymy "deficit" w struktócie gauge
        deficit_angles = [self.complex.compute_deficit_angle(i) 
                         for i in range(self.complex.n_nodes)]
        params['deficit_variance'] = np.var(deficit_angles) if deficit_angles else 0.0
        
        return params
    
    def run(self, n_steps, verbose=True):
        """Uruchamia symulację."""
        if verbose:
            print(f"Rozpoczynam symulację: {n_steps} kroków")
            print(f"  dt = {self.dt}, damping = {self.damping}")
            print(f"  Węzłów: {self.complex.n_nodes}, Krawędzi: {len(self.complex.edges)}")
            print()
        
        for step in range(n_steps):
            self.step()
            
            if verbose and step % max(1, n_steps // 10) == 0:
                print(f"  Krok {step:6d}: E = {self.energy_history[-1]:.6f}, "
                      f"⟨W⟩ = {self.holonomy_history[-1]:.6f}")
        
        if verbose:
            print(f"\nZakończono. Czas symulacji: {self.time:.4f}")
        
        return self.energy_history, self.holonomy_history, self.symmetry_order_params


class SymmetryAnalyzer:
    """Analiza łamania symetrii w sieci."""
    
    def __init__(self, complex_obj):
        self.complex = complex_obj
    
    def compute_gauge_group_representation(self):
        """
        Komputeruje reprezentację grupy gauge z struktury sieci.
        
        W SHZ-U:
        - k̄ = 8 → Spin(10) lub SU(5) w skali GUT
        - Dynamical boundary → SU(3)×SU(2)×U(1) przy niskich energiach
        """
        n_nodes = self.complex.n_nodes
        n_edges = len(self.complex.edges)
        
        # Reprezentacja grupy z macierzy incydencji
        incidence_rank = np.linalg.matrix_rank(
            self.complex.incidence_1.toarray() if hasattr(self.complex.incidence_1, 'toarray') 
            else self.complex.incidence_1.todense()
        )
        
        # Wymiar przestrzeni fundamentalnej
        dim_fund = n_nodes - incidence_rank
        
        # Szacowanie grupy:
        # dim_fund = 5 → SU(5) lub Spin(10)
        # dim_fund = 4 → SU(4) 
        # dim_fund = 3 → SU(3)
        
        results = {
            'dim_fundamental': dim_fund,
            'n_nodes': n_nodes,
            'n_edges': n_edges,
            'estimated_group': self._estimate_group(dim_fund),
            'k_bar': self._estimate_k_bar()
        }
        
        return results
    
    def _estimate_group(self, dim):
        """Szacuje grupę gauge z wymiaru reprezentacji."""
        if dim >= 10:
            return "Spin(10) lub SO(10)"
        elif dim == 5:
            return "SU(5)"
        elif dim == 4:
            return "SU(4) lub Spin(6)"
        elif dim == 3:
            return "SU(3)"
        elif dim == 2:
            return "SU(2)"
        else:
            return "U(1)"
    
    def _estimate_k_bar(self):
        """Szacuje średni stopień k̄."""
        degrees = [self.complex.get_degree(i) for i in range(self.complex.n_nodes)]
        return np.mean(degrees)
    
    def analyze_symmetry_breaking(self, holonomy_data):
        """
        Analizuje spontaniczne łamanie symetrii.
        
        Args:
            holonomy_data: Lista wartości średniej holonomii w czasie
        
        Returns:
            Dictionary z parametrami łamania
        """
        holonomy_data = np.array(holonomy_data)
        
        # Początkowa holonomia (stan symetryczny)
        initial_holonomy = holonomy_data[0] if len(holonomy_data) > 0 else 1.0
        
        # Końcowa holonomia (stan złamany)
        final_holonomy = holonomy_data[-1] if len(holonomy_data) > 0 else 1.0
        
        # Czas łamania (gdy holonomia spada poniżej progu)
        threshold = 0.9 * initial_holonomy
        breaking_time = None
        for i, h in enumerate(holonomy_data):
            if h < threshold:
                breaking_time = i
                break
        
        # Wielkość łamania
        symmetry_breaking_strength = abs(initial_holonomy - final_holonomy)
        
        results = {
            'initial_holonomy': initial_holonomy,
            'final_holonomy': final_holonomy,
            'breaking_time': breaking_time,
            'symmetry_breaking_strength': symmetry_breaking_strength,
            'is_symmetry_broken': symmetry_breaking_strength > 0.01
        }
        
        return results
    
    def compute_vev(self, holonomy_data):
        """
        Oblicza vacuum expectation value z danych holonomii.
        
        W SHZ-U: ⟨Φ⟩ odpowiada dewiacji holonomii od 1.
        """
        if len(holonomy_data) == 0:
            return 0.0
        
        # VEV jako odchylenie od stanu symetrycznego
        vev = 1.0 - np.mean(holonomy_data)
        return max(0.0, vev)
    
    def estimate_higgs_mass(self, energy_data):
        """
        Szacuje masę Higgsa z danych energetycznych.
        
        Przybliżenie: m_H² ∝ |曲率 effektive potential|
        """
        if len(energy_data) < 10:
            return 0.0
        
        energy_data = np.array(energy_data)
        
        # Druga różnica (approx second derivative)
        second_diff = np.diff(energy_data, n=2)
        
        # Średnia "krzywizna" potencjału
        curvature = np.mean(second_diff[-len(second_diff)//2:])
        
        # Szacunkowa masa (w jednostkach naturalnych)
        m_H_squared = abs(curvature) / (self.complex.n_nodes * len(self.complex.edges))
        
        return np.sqrt(max(0, m_H_squared))


class Visualization:
    """Wizualizacja wyników symulacji."""
    
    def __init__(self, save_path='./plots'):
        self.save_path = save_path
        import os
        os.makedirs(save_path, exist_ok=True)
    
    def plot_energy_evolution(self, energy_data, save_name='energy_evolution.png'):
        """Wykres ewolucji energii."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(energy_data, 'b-', linewidth=1)
        ax.set_xlabel('Krok czasowy', fontsize=12)
        ax.set_ylabel('Energia całkowita', fontsize=12)
        ax.set_title('Ewolucja energii Hamiltonianu SHZ-U', fontsize=14)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.save_path}/{save_name}', dpi=150)
        plt.close()
    
    def plot_holonomy_evolution(self, holonomy_data, save_name='holonomy_evolution.png'):
        """Wykres ewolucji holonomii."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(holonomy_data, 'r-', linewidth=1)
        ax.axhline(y=1.0, color='k', linestyle='--', label='Stan symetryczny')
        ax.set_xlabel('Krok czasowy', fontsize=12)
        ax.set_ylabel('Średnia holonomia ⟨W⟩', fontsize=12)
        ax.set_title('Ewolucja holonomii (parametr łamania symetrii)', fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.save_path}/{save_name}', dpi=150)
        plt.close()
    
    def plot_network_structure(self, complex_obj, save_name='network_structure.png'):
        """Wizualizacja struktury sieci (dla małych grafów)."""
        if complex_obj.n_nodes > 50:
            print("Graf zbyt duży dla wizualizacji 2D")
            return
        
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Pozycje węzłów (losowe z rozproszeniem)
        np.random.seed(42)
        pos = {i: np.random.randn(2) for i in range(complex_obj.n_nodes)}
        
        # Rysowanie krawędzi
        for edge in complex_obj.edges:
            i, j = edge
            x = [pos[i][0], pos[j][0]]
            y = [pos[i][1], pos[j][1]]
            ax.plot(x, y, 'k-', alpha=0.3, linewidth=0.5)
        
        # Rysowanie węzłów (kolor = energia)
        energies = complex_obj.node_energies
        colors = (energies - energies.min()) / (energies.max() - energies.min() + 1e-10)
        
        for i in range(complex_obj.n_nodes):
            ax.scatter(pos[i][0], pos[i][1], c=[colors[i]], 
                      s=100, vmin=0, vmax=1, cmap='coolwarm')
        
        ax.set_title('Struktura sieci horyzontów\n(kolor = energia węzła)', fontsize=14)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(f'{self.save_path}/{save_name}', dpi=150)
        plt.close()
    
    def plot_deficit_angles(self, complex_obj, save_name='deficit_angles.png'):
        """Rozkład kątów deficytu."""
        deficit_angles = [complex_obj.compute_deficit_angle(i) 
                         for i in range(complex_obj.n_nodes)]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.hist(deficit_angles, bins=30, edgecolor='black', alpha=0.7)
        ax.axvline(x=np.mean(deficit_angles), color='r', linestyle='--', 
                   label=f'Średnia: {np.mean(deficit_angles):.4f}')
        ax.set_xlabel('Kąt deficytu ε(v)', fontsize=12)
        ax.set_ylabel('Liczba węzłów', fontsize=12)
        ax.set_title('Rozkład kątów deficytu w sieci', fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.save_path}/{save_name}', dpi=150)
        plt.close()
    
    def plot_symmetry_breaking_analysis(self, sym_results, save_name='symmetry_breaking.png'):
        """Wizualizacja analizy łamania symetrii."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Panel 1: Siła łamania
        ax1 = axes[0]
        labels = ['Początkowa\nholonomia', 'Końcowa\nholonomia', 'Siła\nłamania']
        values = [sym_results['initial_holonomy'], 
                  sym_results['final_holonomy'],
                  sym_results['symmetry_breaking_strength']]
        colors = ['green', 'red', 'blue']
        ax1.bar(labels, values, color=colors, alpha=0.7)
        ax1.set_ylabel('Wartość', fontsize=12)
        ax1.set_title('Analiza łamania symetrii', fontsize=14)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Panel 2: Czas łamania
        ax2 = axes[1]
        if sym_results['breaking_time'] is not None:
            ax2.text(0.5, 0.5, f"Czas łamania:\n{sym_results['breaking_time']} kroków",
                    fontsize=16, ha='center', va='center',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
        else:
            ax2.text(0.5, 0.5, "Brak łamania\nsymetrii", fontsize=16, ha='center', va='center',
                    bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
        ax2.axis('off')
        
        plt.tight_layout()
        plt.savefig(f'{self.save_path}/{save_name}', dpi=150)
        plt.close()
    
    def plot_3d_energy_surface(self, complex_obj, save_name='energy_surface_3d.png'):
        """3D wizualizacja powierzchni energetycznej."""
        if complex_obj.n_nodes > 30:
            print("Graf zbyt duży dla wizualizacji 3D")
            return
        
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Pozycje węzłów
        np.random.seed(42)
        x = np.random.randn(complex_obj.n_nodes)
        y = np.random.randn(complex_obj.n_nodes)
        z = complex_obj.node_energies
        
        # Rysowanie krawędzi jako linie
        for edge in complex_obj.edges:
            i, j = edge
            ax.plot([x[i], x[j]], [y[i], y[j]], [z[i], z[j]], 
                   'b-', alpha=0.2, linewidth=0.5)
        
        # Węzły jako scatter
        ax.scatter(x, y, z, c=z, cmap='viridis', s=100)
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Energia')
        ax.set_title('Powierzchnia energetyczna sieci (3D)', fontsize=14)
        
        plt.tight_layout()
        plt.savefig(f'{self.save_path}/{save_name}', dpi=150)
        plt.close()


def run_simulation(n_nodes=50, avg_degree=8, n_steps=500, seed=42, verbose=True):
    """
    Uruchamia pełną symulację sieci SHZ-U.
    
    Args:
        n_nodes: Liczba węzłów
        avg_degree: Średni stopień (k̄)
        n_steps: Liczba kroków czasowych
        seed: Seed losowy
        verbose: Czy wypisywać postęp
    
    Returns:
        Dictionary z wynikami
    """
    print("=" * 60)
    print("SHZ-U: Symulacja numeryczna sieci horyzontów")
    print("=" * 60)
    print()
    
    start_time = datetime.now()
    
    # Generowanie kompleksu
    if verbose:
        print(f"[1/5] Generowanie kompleksu symplicjalnego...")
        print(f"       Węzłów: {n_nodes}, Średni stopień: {avg_degree}")
    
    complex_obj = SimplicialComplex(n_nodes, avg_degree, dimension=4, seed=seed)
    
    if verbose:
        print(f"       Krawędzi: {len(complex_obj.edges)}")
        print(f"       Trójkątów: {len(complex_obj.triangles)}")
        print(f"       Tetraedrów: {len(complex_obj.tetrahedra)}")
        print()
    
    # Inicjalizacja Hamiltonianu
    if verbose:
        print(f"[2/5] Inicjalizacja Hamiltonianu SHZ-U...")
    
    hamiltonian = SHZ_Hamiltonian(complex_obj, coupling_strength=1/16)
    initial_energy = hamiltonian.compute_total_energy()
    
    if verbose:
        print(f"       Energia początkowa: {initial_energy:.6f}")
        print()
    
    # Inicjalizacja ewolucji
    if verbose:
        print(f"[3/5] Konfiguracja ewolucji...")
        print(f"       Krok czasowy: 0.01, Tłumienie: 0.1")
        print()
    
    evolution = NetworkEvolution(complex_obj, hamiltonian, dt=0.01, damping=0.1)
    
    # Uruchomienie symulacji
    if verbose:
        print(f"[4/5] Uruchamianie symulacji ({n_steps} kroków)...")
    
    energy_history, holonomy_history, sym_params = evolution.run(n_steps, verbose=verbose)
    
    if verbose:
        print()
        print(f"       Energia końcowa: {energy_history[-1]:.6f}")
        print(f"       Zmiana energii: {(energy_history[-1] - energy_history[0])/energy_history[0]*100:.2f}%")
        print()
    
    # Analiza symetrii
    if verbose:
        print(f"[5/5] Analiza łamania symetrii...")
    
    sym_analyzer = SymmetryAnalyzer(complex_obj)
    gauge_info = sym_analyzer.compute_gauge_group_representation()
    sym_break_results = sym_analyzer.analyze_symmetry_breaking(holonomy_history)
    vev = sym_analyzer.compute_vev(holonomy_history)
    hodge_mass = sym_analyzer.estimate_higgs_mass(energy_history)
    
    if verbose:
        print(f"       Szacowana grupa gauge: {gauge_info['estimated_group']}")
        print(f"       Wymiar fundamentalny: {gauge_info['dim_fundamental']}")
        print(f"       VEV (pole Higgsa): {vev:.6f}")
        print(f"       Szacunkowa masa Higgsa: {hodge_mass:.4f}")
        print()
    
    # Wizualizacja
    if verbose:
        print("Generowanie wizualizacji...")
    
    viz = Visualization(save_path='./shz_results')
    
    viz.plot_energy_evolution(energy_history)
    viz.plot_holonomy_evolution(holonomy_history)
    viz.plot_network_structure(complex_obj)
    viz.plot_deficit_angles(complex_obj)
    viz.plot_symmetry_breaking_analysis(sym_break_results)
    
    if n_nodes <= 30:
        viz.plot_3d_energy_surface(complex_obj)
    
    if verbose:
        print("Wizualizacja zapisana w ./shz_results/")
        print()
    
    # Podsumowanie
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("=" * 60)
    print("PODSUMOWANIE SYMULACJI")
    print("=" * 60)
    print(f"Czas wykonania: {duration:.2f} s")
    print(f"Konfiguracja sieci:")
    print(f"  - Węzły: {n_nodes}")
    print(f"  - Średni stopień: {avg_degree}")
    print(f"  - Krawędzie: {len(complex_obj.edges)}")
    print(f"Wyniki energetyczne:")
    print(f"  - E_początkowa: {energy_history[0]:.6f}")
    print(f"  - E_końcowa: {energy_history[-1]:.6f}")
    print(f"  - Zmiana: {(energy_history[-1] - energy_history[0])/energy_history[0]*100:.2f}%")
    print(f"Wyniki symetrii:")
    print(f"  - Szacowana grupa: {gauge_info['estimated_group']}")
    print(f"  - Holonomia ⟨W⟩: {holonomy_history[-1]:.6f}")
    print(f"  - VEV Higgsa: {vev:.6f}")
    print(f"  - Masa Higgsa: {hodge_mass:.4f}")
    print(f"  - Łamanie symetrii: {'TAK' if sym_break_results['is_symmetry_broken'] else 'NIE'}")
    print("=" * 60)
    
    results = {
        'configuration': {
            'n_nodes': n_nodes,
            'avg_degree': avg_degree,
            'n_edges': len(complex_obj.edges),
            'n_triangles': len(complex_obj.triangles),
            'n_tetrahedra': len(complex_obj.tetrahedra),
            'seed': seed,
            'n_steps': n_steps
        },
        'energy': {
            'initial': energy_history[0],
            'final': energy_history[-1],
            'history': energy_history
        },
        'holonomy': {
            'initial': holonomy_history[0],
            'final': holonomy_history[-1],
            'history': holonomy_history
        },
        'symmetry': {
            'estimated_group': gauge_info['estimated_group'],
            'dim_fundamental': gauge_info['dim_fundamental'],
            'vev': vev,
            'higgs_mass_estimate': hodge_mass,
            'symmetry_broken': sym_break_results['is_symmetry_broken'],
            'breaking_strength': sym_break_results['symmetry_breaking_strength']
        },
        'timing': {
            'duration_seconds': duration
        }
    }
    
    return results


def run_convergence_study():
    """Badanie zbieżności dla różnych rozmiarów sieci."""
    print("\n" + "=" * 60)
    print("BADANIE ZBIERNOŚCI")
    print("=" * 60 + "\n")
    
    results = []
    sizes = [20, 30, 50, 75, 100]
    
    for n in sizes:
        print(f"Symulacja dla N = {n}...")
        res = run_simulation(n_nodes=n, avg_degree=8, n_steps=200, verbose=False)
        results.append(res)
        print(f"  E_final = {res['energy']['final']:.6f}, "
              f"VEV = {res['symmetry']['vev']:.6f}")
    
    # Wykres zbieżności
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    ns = [r['configuration']['n_nodes'] for r in results]
    energies = [r['energy']['final'] for r in results]
    vevs = [r['symmetry']['vev'] for r in results]
    masses = [r['symmetry']['higgs_mass_estimate'] for r in results]
    
    axes[0].plot(ns, energies, 'bo-')
    axes[0].set_xlabel('Liczba węzłów')
    axes[0].set_ylabel('Energia końcowa')
    axes[0].set_title('Zbieżność energii')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(ns, vevs, 'ro-')
    axes[1].set_xlabel('Liczba węzłów')
    axes[1].set_ylabel('VEV Higgsa')
    axes[1].set_title('Zbieżność VEV')
    axes[1].grid(True, alpha=0.3)
    
    axes[2].plot(ns, masses, 'go-')
    axes[2].set_xlabel('Liczba węzłów')
    axes[2].set_ylabel('Szacunkowa masa Higgsa')
    axes[2].set_title('Zbieżność masy Higgsa')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('./shz_results/convergence_study.png', dpi=150)
    plt.close()
    
    print("\nWykres zbieżności zapisany w ./shz_results/convergence_study.png")


def main():
    """Główna funkcja programu."""
    parser = argparse.ArgumentParser(description='SHZ-U: Symulacja sieci horyzontów')
    parser.add_argument('--nodes', type=int, default=50, help='Liczba węzłów')
    parser.add_argument('--edges-per-node', type=float, default=8.0, 
                       help='Średni stopień węzła (k̄)')
    parser.add_argument('--steps', type=int, default=500, help='Liczba kroków')
    parser.add_argument('--seed', type=int, default=42, help='Seed losowy')
    parser.add_argument('--convergence', action='store_true', 
                       help='Uruchom badanie zbieżności')
    
    args = parser.parse_args()
    
    if args.convergence:
        run_convergence_study()
    else:
        results = run_simulation(
            n_nodes=args.nodes,
            avg_degree=args.edges_per_node,
            n_steps=args.steps,
            seed=args.seed
        )
        
        # Zapisz wyniki do JSON (konwersja numpy types i bools)
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(i) for i in obj]
            elif isinstance(obj, bool):
                return bool(obj)
            return obj
        
        with open('./shz_results/simulation_results.json', 'w') as f:
            json.dump(convert_numpy(results), f, indent=2)
        
        print(f"\nWyniki zapisane w ./shz_results/simulation_results.json")


if __name__ == '__main__':
    main()