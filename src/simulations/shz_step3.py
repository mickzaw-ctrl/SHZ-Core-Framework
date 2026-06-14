import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

def run_locality_simulation(n_vertices=300, n_steps=300000, beta=4.0, alpha=2.0, gamma=1.0):
    # Inicjalizacja
    adj = np.zeros((n_vertices, n_vertices), dtype=int)
    degrees = np.zeros(n_vertices, dtype=int)
    
    # Start z rzadkiej sieci
    for i in range(n_vertices):
        targets = np.random.choice([j for j in range(n_vertices) if j != i], 2, replace=False)
        for t in targets:
            if adj[i, t] == 0:
                adj[i, t] = adj[t, i] = 1
                degrees[i] += 1
                degrees[t] += 1

    energy_history = []
    
    for step in range(n_steps):
        u, v = np.random.randint(0, n_vertices, 2)
        if u == v: continue
        
        is_edge = adj[u, v]
        delta = -1 if is_edge else 1
        
        # 1. Zmiana energii stopnia (Aksjomat SHZ)
        de_shz = gamma * ((degrees[u] + delta - 8)**2 + (degrees[v] + delta - 8)**2 - \
                         (degrees[u] - 8)**2 - (degrees[v] - 8)**2)
        
        # 2. Zmiana energii lokalności (Liczba trójkątów)
        # Wspólni sąsiedzi u i v to wierzchołki w, dla których adj[u,w] i adj[v,w] są 1
        common_neighbors = np.sum(adj[u] * adj[v])
        de_locality = -alpha * delta * common_neighbors
        
        total_de = de_shz + de_locality
        
        if total_de <= 0 or np.random.rand() < np.exp(-beta * total_de):
            adj[u, v] = 1 - is_edge
            adj[v, u] = 1 - is_edge
            degrees[u] += delta
            degrees[v] += delta
            
        if step % 1000 == 0:
            energy_history.append(total_de)

    # Obliczanie wymiaru spektralnego na koniec
    M = np.zeros_like(adj, dtype=float)
    for j in range(n_vertices):
        if degrees[j] > 0:
            M[:, j] = adj[:, j] / degrees[j]
    
    walk_steps = 100
    P_t = np.zeros(walk_steps)
    for start_node in np.random.choice(n_vertices, 50, replace=False):
        v_t = np.zeros(n_vertices)
        v_t[start_node] = 1.0
        for t in range(walk_steps):
            v_t = M @ v_t
            P_t[t] += v_t[start_node]
    P_t /= 50
    
    log_t = np.log(np.arange(1, walk_steps+1)[15:60])
    log_P = np.log(P_t[15:60])
    slope, _ = np.polyfit(log_t, log_P, 1)
    d_s = -2 * slope
    
    return d_s, adj, degrees

# Skanowanie parametru alfa
alphas = [0.0, 0.5, 1.0, 2.0, 4.0]
results_ds = []

print("Skanowanie parametru lokalności alfa...")
for a in alphas:
    ds, _, degs = run_locality_simulation(alpha=a)
    results_ds.append(ds)
    print(f"Alfa: {a:.1f} | d_s: {ds:.3f} | Średni k: {np.mean(degs):.2f}")

plt.figure(figsize=(10, 6))
plt.plot(alphas, results_ds, 'ro-', linewidth=2)
plt.axhline(4, color='green', linestyle='--', label='Wymiar 4D')
plt.axhline(3, color='blue', linestyle='--', label='Wymiar 3D')
plt.title("Przejście Fazowe: Od Chaosu (Expander) do Geometrii")
plt.xlabel("Siła Lokalności (alfa)")
plt.ylabel("Wymiar Spektralny (d_s)")
plt.legend()
plt.grid(True)
plt.savefig('shz_phase_transition.png')
