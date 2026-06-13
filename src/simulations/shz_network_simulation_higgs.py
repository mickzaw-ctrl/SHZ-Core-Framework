#!/usr/bin/env python3
"""
SHZ-U: Symulacja numeryczna z potencjałem Higgsa
=================================================
Wersja z jawnym potencjałem V(φ) = μ²φ² - λφ⁴, μ² > 0
Prowadzi do spontanicznego łamania symetrii.

Użycie:
    python3 shz_network_simulation_higgs.py [--nodes N] [--mu2 MU2] [--lambda LAMBDA]
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import itertools
import argparse
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# STAŁE
# ============================================================
hbar = 1.0
omega_P = 1.0
k_bar = 8

class SimplicialComplex:
    """Kompleks symplicjalny sieci horyzontów."""
    
    def __init__(self, n_nodes, avg_degree=8, seed=None):
        self.n_nodes = n_nodes
        self.avg_degree = avg_degree
        self.seed = seed or np.random.randint(1e9)
        np.random.seed(self.seed)
        
        self.nodes = list(range(n_nodes))
        self.edges = []
        self.triangles = []
        
        # Stan sieci
        self.node_energies = np.zeros(n_nodes)
        self.phi_field = np.zeros(n_nodes)  # Pole Higgsa!
        self.holonomies = {}
        
        self._generate()
    
    def _generate(self):
        """Generuje sieć."""
        # Krawędzie
        target_edges = int(self.n_nodes * self.avg_degree / 2)
        for i in range(self.n_nodes):
            for j in range(i + 1, self.n_nodes):
                if np.random.random() < 0.35:
                    self.edges.append((i, j))
        
        while len(self.edges) < target_edges:
            i, j = np.random.choice(self.n_nodes, 2, replace=False)
            if (i, j) not in self.edges and (j, i) not in self.edges:
                self.edges.append((i, j))
        
        # Trójkąty
        edge_set = set(tuple(sorted(e)) for e in self.edges)
        for i, j, k in itertools.combinations(self.nodes, 3):
            if all(tuple(sorted(e)) in edge_set for e in [(i,j), (j,k), (i,k)]):
                if np.random.random() < 0.5:
                    self.triangles.append((i, j, k))
        
        # Inicjalizacja
        self.node_energies = np.abs(np.random.normal(1.0, 0.1, self.n_nodes))
        
        # Pole Higgsa: małe fluktuacje wokół zera (symetria!)
        self.phi_field = np.random.normal(0, 0.1, self.n_nodes)
        
        for edge in self.edges:
            phase = np.random.uniform(0, 2 * np.pi)
            self.holonomies[edge] = np.exp(1j * phase)
    
    def get_degree(self, node):
        return sum(1 for e in self.edges if node in e)


class SHZ_Hamiltonian_Higgs:
    """
    Hamiltonian SHZ-U z potencjałem Higgsa.
    H = H_kin + H_pot + H_hol + V_Higgs(φ)
    
    V_Higgs(φ) = μ²φ² - λφ⁴
    """
    
    def __init__(self, complex, mu_squared=2.0, lambda_higgs=0.5):
        self.complex = complex
        
        # Parametry potencjału Higgsa
        # UWAGA: μ² > 0 dla Double-Well V(φ) = +μ²φ² - λφ⁴
        # Minimum przy |φ| = √(μ²/λ)
        self.mu_squared = mu_squared  # > 0: spontaniczne łamanie!
        self.lambda_higgs = lambda_higgs
        
        self.hbar_omega0 = hbar * omega_P / 2
        self.k_bar_over_4 = k_bar / 4
    
    def V_higgs(self, phi):
        """Potencjał Higgsa: V = μ²φ² - λφ⁴"""
        return self.mu_squared * phi**2 - self.lambda_higgs * phi**4
    
    def dV_dphi(self, phi):
        """dV/dφ = 2μ²φ - 4λφ³"""
        return 2 * self.mu_squared * phi - 4 * self.lambda_higgs * phi**3
    
    def kinetic_term(self):
        """Człon kinetyczny."""
        H_kin = 0.0
        for edge in self.complex.edges:
            i, j = edge
            E_i = self.complex.node_energies[i]
            E_j = self.complex.node_energies[j]
            if E_i + E_j > 0:
                H_kin += self.hbar_omega0 * E_i * E_j / (E_i + E_j)
        return H_kin
    
    def potential_term(self):
        """Człon potencjałowy z kątów deficytu."""
        H_pot = 0.0
        for tri in self.complex.triangles:
            i, j, k = tri
            E_i = self.complex.node_energies[i]
            E_j = self.complex.node_energies[j]
            E_k = self.complex.node_energies[k]
            diff = E_i + E_j - E_k
            H_pot += self.k_bar_over_4 * diff**2
        return H_pot
    
    def holonomy_term(self):
        """Człon z holonomii (energia gdy holonomia ≠ 1)."""
        H_hol = 0.0
        for tri in self.complex.triangles:
            product = 1.0 + 0j
            for edge in tri:
                if edge in self.complex.holonomies:
                    product *= self.complex.holonomies[edge]
            H_hol += (1 - np.real(product))
        return H_hol
    
    def total_energy(self):
        """Całkowita energia z potencjałem Higgsa."""
        H_kin = self.kinetic_term()
        H_pot = self.potential_term()
        H_hol = self.holonomy_term()
        
        # Potencjał Higgsa sumowany po węzłach
        V_H = sum(self.V_higgs(phi) for phi in self.complex.phi_field)
        
        return H_kin + H_pot + H_hol + V_H
    
    def gradient_phi(self):
        """Gradient Hamiltonianu względem φ (dla dynamiki φ)."""
        grad = np.zeros(self.complex.n_nodes)
        
        for i in range(self.complex.n_nodes):
            # Potencjał Higgsa: dV/dφ
            grad[i] = self.dV_dphi(self.complex.phi_field[i])
        
        return grad
    
    def coupling_holonomy_phi(self):
        """
        Sprzężenie między polem φ a holonomią.
        Gdy φ ≠ 0, holonomie odchylają się od 1.
        """
        coupling = 0.0
        for tri in self.complex.triangles:
            for edge in tri:
                if edge in self.complex.holonomies:
                    # Siła proporcjonalna do |φ| na krawędzi
                    i, j = edge
                    phi_avg = (abs(self.complex.phi_field[i]) + 
                              abs(self.complex.phi_field[j])) / 2
                    # Gdy φ rośnie, holonomia zaczyna "dryfować"
                    coupling += phi_avg * (1 - np.abs(self.complex.holonomies[edge]))
        return coupling


class NetworkEvolutionHiggs:
    """
    Ewolucja sieci z potencjałem Higgsa.
    
    Dynamika:
    dφ/dt = -dV/dφ - γ_φ φ + (sprzężenie z holonomią)
    dU/dt = -(1 - |U|) + φ * (odchylenie od jedności)
    """
    
    def __init__(self, complex, hamiltonian, dt=0.001, gamma_phi=0.5):
        self.complex = complex
        self.H = hamiltonian
        self.dt = dt
        self.gamma_phi = gamma_phi  # Tłumienie dla φ
        
        self.history = {
            'energy': [],
            'phi_avg': [],
            'phi_std': [],
            'holonomy_avg': [],
            'symmetry_order': [],
            'vev': []
        }
        
        self.time = 0.0
    
    def step(self):
        """Jeden krok ewolucji."""
        n = self.complex.n_nodes
        
        # Zabezpieczenie przed niestabilnością
        if np.any(np.isnan(self.complex.phi_field)):
            return
        
        # 1. Dynamika pola φ z mniejszym krokiem i silniejszym tłumieniem
        # dφ/dt = -dV/dφ - γ_φ * φ + noise
        grad_V = self.H.gradient_phi()
        
        # Ogranicz gradient
        grad_V = np.clip(grad_V, -50, 50)
        
        d_phi = -grad_V - self.gamma_phi * self.complex.phi_field
        
        # Mały szum termiczny
        noise = np.random.normal(0, 0.001, n)
        
        # Mały krok czasowy dla stabilności
        self.complex.phi_field += 0.0001 * (d_phi + noise)
        
        # Ogranicz φ
        self.complex.phi_field = np.clip(self.complex.phi_field, -5, 5)
        
        # 2. Ewolucja holonomii zależna od φ (wolniejsza, stabilna)
        dt_hol = 0.0001
        for edge, hol in self.complex.holonomies.items():
            i, j = edge
            
            # Średnie pole na krawędzi
            phi_edge = (self.complex.phi_field[i] + self.complex.phi_field[j]) / 2
            
            current_abs = np.abs(hol)
            current_phase = np.angle(hol)
            
            # Zmiana fazy zależna od φ (mniejsza dla stabilności)
            d_phase = 0.001 * phi_edge
            
            # Zmiana modułu (odchylenie od 1)
            d_abs = 0.001 * (abs(phi_edge) - (1 - current_abs))
            
            # Aktualizacja
            new_abs = current_abs + dt_hol * d_abs
            new_phase = current_phase + dt_hol * d_phase
            
            # Ogranicz do [0.8, 1.0]
            new_abs = max(0.8, min(1.0, new_abs))
            
            self.complex.holonomies[edge] = new_abs * np.exp(1j * new_phase)
        
        # 3. Ewolucja energii węzłów (bardzo wolna)
        alpha = 0.01
        for i in range(n):
            phi_i = self.complex.phi_field[i]
            dE = -0.001 * self.complex.node_energies[i] * (1 + alpha * phi_i**2)
            self.complex.node_energies[i] += dE * dt_hol
        
        self.time += self.dt
        
        # Zapis historii
        self._record_history()
    
    def _record_history(self):
        """Zapisuje chwilowe wartości."""
        self.history['energy'].append(self.H.total_energy())
        
        phi = self.complex.phi_field
        self.history['phi_avg'].append(np.mean(phi))
        self.history['phi_std'].append(np.std(phi))
        
        # Średnia holonomia
        hol_values = list(self.complex.holonomies.values())
        self.history['holonomy_avg'].append(np.mean([np.abs(h) for h in hol_values]))
        
        # Parametr rzędu symetrii (odchylenie holonomii od 1)
        order_param = 1 - np.mean([np.abs(h) for h in hol_values])
        self.history['symmetry_order'].append(order_param)
        
        # VEV = średnia wartość bezwzględna φ
        self.history['vev'].append(np.mean(np.abs(phi)))
    
    def run(self, n_steps, verbose=True):
        """Uruchamia symulację."""
        if verbose:
            print(f"Rozpoczynam symulację z potencjałem Higgsa")
            print(f"  μ² = {self.H.mu_squared} (< 0: SSB!)")
            print(f"  λ = {self.H.lambda_higgs}")
            print(f"  VEV oczekiwany = √(|μ²|/λ) = {np.sqrt(abs(self.H.mu_squared)/self.H.lambda_higgs):.4f}")
            print()
        
        for step in range(n_steps):
            self.step()
            
            if verbose and step % max(1, n_steps // 10) == 0:
                e = self.history['energy'][-1]
                phi = self.history['phi_avg'][-1]
                vev = self.history['vev'][-1]
                order = self.history['symmetry_order'][-1]
                hol = self.history['holonomy_avg'][-1]
                print(f"  Krok {step:5d}: E={e:.4f}, ⟨φ⟩={phi:.4f}, "
                      f"VEV={vev:.4f}, ⟨W⟩={hol:.4f}, Order={order:.4f}")
        
        if verbose:
            print()
            print("=" * 50)
            print("STAN KOŃCOWY:")
            print(f"  VEV = {self.history['vev'][-1]:.6f}")
            print(f"  ⟨φ⟩ = {self.history['phi_avg'][-1]:.6f}")
            print(f"  ⟨W⟩ = {self.history['holonomy_avg'][-1]:.6f}")
            print(f"  Łamanie symetrii: {'TAK' if self.history['symmetry_order'][-1] > 0.01 else 'NIE'}")
            print("=" * 50)
        
        return self.history


def plot_higgs_results(history, save_dir='./shz_higgs_results'):
    """Generuje wykresy dla symulacji z Higgsem."""
    import os
    os.makedirs(save_dir, exist_ok=True)
    
    n_steps = len(history['energy'])
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    t = np.arange(n_steps)
    
    # 1. Ewolucja energii
    ax = axes[0, 0]
    ax.plot(t, history['energy'], 'b-', linewidth=1)
    ax.set_xlabel('Krok')
    ax.set_ylabel('Energia')
    ax.set_title('Ewolucja energii całkowitej')
    ax.grid(True, alpha=0.3)
    
    # 2. Pole φ (średnie)
    ax = axes[0, 1]
    ax.plot(t, history['phi_avg'], 'r-', linewidth=1, label='⟨φ⟩')
    ax.fill_between(t, 
                    np.array(history['phi_avg']) - np.array(history['phi_std']),
                    np.array(history['phi_avg']) + np.array(history['phi_std']),
                    alpha=0.3, color='red', label='±σ')
    ax.axhline(y=np.sqrt(2), color='g', linestyle='--', label='VEV oczekiwany')
    ax.set_xlabel('Krok')
    ax.set_ylabel('⟨φ⟩')
    ax.set_title('Ewolucja pola Higgsa')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. VEV
    ax = axes[0, 2]
    ax.plot(t, history['vev'], 'purple', linewidth=1)
    ax.set_xlabel('Krok')
    ax.set_ylabel('VEV')
    ax.set_title('Vacuum Expectation Value |φ|')
    ax.grid(True, alpha=0.3)
    
    # 4. Holonomia
    ax = axes[1, 0]
    ax.plot(t, history['holonomy_avg'], 'orange', linewidth=1)
    ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='Stan symetryczny')
    ax.set_xlabel('Krok')
    ax.set_ylabel('⟨|W|⟩')
    ax.set_title('Ewolucja holonomii')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 5. Parametr rzędu symetrii
    ax = axes[1, 1]
    ax.plot(t, history['symmetry_order'], 'green', linewidth=1)
    ax.set_xlabel('Krok')
    ax.set_ylabel('Order')
    ax.set_title('Parametr łamania symetrii (1 - ⟨|W|⟩)')
    ax.grid(True, alpha=0.3)
    
    # 6. Podsumowanie
    ax = axes[1, 2]
    ax.axis('off')
    
    summary = (
        f"PODSUMOWANIE SYMULACJI\n"
        f"{'='*30}\n"
        f"VEV końcowy: {history['vev'][-1]:.4f}\n"
        f"Oczekiwany: √(2) ≈ 1.414\n"
        f"{'='*30}\n"
        f"⟨W⟩ końcowe: {history['holonomy_avg'][-1]:.4f}\n"
        f"Łamanie symetrii: {history['symmetry_order'][-1]:.4f}\n"
        f"{'='*30}\n"
    )
    ax.text(0.5, 0.5, summary, fontsize=11, 
            ha='center', va='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            family='monospace')
    
    plt.tight_layout()
    plt.savefig(f'{save_dir}/higgs_simulation_results.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\nWykresy zapisane w {save_dir}/")


def main():
    parser = argparse.ArgumentParser(description='SHZ-U z potencjałem Higgsa')
    parser.add_argument('--nodes', type=int, default=40, help='Liczba węzłów')
    parser.add_argument('--mu2', type=float, default=-2.0, help='μ² (ujemne!)')
    parser.add_argument('--lambda', type=float, dest='lam', default=0.5, help='λ')
    parser.add_argument('--steps', type=int, default=1000, help='Liczba kroków')
    parser.add_argument('--seed', type=int, default=42, help='Seed')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SHZ-U: Symulacja z potencjałem Higgsa")
    print(f"  μ² = {args.mu2}, λ = {args.lam}")
    print("=" * 60)
    print()
    
    start = datetime.now()
    
    # Generowanie sieci
    print("[1/4] Generowanie sieci horyzontów...")
    complex = SimplicialComplex(args.nodes, avg_degree=8, seed=args.seed)
    print(f"  Węzłów: {complex.n_nodes}, Krawędzi: {len(complex.edges)}, Trójkątów: {len(complex.triangles)}")
    print()
    
    # Hamiltonian
    print("[2/4] Inicjalizacja Hamiltonianu SHZ-U z potencjałem Higgsa...")
    H = SHZ_Hamiltonian_Higgs(complex, mu_squared=args.mu2, lambda_higgs=args.lam)
    print(f"  μ² = {H.mu_squared}")
    print(f"  λ = {H.lambda_higgs}")
    print(f"  Minimum potencjału przy: φ = ±{np.sqrt(abs(H.mu_squared)/H.lambda_higgs):.4f}")
    print()
    
    # Ewolucja
    print("[3/4] Uruchamianie ewolucji...")
    evolution = NetworkEvolutionHiggs(complex, H, dt=0.001, gamma_phi=0.5)
    history = evolution.run(args.steps, verbose=True)
    print()
    
    # Wizualizacja
    print("[4/4] Generowanie wykresów...")
    plot_higgs_results(history)
    print()
    
    end = datetime.now()
    print(f"Czas wykonania: {(end - start).total_seconds():.2f} s")
    
    # Zapisz wyniki
    results = {
        'configuration': {
            'n_nodes': args.nodes,
            'mu_squared': args.mu2,
            'lambda_higgs': args.lam,
            'n_steps': args.steps,
            'seed': args.seed
        },
        'final_state': {
            'vev': float(history['vev'][-1]),
            'phi_avg': float(history['phi_avg'][-1]),
            'phi_std': float(history['phi_std'][-1]),
            'holonomy_avg': float(history['holonomy_avg'][-1]),
            'symmetry_breaking': float(history['symmetry_order'][-1]),
            'energy': float(history['energy'][-1])
        },
        'expected': {
            'vev': np.sqrt(abs(args.mu2) / args.lam)
        }
    }
    
    with open('./shz_higgs_results/results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("Wyniki zapisane w ./shz_higgs_results/results.json")


if __name__ == '__main__':
    main()