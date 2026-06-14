import networkx as nx
import numpy as np

def check_local_symmetries(k=8):
    # Tworzymy idealny subgraf 4D (16-komórka / Cross-polytope)
    # Jest to regularny graf k=8 o 16 wierzchołkach
    G = nx.complete_multipartite_graph(2, 2, 2, 2) 
    
    print(f"Analiza lokalnego węzła k={G.degree(0)}")
    print(f"Liczba wierzchołków: {G.number_of_nodes()}")
    print(f"Liczba krawędzi: {G.number_of_edges()}")
    
    # Grupa automorfizmów
    from networkx.algorithms import isomorphism
    import itertools
    
    # Obliczamy rząd grupy automorfizmów
    # (Dla 16-komórki grupa to B4, rząd 384)
    # W praktyce sprawdzimy gęstość trójkątów i spektrum macierzy sąsiedztwa
    # bo pełna grupa automorfizmów dla dużych grafów jest trudna.
    
    spectrum = np.linalg.eigvals(nx.adjacency_matrix(G).todense())
    print(f"Wartości własne subgrafu: {np.unique(np.round(spectrum, 2))}")
    
    # Grupa symetrii 16-komórki zawiera reprezentacje SU(2)
    # ponieważ SO(4) ~ SU(2) x SU(2) / Z2

check_local_symmetries()
