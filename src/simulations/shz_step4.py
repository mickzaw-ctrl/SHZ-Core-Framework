import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

def run_propagation_study(n_vertices=400, alpha=1.2, beta=4.0, n_burnin=100000, n_obs=50000):
    # 1. Generowanie stabilnego tła
    adj = np.zeros((n_vertices, n_vertices), dtype=int)
    degrees = np.zeros(n_vertices, dtype=int)
    
    # Inicjalizacja
    for i in range(n_vertices):
        targets = np.random.choice([j for j in range(n_vertices) if j != i], 4, replace=False)
        for t in targets:
            if adj[i, t] == 0:
                adj[i, t] = adj[t, i] = 1
                degrees[i] += 1
                degrees[t] += 1

    def get_de(u, v, delta, adj, degrees):
        de_shz = ((degrees[u] + delta - 8)**2 + (degrees[v] + delta - 8)**2 - \
                 (degrees[u] - 8)**2 - (degrees[v] - 8)**2)
        common = np.sum(adj[u] * adj[v])
        de_loc = -alpha * delta * common
        return de_shz + de_loc

    # Relaksacja do próżni
    for _ in range(n_burnin):
        u, v = np.random.randint(0, n_vertices, 2)
        if u == v: continue
        delta = -1 if adj[u, v] else 1
        de = get_de(u, v, delta, adj, degrees)
        if de <= 0 or np.random.rand() < np.exp(-beta * de):
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = 1 - adj[u, v]
            degrees[u] += delta
            degrees[v] += delta

    # 2. Iniekcja zaburzenia (Kick)
    source_node = 0
    # Wymuszamy duży defekt w punkcie 0
    potential_neighbors = np.where(adj[source_node] == 0)[0]
    kick_size = 10
    targets = np.random.choice(potential_neighbors, kick_size, replace=False)
    for t in targets:
        adj[source_node, t] = adj[t, source_node] = 1
        degrees[source_node] += 1
        degrees[t] += 1

    # Obliczamy dystanse grafowe od źródła
    G = nx.from_numpy_array(adj)
    distances = nx.single_source_shortest_path_length(G, source_node)
    
    # 3. Obserwacja propagacji
    max_dist = 5
    propagation_data = {d: [] for d in range(max_dist + 1)}
    
    for step in range(n_obs):
        u, v = np.random.randint(0, n_vertices, 2)
        if u == v: continue
        delta = -1 if adj[u, v] else 1
        de = get_de(u, v, delta, adj, degrees)
        if de <= 0 or np.random.rand() < np.exp(-beta * de):
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = 1 - adj[u, v]
            degrees[u] += delta
            degrees[v] += delta
            
        if step % 500 == 0:
            # Mierzymy średnie odchylenie od próżni na każdym dystansie
            for d in range(max_dist + 1):
                nodes_at_d = [n for n, dist in distances.items() if dist == d]
                if nodes_at_d:
                    avg_excess = np.mean([abs(degrees[n] - 8) for n in nodes_at_d])
                    propagation_data[d].append(avg_excess)

    return propagation_data

print("Rozpoczynam badanie propagacji fali w sieci SHZ-L...")
data = run_propagation_study()

plt.figure(figsize=(12, 7))
for d, values in data.items():
    plt.plot(values, label=f'Dystans r={d}')

plt.title("Relaksacja i Propagacja Zaburzenia Topologicznego")
plt.xlabel("Czas symulacji (kroki MCMC / 500)")
plt.ylabel("Zaburzenie średniego stopnia |k - 8|")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('shz_propagation.png')
print("Wynik zapisany w 'shz_propagation.png'.")
