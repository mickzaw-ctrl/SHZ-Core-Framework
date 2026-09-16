import os
import jax
import jax.numpy as jnp

os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"

N_NODES = 5_000_000
K_ATTRACTOR = 8.0
GAMMA_IMMIRZI = 0.2739
N_S = 0.9648
H11_GENERATIONS = 3.0
DILUTION_FACTOR = 20000.0

# Nowy, niezależny czynnik z SU(3)xSU(2)xU(1): konwersja B-L -> B przez sfalerony EW
A_SPH = 28.0 / 79.0  # standardowy wynik podręcznikowy dla SM (3 generacje, 1 Higgs)

CP_VIOLATION_PHASE = (GAMMA_IMMIRZI ** 3) * (1.0 - N_S) / (K_ATTRACTOR * H11_GENERATIONS)

@jax.jit
def baryogenesis_v3(key, phase, a_sph):
    state = jax.random.normal(key, (N_NODES,))
    decay_matter = jnp.exp(phase / 2.0)
    decay_anti = jnp.exp(-phase / 2.0)
    topological_bias = (decay_matter - decay_anti) / (decay_matter + decay_anti)
    eta_BL_equivalent = topological_bias / DILUTION_FACTOR   # traktowane jako n_(B-L)/s
    eta_B_final = eta_BL_equivalent * a_sph                   # konwersja sfaleronowa
    return eta_BL_equivalent, eta_B_final

key = jax.random.PRNGKey(108)
_ = baryogenesis_v3(key, CP_VIOLATION_PHASE, A_SPH)
eta_BL, eta_B_final = baryogenesis_v3(key, CP_VIOLATION_PHASE, A_SPH)
eta_B_final.block_until_ready()

target = 6.11e-10
ratio = float(eta_B_final) / target

print("="*62)
print(" SHZ-U: BARYOGENEZA v3 - z czynnikiem sfaleronowym SU(3)x SU(2)xU(1) ")
print("="*62)
print(f"[+] eta_(B-L) [z v2, przed konwersją] = {float(eta_BL):.4e}")
print(f"[+] a_sph (28/79, konwersja EW)       = {A_SPH:.4f}")
print(f"[+] eta_B finalne (po konwersji)      = {float(eta_B_final):.4e}")
print(f"[+] Wartość z predykcji CMB-S4        = {target:.4e}")
print(f"[+] Współczynnik rozbieżności          = {ratio:.2f}x")
print("="*62)
