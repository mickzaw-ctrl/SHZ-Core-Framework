import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

def run_spectral_dimension_analysis(n_vertices=400, n_steps_mcmc=200000, beta=4.0, walk_steps=100):
    # 1. Generowanie stabilnej sieci SHZ (k=8)
    adj = np.zeros((n_vertices, n_vertices), dtype=int)
    degrees = np.zeros(n_vertices, dtype=int)
    
    # Inicjalizacja (każdy węzeł ma ok. 8 krawędzi)
    for i in range(n_vertices):
        potential_targets = [j for j in range(n_vertices) if j != i and adj[i,j] == 0]
        if len(potential_targets) > 0:
            targets = np.random.choice(potential_targets, min(len(potential_targets), 4), replace=False)
            for t in targets:
                adj[i, t] = adj[t, i] = 1
                degrees[i] += 1
                degrees[t] += 1

    energy_table = (np.arange(n_vertices) - 8.0)**2
    for _ in range(n_steps_mcmc):
        u, v = np.random.randint(0, n_vertices, 2)
        if u == v: continue
        delta = -1 if adj[u, v] else 1
        de = (energy_table[degrees[u]+delta] + energy_table[degrees[v]+delta]) - (energy_table[degrees[u]] + energy_table[degrees[v]])
        if de <= 0 or np.random.rand() < np.exp(-beta * de):
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = 1 - adj[u, v]
            degrees[u] += delta
            degrees[v] += delta

    # 2. Błądzenie losowe
    P_t = np.zeros(walk_steps)
    num_trials = 200 # Liczba startów błądzenia
    
    # Macierz przejścia M
    deg_inv = np.array([1.0/d if d > 0 else 0 for d in degrees])
    M = adj * deg_inv[:, np.newaxis] 

    for start_node in np.random.choice(n_vertices, num_trials, replace=False):
        v_t = np.zeros(n_vertices)
        v_t[start_node] = 1.0
        for t in range(walk_steps):
            v_t = M @ v_t
            P_t[t] += v_t[start_node]
            
    P_t /= num_trials
    
    # 3. Obliczanie ds = -2 * d(log P) / d(log t)
    t_axis = np.arange(1, walk_steps + 1)
    log_t = np.log(t_axis[10:60]) # Analiza środkowego zakresu (unikamy efektów skali atomowej i skończoności sieci)
    log_P = np.log(P_t[10:60])
    
    slope, intercept = np.polyfit(log_t, log_P, 1)
    d_s = -2 * slope
    
    return t_axis, P_t, d_s

print("Rozpoczynam analizę wymiarowości spektralnej (N=400)...")
t, Pt, ds_val = run_spectral_dimension_analysis()

print(f"Wyznaczony wymiar spektralny d_s: {ds_val:.3f}")

# Wykres
plt.figure(figsize=(10, 6))
plt.loglog(t, Pt, 'o-', label=f'Symulacja SHZ (d_s ≈ {ds_val:.2f})')
# Linia referencyjna dla d=3 (P ~ t^-1.5)
plt.loglog(t[10:60], Pt[10]* (t[10:60]/t[10])**(-1.5), '--', label='Referencja d=3 (slope -1.5)')
# Linia referencyjna dla d=4 (P ~ t^-2.0)
plt.loglog(t[10:60], Pt[10]* (t[10:60]/t[10])**(-2.0), '--', label='Referencja d=4 (slope -2.0)')

plt.title("Prawdopodobieństwo powrotu błądzenia losowego w sieci SHZ")
plt.xlabel("Krok czasu (t)")
plt.ylabel("P(t)")
plt.legend()
plt.grid(True, which="both", ls="-", alpha=0.5)
plt.savefig('spectral_dimension.png')
print("Wykres zapisany jako 'spectral_dimension.png'.")
