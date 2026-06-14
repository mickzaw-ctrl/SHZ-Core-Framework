import numpy as np
import matplotlib.pyplot as plt

def run_shz_simulation(n_vertices=200, n_steps=100000, beta=3.0, k_initial=2.5, gamma=1.0):
    # Relational array architecture: use adjacency matrix for O(1) flips
    # and degree array for O(1) energy calculation.
    adj = np.zeros((n_vertices, n_vertices), dtype=int)
    degrees = np.zeros(n_vertices, dtype=int)
    
    # Initial Erdős-Rényi graph
    p = k_initial / (n_vertices - 1)
    for i in range(n_vertices):
        for j in range(i + 1, n_vertices):
            if np.random.rand() < p:
                adj[i, j] = adj[j, i] = 1
                degrees[i] += 1
                degrees[j] += 1
                
    # Global degree distribution histogram
    max_k = n_vertices
    histogram = np.zeros(max_k, dtype=int)
    for d in degrees:
        histogram[d] += 1
        
    avg_k_history = np.zeros(n_steps)
    
    # Precompute energy for efficiency
    # E(k) = gamma * (k - 8)^2
    # We use the positive form to ensure k=8 is the minimum (attractor)
    energy_table = gamma * (np.arange(max_k) - 8.0)**2

    for step in range(n_steps):
        # Pick two random vertices u, v
        u = np.random.randint(0, n_vertices)
        v = np.random.randint(0, n_vertices)
        while u == v:
            v = np.random.randint(0, n_vertices)
        
        # Determine if move is creation (delta=1) or annihilation (delta=-1)
        is_edge = adj[u, v]
        delta = -1 if is_edge else 1
        
        # Proposed new degrees
        ku_new = degrees[u] + delta
        kv_new = degrees[v] + delta
        
        # Constant time energy differential calculation O(1)
        # Delta E = E(ku_new) + E(kv_new) - [E(ku) + E(kv)]
        delta_e = (energy_table[ku_new] + energy_table[kv_new]) - \
                  (energy_table[degrees[u]] + energy_table[degrees[v]])
        
        # Metropolis-Hastings acceptance
        accept = False
        if delta_e <= 0:
            accept = True
        else:
            if np.random.rand() < np.exp(-beta * delta_e):
                accept = True
                
        if accept:
            # Update adjacency
            adj[u, v] = 1 - is_edge
            adj[v, u] = 1 - is_edge
            
            # Incremental histogram update O(1)
            histogram[degrees[u]] -= 1
            histogram[degrees[v]] -= 1
            
            # Update degrees
            degrees[u] = ku_new
            degrees[v] = kv_new
            
            histogram[degrees[u]] += 1
            histogram[degrees[v]] += 1
            
        avg_k_history[step] = np.mean(degrees)
            
    return degrees, histogram, avg_k_history

if __name__ == "__main__":
    # Parameters from LaTeX
    N = 200
    STEPS = 100000
    BETA = 3.0
    K_INIT = 2.5
    
    print(f"Starting SHZ-U simulation (N={N}, Steps={STEPS}, Beta={BETA})...")
    degrees, histogram, avg_k_history = run_shz_simulation(n_vertices=N, n_steps=STEPS, beta=BETA, k_initial=K_INIT)
    print("Simulation complete.")

    # Generate Figure
    plt.style.use('seaborn-v0_8-muted')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left panel: Final degree distribution histogram
    max_relevant_k = int(max(np.nonzero(histogram)[0]) + 2)
    ks = np.arange(max_relevant_k)
    ax1.bar(ks, histogram[:max_relevant_k], color='royalblue', alpha=0.7, edgecolor='black', label='Observed')
    ax1.axvline(8, color='crimson', linestyle='--', linewidth=2, label='k=8 Baseline')
    ax1.set_title('Final Degree Distribution')
    ax1.set_xlabel('Vertex Degree (k)')
    ax1.set_ylabel('Vertex Count $\mathcal{D}[k]$')
    ax1.set_xticks(range(0, max_relevant_k))
    ax1.legend()
    ax1.grid(axis='y', linestyle=':', alpha=0.6)

    # Right panel: Asymptotic convergence of average degree
    ax2.plot(avg_k_history, color='darkgreen', linewidth=1.5)
    ax2.axhline(8, color='crimson', linestyle='--', linewidth=2, label='Target <k>=8')
    ax2.set_title('Dynamical Convergence to Vacuum')
    ax2.set_xlabel('Simulation Step (Quantum Fluctuations)')
    ax2.set_ylabel('Average Degree $\langle k \\rangle$')
    ax2.set_ylim(2, 9)
    ax2.legend()
    ax2.grid(linestyle=':', alpha=0.6)

    plt.suptitle('Numerical Validation of the SHZ-U Framework', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('shz_results.png', dpi=300)
    print("Figure saved as 'shz_results.png'.")
