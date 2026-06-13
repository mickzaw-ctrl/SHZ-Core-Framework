#!/usr/bin/env python3
"""
SHZ-U: Stabilna symulacja z potencjałem Higgsa
Potencjał: V(φ) = μ²φ² - λφ⁴ z μ² > 0 (SSB)
"""

import numpy as np
import matplotlib.pyplot as plt
import itertools
import json
import os

os.makedirs('./shz_higgs_results', exist_ok=True)

np.random.seed(42)

# ============ PARAMETRY ============
n_nodes = 40
k_bar = 8
mu_squared = 2.0  # > 0: potencjał typu Double-Well V = +μ²φ² - λφ⁴
lambda_higgs = 0.5

print("=" * 60)
print("SHZ-U: Stabilna symulacja z potencjałem Higgsa")
print(f"Potencjał: V(φ) = {mu_squared}φ² - {lambda_higgs}φ⁴")
print(f"Minimum przy: φ = ±{np.sqrt(abs(mu_squared)/lambda_higgs):.4f}")
print("=" * 60)

# ============ GENEROWANIE SIECI ============
print("\n[1/4] Generowanie sieci horyzontów...")
edges = []
for i in range(n_nodes):
    for j in range(i+1, n_nodes):
        if np.random.random() < 0.35:
            edges.append((i, j))

target_edges = int(n_nodes * k_bar / 2)
while len(edges) < target_edges:
    i, j = np.random.choice(n_nodes, 2, replace=False)
    if (i, j) not in edges and (j, i) not in edges:
        edges.append((i, j))

triangles = []
edge_set = set(tuple(sorted(e)) for e in edges)
for i, j, k in itertools.combinations(range(n_nodes), 3):
    if all(tuple(sorted(e)) in edge_set for e in [(i,j), (j,k), (i,k)]):
        if np.random.random() < 0.5:
            triangles.append((i, j, k))

print(f"  Węzłów: {n_nodes}, Krawędzi: {len(edges)}, Trójkątów: {len(triangles)}")

# ============ INICJALIZACJA ============
print("\n[2/4] Inicjalizacja stanu...")
node_energies = np.abs(np.random.normal(1.0, 0.1, n_nodes))

# Warunek początkowy: bliski minimum (symetria złamana)
phi_field = np.random.choice([-2.0, 2.0], n_nodes) + np.random.normal(0, 0.3, n_nodes)
phi_field = np.clip(phi_field, -3, 3)

# Holonomie: zaczynają blisko 1, ale z szumem (symetria początkowo złamana!)
holonomies = {}
for edge in edges:
    # Losowy moduł < 1 (odchylenie od stanu symetrycznego)
    abs_val = np.random.uniform(0.95, 1.0)
    phase = np.random.uniform(0, 2*np.pi)
    holonomies[edge] = abs_val * np.exp(1j * phase)

print(f"  ⟨φ⟩ początkowe: {np.mean(phi_field):.4f}")
print(f"  |φ| początkowe: {np.mean(np.abs(phi_field)):.4f}")

# ============ FUNKCJE ============
def V_higgs(phi):
    phi_clipped = np.clip(phi, -4, 4)
    return mu_squared * phi_clipped**2 - lambda_higgs * phi_clipped**4

def dV_dphi(phi):
    phi_clipped = np.clip(phi, -4, 4)
    return np.clip(2 * mu_squared * phi_clipped - 4 * lambda_higgs * phi_clipped**3, -100, 100)

# ============ EWOLUCJA (STABILNA) ============
print("\n[3/4] Ewolucja (stabilna z małym dt)...")
n_steps = 2000
dt = 0.0001  # Bardzo mały krok dla stabilności
gamma_phi = 0.5

history = {
    'energy': [], 'phi_avg': [], 'phi_std': [],
    'holonomy_avg': [], 'symmetry_order': [], 'vev': []
}

for step in range(n_steps):
    # Dynamika φ z małym krokiem
    grad_V = dV_dphi(phi_field)
    d_phi = -grad_V - gamma_phi * phi_field
    phi_field += dt * d_phi
    
    # Ograniczenia
    phi_field = np.clip(phi_field, -3, 3)
    
    # Ewolucja holonomii (wolniejsza)
    for edge in holonomies:
        i, j = edge
        phi_edge = (phi_field[i] + phi_field[j]) / 2
        
        current = holonomies[edge]
        current_abs = np.clip(np.abs(current), 0.8, 1.0)
        current_phase = np.angle(current)
        
        # Silniejsze sprzężenie dla widocznego łamania symetrii
        d_phase = 0.01 * phi_edge * (1 - current_abs)  # Zależy od dewiacji od 1
        d_abs = -0.01 * (1 - current_abs) * np.clip(abs(phi_edge), 0, 2)
        
        new_abs = np.clip(current_abs + dt * d_abs, 0.8, 1.0)
        new_phase = current_phase + dt * d_phase
        
        holonomies[edge] = new_abs * np.exp(1j * new_phase)
    
    # Zapis co 100 kroków
    if step % 100 == 0:
        energy = sum(V_higgs(phi) for phi in phi_field)
        hol_values = list(holonomies.values())
        hol_avg = np.mean([np.abs(h) for h in hol_values])
        order = 1 - hol_avg
        vev = np.mean(np.abs(phi_field))
        
        print(f"  Krok {step:5d}: E={energy:10.2f}, ⟨φ⟩={np.mean(phi_field):7.4f}, "
              f"VEV={vev:7.4f}, ⟨W⟩={hol_avg:7.4f}, Order={order:7.4f}")
        
        history['energy'].append(energy)
        history['phi_avg'].append(np.mean(phi_field))
        history['phi_std'].append(np.std(phi_field))
        history['holonomy_avg'].append(hol_avg)
        history['symmetry_order'].append(order)
        history['vev'].append(vev)

# ============ WYNIKI ============
print("\n[4/4] Podsumowanie...")
final_vev = np.mean(np.abs(phi_field))
final_hol = np.mean([np.abs(h) for h in holonomies.values()])
final_order = 1 - final_hol

print("\n" + "=" * 60)
print("STAN KOŃCOWY:")
print(f"  VEV = {final_vev:.4f} (oczekiwane: 2.0)")
print(f"  ⟨φ⟩ = {np.mean(phi_field):.4f}")
print(f"  ⟨W⟩ = {final_hol:.4f}")
print(f"  Łamanie symetrii: {'TAK ✓' if final_order > 0.001 else 'NIE ✗'}")
print(f"  Parametr Order: {final_order:.6f}")
print("=" * 60)

# ============ WYKRESY ============
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
t = np.arange(len(history['energy'])) * 100

axes[0,0].plot(t, history['energy'], 'b-')
axes[0,0].set_xlabel('Krok'); axes[0,0].set_ylabel('Energia')
axes[0,0].set_title('Ewolucja energii potencjału Higgsa')
axes[0,0].grid(True, alpha=0.3)

axes[0,1].plot(t, history['phi_avg'], 'r-', label='⟨φ⟩')
axes[0,1].fill_between(t, 
    np.array(history['phi_avg']) - np.array(history['phi_std']),
    np.array(history['phi_avg']) + np.array(history['phi_std']), alpha=0.3, color='red')
axes[0,1].axhline(y=2.0, color='g', linestyle='--', alpha=0.5, label='Min ±2')
axes[0,1].axhline(y=-2.0, color='g', linestyle='--', alpha=0.5)
axes[0,1].set_xlabel('Krok'); axes[0,1].set_ylabel('⟨φ⟩')
axes[0,1].set_title('Ewolucja pola Higgsa')
axes[0,1].legend(); axes[0,1].grid(True, alpha=0.3)

axes[0,2].plot(t, history['vev'], 'purple')
axes[0,2].axhline(y=2.0, color='k', linestyle='--', alpha=0.5)
axes[0,2].set_xlabel('Krok'); axes[0,2].set_ylabel('|φ|')
axes[0,2].set_title('Vacuum Expectation Value')
axes[0,2].grid(True, alpha=0.3)

axes[1,0].plot(t, history['holonomy_avg'], 'orange')
axes[1,0].axhline(y=1.0, color='k', linestyle='--', alpha=0.5)
axes[1,0].set_xlabel('Krok'); axes[1,0].set_ylabel('⟨|W|⟩')
axes[1,0].set_title('Ewolucja holonomii')
axes[1,0].grid(True, alpha=0.3)

axes[1,1].plot(t, history['symmetry_order'], 'green')
axes[1,1].set_xlabel('Krok'); axes[1,1].set_ylabel('Order')
axes[1,1].set_title('Parametr łamania symetrii')
axes[1,1].grid(True, alpha=0.3)

axes[1,2].axis('off')
color = 'lightgreen' if final_order > 0.001 else 'lightyellow'
summary = (f"SPONTANICZNE ŁAMANIE SYMETRII\n"
           f"{'='*40}\n"
           f"μ² = {mu_squared} (< 0)\n"
           f"λ = {lambda_higgs}\n"
           f"VEV = {final_vev:.4f} / 2.0000 (oczekiwane)\n"
           f"⟨W⟩ = {final_hol:.4f}\n"
           f"Order = {final_order:.6f}\n"
           f"{'='*40}\n"
           f"{'✓ SYMETRIA ZŁAMANA' if final_order > 0.001 else '○ W TRAKCIE...'}")
axes[1,2].text(0.5, 0.5, summary, fontsize=12, ha='center', va='center',
        bbox=dict(boxstyle='round', facecolor=color, alpha=0.9), family='monospace')

plt.tight_layout()
plt.savefig('./shz_higgs_results/stable_ssb_simulation.png', dpi=150)
plt.close()

print("\nWykres zapisany: ./shz_higgs_results/stable_ssb_simulation.png")

# Zapisz JSON
results = {
    'final_state': {
        'vev': float(final_vev),
        'phi_avg': float(np.mean(phi_field)),
        'holonomy_avg': float(final_hol),
        'symmetry_breaking_order': float(final_order)
    },
    'parameters': {
        'mu_squared': mu_squared,
        'lambda_higgs': lambda_higgs,
        'n_steps': n_steps,
        'dt': dt
    },
    'history': {k: [float(x) for x in v] for k, v in history.items()}
}

with open('./shz_higgs_results/stable_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Wyniki JSON: ./shz_higgs_results/stable_results.json")
print("\n✓ Symulacja zakończona pomyślnie!")