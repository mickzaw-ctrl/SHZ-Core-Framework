import numpy as np
import matplotlib.pyplot as plt

def run_spectral_dimension_v2(n_vertices=1000, n_steps_mcmc=400000, beta=5.0, walk_steps=200):
    # 1. Generowanie stabilnej sieci SHZ (k=8)
    adj = np.zeros((n_vertices, n_vertices), dtype=float)
    degrees = np.zeros(n_vertices, dtype=int)
    
    # Inicjalizacja k=8
    for i in range(n_vertices):
        potential_targets = [j for j in range(n_vertices) if j > i]
        if potential_targets:
            targets = np.random.choice(potential_targets, 4, replace=False)
            for t in targets:
                adj[i, t] = adj[t, i] = 1
                degrees[i] += 1
                degrees[t] += 1

    energy_table = (np.arange(n_vertices + 20) - 8.0)**2
    for _ in range(n_steps_mcmc):
        u = np.random.randint(0, n_vertices)
        v = np.random.randint(0, n_vertices)
        if u == v: continue
        delta = -1 if adj[u, v] else 1
        # Ograniczenie stopnia do sensownych wartości
        if degrees[u] + delta < 0 or degrees[v] + delta < 0: continue
        
        de = (energy_table[degrees[u]+delta] + energy_table[degrees[v]+delta]) - \
             (energy_table[degrees[u]] + energy_table[degrees[v]])
        
        if de <= 0 or np.random.rand() < np.exp(-beta * de):
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = 1 - adj[u, v]
            degrees[u] += delta
            degrees[v] += delta

    # 2. Poprawna macierz przejścia błądzenia losowego (Column-stochastic)
    # P(next = i | current = j) = A_ij / deg_j
    M = np.zeros_like(adj)
    for j in range(n_vertices):
        if degrees[j] > 0:
            M[:, j] = adj[:, j] / degrees[j]

    # 3. Pomiary prawdopodobieństwa powrotu
    P_t = np.zeros(walk_steps)
    num_starts = 100
    start_nodes = np.random.choice(n_vertices, num_starts, replace=False)
    
    for start_node in start_nodes:
        v_t = np.zeros(n_vertices)
        v_t[start_node] = 1.0
        for t in range(walk_steps):
            v_t = M @ v_t # v_{t+1} = M * v_t
            P_t[t] += v_t[start_node]
            
    P_t /= num_starts
    
    # 4. Obliczanie d_s
    # Wybieramy zakres t, zanim P_t osiągnie 1/N (nasycenie)
    t_min, t_max = 15, 70
    t_axis = np.arange(1, walk_steps + 1)
    log_t = np.log(t_axis[t_min:t_max])
    log_P = np.log(P_t[t_min:t_max])
    
    slope, _ = np.polyfit(log_t, log_P, 1)
    d_s = -2 * slope
    
    return t_axis, P_t, d_s, degrees

print("Uruchamiam poprawioną analizę wymiarowości spektralnej (N=1000)...")
t, Pt, ds, final_degs = run_spectral_dimension_v2()

print(f"Średni stopień węzła: {np.mean(final_degs):.2f}")
print(f"Wyznaczony wymiar spektralny d_s: {ds:.3f}")

# Wykres
plt.figure(figsize=(12, 7))
plt.loglog(t, Pt, 'b-', label=f'SHZ-U Network (d_s ≈ {ds:.2f})')
plt.loglog(t[15:70], Pt[15] * (t[15:70]/t[15])**(-3/2), 'r--', label='Ideal 3D (slope -1.5)')
plt.loglog(t[15:70], Pt[15] * (t[15:70]/t[15])**(-4/2), 'g--', label='Ideal 4D (slope -2.0)')

plt.axhline(1/1000, color='black', linestyle=':', label='Próg nasycenia (1/N)')
plt.title("Analiza Wymiarowości Spektralnej Sieci SHZ-U")
plt.xlabel("Czas błądzenia log(t)")
plt.ylabel("Prawdopodobieństwo powrotu log(P(t))")
plt.legend()
plt.grid(True, which="both", alpha=0.3)
plt.savefig('spectral_dimension_v2.png')
print("Wyniki zapisane.")
