import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

def run_defect_analysis(n_vertices=150, n_steps=150000, beta=4.0, gamma=1.0):
    # Inicjalizacja
    adj = np.zeros((n_vertices, n_vertices), dtype=int)
    degrees = np.zeros(n_vertices, dtype=int)
    
    # Start z k=8 (idealna próżnia) lub losowy. 
    # Aby zbadać powstawanie defektów, zacznijmy od stanu bliskiego próżni.
    for i in range(n_vertices):
        targets = np.random.choice([j for j in range(n_vertices) if j != i], 4, replace=False)
        for t in targets:
            if adj[i, t] == 0:
                adj[i, t] = adj[t, i] = 1
                degrees[i] += 1
                degrees[t] += 1

    energy_table = gamma * (np.arange(n_vertices) - 8.0)**2

    # Symulacja relaksacji
    for step in range(n_steps):
        u, v = np.random.randint(0, n_vertices, 2)
        if u == v: continue
        
        delta = -1 if adj[u, v] else 1
        delta_e = (energy_table[degrees[u] + delta] + energy_table[degrees[v] + delta]) - \
                  (energy_table[degrees[u]] + energy_table[degrees[v]])
        
        if delta_e <= 0 or np.random.rand() < np.exp(-beta * delta_e):
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = 1 - adj[u, v]
            degrees[u] += delta
            degrees[v] += delta

    # Analiza końcowa
    defect_nodes = np.where(degrees != 8)[0]
    num_defects = len(defect_nodes)
    
    # Tworzenie obiektu NetworkX do obliczeń odległości
    G = nx.from_numpy_array(adj)
    
    if num_defects > 1:
        # Obliczanie średniej odległości między defektami
        distances = []
        for i in range(len(defect_nodes)):
            for j in range(i + 1, len(defect_nodes)):
                try:
                    d = nx.shortest_path_length(G, defect_nodes[i], defect_nodes[j])
                    distances.append(d)
                except nx.NetworkXNoPath:
                    continue
        
        avg_defect_dist = np.mean(distances) if distances else 0
        
        # Średnia odległość między losowymi węzłami (tło)
        all_nodes = list(G.nodes())
        random_nodes = np.random.choice(all_nodes, min(num_defects, 50), replace=False)
        random_distances = []
        for i in range(len(random_nodes)):
            for j in range(i + 1, len(random_nodes)):
                try:
                    d = nx.shortest_path_length(G, random_nodes[i], random_nodes[j])
                    random_distances.append(d)
                except nx.NetworkXNoPath:
                    continue
        avg_random_dist = np.mean(random_distances) if random_distances else 0
    else:
        avg_defect_dist, avg_random_dist = 0, 0

    return degrees, defect_nodes, avg_defect_dist, avg_random_dist, adj

# Uruchomienie analizy
N = 150
deg, defects, d_def, d_rand, final_adj = run_defect_analysis(n_vertices=N)

print(f"Liczba wierzchołków: {N}")
print(f"Liczba defektów (k!=8): {len(defects)} ({(len(defects)/N)*100:.1f}%)")
print(f"Średnia odległość między defektami: {d_def:.2f}")
print(f"Średnia odległość między losowymi węzłami: {d_rand:.2f}")

# Wizualizacja defektów
G_final = nx.from_numpy_array(final_adj)
pos = nx.spring_layout(G_final, k=0.15)

plt.figure(figsize=(10, 8))
node_colors = []
node_sizes = []
for i in range(N):
    if deg[i] == 8:
        node_colors.append('lightgrey')
        node_sizes.append(30)
    elif deg[i] > 8:
        node_colors.append('red') # Materia (nadmiar połączeń)
        node_sizes.append(100)
    else:
        node_colors.append('blue') # Antymateria/Luka (niedobór połączeń)
        node_sizes.append(100)

nx.draw_networkx_nodes(G_final, pos, node_color=node_colors, node_size=node_sizes, alpha=0.8)
nx.draw_networkx_edges(G_final, pos, alpha=0.1)
plt.title("Mapa Defektów Topologicznych w Próżni SHZ (Czerwony: k>8, Niebieski: k<8)")
plt.savefig('shz_defects.png')
print("Mapa defektów zapisana jako 'shz_defects.png'.")
