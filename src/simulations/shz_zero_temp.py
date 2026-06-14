import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

def run_zero_temp_limit(n_vertices=200, alpha=1.5, n_steps=300000):
    # Startujemy z losowej sieci, ale beta jest ogromna (limit zero-temp)
    adj = np.zeros((n_vertices, n_vertices), dtype=int)
    degrees = np.zeros(n_vertices, dtype=int)
    
    # Inicjalizacja rzadka
    for i in range(n_vertices):
        t = np.random.randint(0, n_vertices)
        if t != i:
            adj[i, t] = adj[t, i] = 1
            degrees[i] = np.sum(adj[i])
            degrees[t] = np.sum(adj[t])

    # Funkcja energii (SHZ-L)
    def energy_node(i, adj, degrees):
        # E = gamma*(k-8)^2 - alpha*Triangles
        shz = (degrees[i] - 8)**2
        # Trójkąty w których uczestniczy węzeł i
        tri = 0
        neighbors = np.where(adj[i] == 1)[0]
        for idx_a in range(len(neighbors)):
            for idx_b in range(idx_a + 1, len(neighbors)):
                if adj[neighbors[idx_a], neighbors[idx_b]] == 1:
                    tri += 1
        return shz - alpha * tri

    # Optymalizacja "Greedy" (Beta -> Inf)
    for step in range(n_steps):
        u, v = np.random.randint(0, n_vertices, 2)
        if u == v: continue
        
        # Oblicz energię przed zmianą
        e_before = energy_node(u, adj, degrees) + energy_node(v, adj, degrees)
        
        # Zmiana
        is_edge = adj[u, v]
        delta = -1 if is_edge else 1
        adj[u, v] = adj[v, u] = 1 - is_edge
        degrees[u] += delta
        degrees[v] += delta
        
        # Oblicz energię po zmianie
        e_after = energy_node(u, adj, degrees) + energy_node(v, adj, degrees)
        
        # Akceptuj TYLKO jeśli energia spada (Beta -> Inf)
        if e_after >= e_before:
            # Cofnij zmianę
            adj[u, v] = adj[v, u] = is_edge
            degrees[u] -= delta
            degrees[v] -= delta

    return adj, degrees

print("Poszukiwanie stanu podstawowego sieci (Beta -> Inf)...")
final_adj, final_degs = run_zero_temp_limit()

print(f"Średni stopień w stanie podstawowym: {np.mean(final_degs):.2f}")

# Wizualizacja "Kryształu"
G = nx.from_numpy_array(final_adj)
plt.figure(figsize=(10, 10))
pos = nx.kamada_kawai_layout(G)
nx.draw_networkx_nodes(G, pos, node_size=50, node_color=final_degs, cmap=plt.cm.plasma)
nx.draw_networkx_edges(G, pos, alpha=0.3)
plt.title("Kryształ Topologiczny SHZ-U (Stan podstawowy w T=0)")
plt.savefig('shz_ground_state.png')
print("Zapisano stan podstawowy.")
