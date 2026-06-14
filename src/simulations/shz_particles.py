import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

def run_particle_physics_sim(n_vertices=200, beta=6.0, alpha=1.2, n_steps=100000):
    # Inicjalizacja próżni k=8
    adj = np.zeros((n_vertices, n_vertices), dtype=int)
    degrees = np.zeros(n_vertices, dtype=int)
    
    # Budowa idealnej próżni (uproszczona)
    for i in range(n_vertices):
        for _ in range(4):
            t = np.random.randint(0, n_vertices)
            if i != t and adj[i, t] == 0:
                adj[i, t] = adj[t, i] = 1
                degrees[i] += 1
                degrees[t] += 1

    # Wstrzyknięcie pary: Cząstka (k=9) i Antycząstka (k=7)
    p_pos = 10  # Pozyton candidate
    p_neg = 50  # Elektron candidate
    
    # Ręczna modyfikacja stopni (wymuszamy defekt)
    # Dla p_pos dodajemy krawędź, dla p_neg usuwamy
    target_pos = np.random.choice(np.where(adj[p_pos]==0)[0])
    adj[p_pos, target_pos] = adj[target_pos, p_pos] = 1
    
    # Symulacja z obserwacją "ładunku"
    charge_history = [] # Będziemy mierzyć sumaryczne odchylenie |k-8|
    dist_history = []
    
    energy_table = (np.arange(n_vertices + 10) - 8.0)**2

    for step in range(n_steps):
        u, v = np.random.randint(0, n_vertices, 2)
        if u == v: continue
        
        delta = -1 if adj[u, v] else 1
        de = (energy_table[degrees[u]+delta] + energy_table[degrees[v]+delta]) - \
             (energy_table[degrees[u]] + energy_table[degrees[v]])
        
        # Uwzględnienie lokalności
        common = np.sum(adj[u] * adj[v])
        de -= alpha * delta * common
        
        if de <= 0 or np.random.rand() < np.exp(-beta * de):
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = 1 - adj[u, v]
            degrees[u] += delta
            degrees[v] += delta
            
        if step % 500 == 0:
            # Liczymy "ilość materii" w systemie
            total_matter = np.sum(np.abs(degrees - 8))
            charge_history.append(total_matter)
            
            # Odległość między pierwotnymi defektami (jeśli przeżyły)
            G = nx.from_numpy_array(adj)
            try:
                d = nx.shortest_path_length(G, p_pos, p_neg)
                dist_history.append(d)
            except:
                dist_history.append(0)

    return charge_history, dist_history

print("Symulacja mikroświata SHZ-U: Anihilacja i Ładunek...")
charge, dist = run_particle_physics_sim()

fig, ax1 = plt.subplots(figsize=(10, 6))

ax1.set_xlabel('Czas (kroki)')
ax1.set_ylabel('Całkowita Materia (Suma |k-8|)', color='red')
ax1.plot(charge, color='red', label='Materia')
ax1.tick_params(axis='y', labelcolor='red')

ax2 = ax1.twinx()
ax2.set_ylabel('Dystans Cząstka-Antycząstka', color='blue')
ax2.plot(dist, color='blue', alpha=0.3, label='Dystans')
ax2.tick_params(axis='y', labelcolor='blue')

plt.title("Dynamika Cząstek w SHZ-U: Procesy Kreacji i Anihilacji")
plt.savefig('shz_particle_physics.png')
print("Wyniki zapisane.")
