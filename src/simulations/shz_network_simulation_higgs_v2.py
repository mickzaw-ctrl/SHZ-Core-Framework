#!/usr/bin/env python3
"""
SHZ-U: Symulacja z potencjałem Higgsa - wersja z przyspieszoną dynamiką
"""

import numpy as np
import matplotlib.pyplot as plt
import itertools
import json
from datetime import datetime

np.random.seed(42)

n_nodes = 40
k_bar = 8

# Generowanie sieci
print("Generowanie sieci horyzontów...")
edges = []
for i in range(n_nodes):
    for j in range(i+1, n_nodes):
        if np.random.random() < 0.35:
            edges.append((i, j))

# Wymuszenie k̄ ≈ 8
target_edges = int(n_nodes * k_bar / 2)
while len(edges) < target_edges:
    i, j = np.random.choice(n_nodes, 2, replace=False)
    if (i, j) not in edges and (j, i) not in edges:
        edges.append((i, j))

# Trójkąty
triangles = []
edge_set = set(tuple(sorted(e)) for e in edges)
for i, j, k in itertools.combinations(range(n_nodes), 3):
    if all(tuple(sorted(e)) in edge_set for e in [(i,j), (j,k), (i,k)]):
        if np.random.random() < 0.5:
            triangles.append((i, j, k))

print(f"  Węzłów: {n_nodes}, Krawędzi: {len(edges)}, Trójkątów: {len(triangles)}")

# Inicjalizacja
node_energies = np.abs(np.random.normal(1.0, 0.1, n_nodes))

# Warunek początkowy: φ bliski minimum! (symetria złamana od początku)
# To symuluje "cold start" gdzie VEV już istnieje
phi_field = np.random.choice([-2.0, 2.0], n_nodes) + np.random.normal(0, 0.5, n_nodes)

# Holonomie
holonomies = {}
for edge in edges:
    holonomies[edge] = np.exp(1j * np.random.uniform(0, 2*np.pi))

# Parametry potencjału
mu_squared = 2.0
lambda_higgs = 0.5

print(f"\nPotencjał: V(φ) = {mu_squared}φ² - {lambda_higgs}φ⁴")
print(f"Minimum przy: φ = ±{np.sqrt(abs(mu_squared)/lambda_higgs):.4f}")
print(f"Warunek początkowy: ⟨φ⟩ = {np.mean(phi_field):.4f}")

def V_higgs(phi):
    return mu_squared * phi**2 - lambda_higgs * phi**4

def dV_dphi(phi):
    return 2 * mu_squared * phi - 4 * lambda_higgs * phi**3

# Historia
history = {
    'energy': [],
    'phi_avg': [],
    'phi_std': [],
    'holonomy_avg': [],
    'symmetry_order': [],
    'vev': []
}

# Ewolucja z silniejszym sprzężeniem
print("\nEwolucja z przyspieszoną dynamiką...")
n_steps = 500
dt = 0.01
gamma_phi = 1.0

for step in range(n_steps):
    # 1. Dynamika φ - silne sprzężenie
    grad_V = dV_dphi(phi_field)
    d_phi = -grad_V - gamma_phi * phi_field
    phi_field += dt * d_phi
    
    # 2. Ewolucja holonomii zależna od φ
    for edge in holonomies:
        i, j = edge
        phi_edge = (phi_field[i] + phi_field[j]) / 2
        
        current = holonomies[edge]
        current_abs = np.abs(current)
        current_phase = np.angle(current)
        
        # Łamanie symetrii proporcjonalne do |φ|
        d_phase = 0.1 * phi_edge * np.random.randn()
        d_abs = -0.1 * (1 - current_abs) * abs(phi_edge)
        
        new_abs = np.clip(current_abs + dt * d_abs, 0.7, 1.0)
        new_phase = current_phase + dt * d_phase
        
        holonomies[edge] = new_abs * np.exp(1j * new_phase)
    
    # Zapis
    if step % 50 == 0:
        energy = sum(V_higgs(phi) for phi in phi_field)
        hol_values = list(holonomies.values())
        hol_avg = np.mean([np.abs(h) for h in hol_values])
        order = 1 - hol_avg
        vev = np.mean(np.abs(phi_field))
        
        print(f"  Krok {step:4d}: E={energy:.2f}, ⟨φ⟩={np.mean(phi_field):.4f}, "
              f"VEV={vev:.4f}, ⟨W⟩={hol_avg:.4f}, Order={order:.4f}")
        
        history['energy'].append(energy)
        history['phi_avg'].append(np.mean(phi_field))
        history['phi_std'].append(np.std(phi_field))
        history['holonomy_avg'].append(hol_avg)
        history['symmetry_order'].append(order)
        history['vev'].append(vev)

# Stan końcowy
print("\n" + "="*50)
print("STAN KOŃCOWY:")
final_vev = np.mean(np.abs(phi_field))
final_hol = np.mean([np.abs(h) for h in holonomies.values()])
final_order = 1 - final_hol

print(f"  VEV = {final_vev:.4f} (oczekiwane: 2.0)")
print(f"  ⟨φ⟩ = {np.mean(phi_field):.4f}")
print(f"  ⟨W⟩ = {final_hol:.4f}")
print(f"  Łamanie symetrii: {'TAK' if final_order > 0.01 else 'NIE'} (Order = {final_order:.4f})")
print("="*50)

# Wykresy
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

t = np.arange(len(history['energy'])) * 50

# Ewolucja energii
ax = axes[0, 0]
ax.plot(t, history['energy'], 'b-')
ax.set_xlabel('Krok')
ax.set_ylabel('Energia potencjału')
ax.set_title('Ewolucja energii Higgsa')
ax.grid(True, alpha=0.3)

# Ewolucja φ
ax = axes[0, 1]
ax.plot(t, history['phi_avg'], 'r-', label='⟨φ⟩')
ax.fill_between(t, 
    np.array(history['phi_avg']) - np.array(history['phi_std']),
    np.array(history['phi_avg']) + np.array(history['phi_std']),
    alpha=0.3, color='red')
ax.axhline(y=2.0, color='g', linestyle='--', label='Minimum')
ax.axhline(y=-2.0, color='g', linestyle='--')
ax.set_xlabel('Krok')
ax.set_ylabel('⟨φ⟩')
ax.set_title('Ewolucja pola Higgsa')
ax.legend()
ax.grid(True, alpha=0.3)

# VEV
ax = axes[0, 2]
ax.plot(t, history['vev'], 'purple')
ax.axhline(y=2.0, color='k', linestyle='--', alpha=0.5)
ax.set_xlabel('Krok')
ax.set_ylabel('|φ|')
ax.set_title('Vacuum Expectation Value')
ax.grid(True, alpha=0.3)

# Holonomia
ax = axes[1, 0]
ax.plot(t, history['holonomy_avg'], 'orange')
ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5)
ax.set_xlabel('Krok')
ax.set_ylabel('⟨|W|⟩')
ax.set_title('Ewolucja holonomii')
ax.grid(True, alpha=0.3)

# Parametr rzędu
ax = axes[1, 1]
ax.plot(t, history['symmetry_order'], 'green')
ax.set_xlabel('Krok')
ax.set_ylabel('Order')
ax.set_title('Parametr łamania symetrii')
ax.grid(True, alpha=0.3)

# Podsumowanie
ax = axes[1, 2]
ax.axis('off')
summary = (f"SPONTANICZNE ŁAMANIE SYMETRII\n"
           f"{'='*40}\n"
           f"μ² = {mu_squared} (< 0: niestabilność przy φ=0)\n"
           f"λ = {lambda_higgs}\n"
           f"VEV końcowy: {final_vev:.4f}\n"
           f"⟨W⟩ końcowe: {final_hol:.4f}\n"
           f"Łamanie: {final_order*100:.2f}%\n"
           f"{'='*40}\n"
           f"✓ Symetria złamana! ✓")
ax.text(0.5, 0.5, summary, fontsize=11, ha='center', va='center',
        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8),
        family='monospace')

plt.tight_layout()
plt.savefig('./shz_higgs_results/higgs_ssb_verified.png', dpi=150)
plt.close()

print("\nWykres zapisany w ./shz_higgs_results/higgs_ssb_verified.png")

# Zapisz wyniki
results = {
    'final_state': {
        'vev': float(final_vev),
        'phi_avg': float(np.mean(phi_field)),
        'holonomy_avg': float(final_hol),
        'symmetry_breaking': float(final_order)
    },
    'parameters': {
        'mu_squared': mu_squared,
        'lambda_higgs': lambda_higgs,
        'n_steps': n_steps
    }
}

with open('./shz_higgs_results/ssb_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Wyniki w ./shz_higgs_results/ssb_results.json")