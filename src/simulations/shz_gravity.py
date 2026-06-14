import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

def run_gravity_simulation(n_vertices=300, alpha=1.2, beta=5.0, n_steps=200000):
    adj = np.zeros((n_vertices, n_vertices), dtype=int)
    degrees = np.zeros(n_vertices, dtype=int)
    
    # Inicjalizacja stabilnej próżni
    for i in range(n_vertices):
        targets = np.random.choice([j for j in range(n_vertices) if j != i], 4, replace=False)
        for t in targets:
            if adj[i, t] == 0:
                adj[i, t] = adj[t, i] = 1
                degrees[i] += 1
                degrees[t] += 1

    def get_energy(u, v, delta, adj, degrees):
        de_shz = ((degrees[u] + delta - 8)**2 + (degrees[v] + delta - 8)**2 - \
                 (degrees[u] - 8)**2 - (degrees[v] - 8)**2)
        common = np.sum(adj[u] * adj[v])
        return de_shz - alpha * delta * common

    # 1. Tworzymy dwa stabilne "źródła masy" (wierzchołki 0 i 100)
    # Będziemy śledzić odległość między nimi
    m1, m2 = 0, 100
    
    # Relaksacja tła
    dist_history = []
    
    for step in range(n_steps):
        u, v = np.random.randint(0, n_vertices, 2)
        if u == v: continue
        
        # "Masy" są trudniejsze do usunięcia (imitacja cząstek)
        delta = -1 if adj[u, v] else 1
        de = get_energy(u, v, delta, adj, degrees)
        
        # Modyfikacja potencjału dla mas: dążą do k=12 (nadmiar energii)
        if u in [m1, m2] or v in [m1, m2]:
            # Dodatkowy potencjał utrzymujący masę
            target_k = 14
            de_mass = (degrees[u]+delta-target_k)**2 - (degrees[u]-target_k)**2 if u in [m1, m2] else 0
            de_mass += (degrees[v]+delta-target_k)**2 - (degrees[v]-target_k)**2 if v in [m1, m2] else 0
            de += de_mass

        if de <= 0 or np.random.rand() < np.exp(-beta * de):
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = 1 - adj[u, v]
            degrees[u] += delta
            degrees[v] += delta
            
        if step % 1000 == 0:
            # Obliczamy najkrótszą ścieżkę między masami
            G = nx.from_numpy_array(adj)
            try:
                d = nx.shortest_path_length(G, m1, m2)
                dist_history.append(d)
            except nx.NetworkXNoPath:
                dist_history.append(10) # Max dystans dla braku ścieżki

    return dist_history

print("Symulacja oddziaływania mas w sieci SHZ-U...")
history = run_gravity_simulation()

plt.figure(figsize=(10, 6))
plt.plot(history, color='purple', alpha=0.6, label='Dystans grafowy między defektami')
plt.plot(np.convolve(history, np.ones(20)/20, mode='valid'), color='black', linewidth=2, label='Średnia krocząca')
plt.title("Prymordialna Grawitacja: Przyciąganie Defektów Topologicznych")
plt.xlabel("Czas (kroki MCMC / 1000)")
plt.ylabel("Odległość d(m1, m2)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('shz_gravity.png')
print("Wynik zapisany.")
