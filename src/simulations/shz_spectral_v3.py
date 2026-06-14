import numpy as np
import matplotlib.pyplot as plt

def run_spectral_dimension_v3(n_vertices=1000, n_steps_mcmc=500000, beta=6.0, walk_steps=200):
    adj = np.zeros((n_vertices, n_vertices), dtype=float)
    degrees = np.zeros(n_vertices, dtype=int)
    
    # Bezpieczna inicjalizacja (średnio k=8)
    for i in range(n_vertices):
        needed = 4 - degrees[i]
        if needed > 0:
            potential = [j for j in range(i+1, n_vertices) if adj[i,j] == 0]
            if potential:
                targets = np.random.choice(potential, min(len(potential), needed), replace=False)
                for t in targets:
                    adj[i, t] = adj[t, i] = 1
                    degrees[i] += 1
                    degrees[t] += 1

    energy_table = (np.arange(n_vertices + 100) - 8.0)**2
    
    # MCMC do stabilizacji próżni
    for _ in range(n_steps_mcmc):
        u, v = np.random.randint(0, n_vertices, 2)
        if u == v: continue
        delta = -1 if adj[u, v] else 1
        if degrees[u] + delta < 0 or degrees[v] + delta < 0: continue
        
        de = (energy_table[degrees[u]+delta] + energy_table[degrees[v]+delta]) - \
             (energy_table[degrees[u]] + energy_table[degrees[v]])
        
        if de <= 0 or np.random.rand() < np.exp(-beta * de):
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = 1 - adj[u, v]
            degrees[u] += delta
            degrees[v] += delta

    # Macierz przejścia (Column-stochastic)
    M = np.zeros_like(adj)
    for j in range(n_vertices):
        if degrees[j] > 0:
            M[:, j] = adj[:, j] / degrees[j]

    # Błądzenie losowe
    P_t = np.zeros(walk_steps)
    num_starts = 150
    start_nodes = np.random.choice(n_vertices, num_starts, replace=False)
    
    for start_node in start_nodes:
        v_t = np.zeros(n_vertices)
        v_t[start_node] = 1.0
        for t in range(walk_steps):
            v_t = M @ v_t 
            P_t[t] += v_t[start_node]
            
    P_t /= num_starts
    
    # Analiza ds (zakres gdzie sieć nie jest jeszcze nasycona)
    t_min, t_max = 20, 80
    t_axis = np.arange(1, walk_steps + 1)
    log_t = np.log(t_axis[t_min:t_max])
    log_P = np.log(P_t[t_min:t_max])
    
    slope, _ = np.polyfit(log_t, log_P, 1)
    d_s = -2 * slope
    
    return t_axis, P_t, d_s, degrees

print("Analiza SHZ-U: Wymiar spektralny (N=1000)...")
t, Pt, ds, final_degs = run_spectral_dimension_v3()

print(f"Średni stopień: {np.mean(final_degs):.3f}")
print(f"Wyznaczony wymiar spektralny d_s: {ds:.4f}")

plt.figure(figsize=(10, 6))
plt.loglog(t, Pt, 'k-', label=f'Symulacja SHZ (d_s ≈ {ds:.2f})')
plt.loglog(t[20:80], Pt[20] * (t[20:80]/t[20])**(-3/2), 'r--', alpha=0.6, label='Skalowanie 3D')
plt.loglog(t[20:80], Pt[20] * (t[20:80]/t[20])**(-4/2), 'g--', alpha=0.6, label='Skalowanie 4D')
plt.title(f"P(t) powrotu - Wymiar Spektralny d_s = {ds:.3f}")
plt.xlabel("Krok t")
plt.ylabel("P(t)")
plt.legend()
plt.grid(True, which="both", alpha=0.2)
plt.savefig('spectral_dimension_final.png')
