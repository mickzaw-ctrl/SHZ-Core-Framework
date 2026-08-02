# Snowmass 2750334 and PBMZ Gauge-Matching Audit

**Audit date:** 2026-08-02  
**Target documentation repository:** `mickzaw-ctrl/SHZ-Core-Framework`  
**Status:** Software validation passed; precision-complete MSSM matching remains incomplete  
**Confidence:** High for the one-loop coefficients and finite scheme conversion; low for any claim of complete PBMZ matching

## Executive conclusions

1. **Snowmass 2013 pMSSM-19 model 2750334 remains the primary reproducibility benchmark.** MasterCode pMSSM11 is retained only as an independent cross-check and must not replace the production benchmark without a separate owner decision.
2. The implemented spectrum treatment must be labelled exactly as:

   > **two-loop step RGE with one-loop spectrum-resolved leading-log threshold corrections.**

3. The finite one-loop regularization-scheme conversion at the matching scale is required:

   $$
   \alpha_{i,\overline{\mathrm{DR}}}^{-1}
   =
   \alpha_{i,\overline{\mathrm{MS}}}^{-1}
   -\frac{C_A(G_i)}{12\pi},
   \qquad C_A=(0,2,3),
   $$

   giving

   $$
   \Delta\alpha_i^{-1}
   =
   \left(0,-\frac{2}{12\pi},-\frac{3}{12\pi}\right)
   =
   (0,-0.05305165,-0.07957747).
   $$

4. Complete Pierce-Bagger-Matchev-Zhang observable matching is **not implemented** and must not be claimed. Adding isolated finite terms to the existing $\overline{\mathrm{MS}}$ input triplet would risk double counting.
5. Two-loop particle-by-particle decoupling is deferred until scheme control, mixing-aware parsing, spectrum covariance, baseline comparisons, and a compute/rollback plan are documented.

## Established physics

The one-loop difference between the MSSM and Standard Model gauge beta-function coefficients, with GUT-normalized hypercharge, is

$$
\Delta b
=
b^{\mathrm{MSSM}}-b^{\mathrm{SM}}
=
\left(\frac{5}{2},\frac{25}{6},4\right).
$$

The decomposition into the wino, gluino, higgsinos, heavy Higgs doublet, and three generations of $Q,U,D,L,E$ multiplets reproduces this coefficient exactly.

The universal $\overline{\mathrm{MS}}\rightarrow\overline{\mathrm{DR}}$ inverse-coupling shift is negative for the non-Abelian groups and zero for GUT-normalized $U(1)_Y$. Consequently, $\alpha_{2,3}^{\overline{\mathrm{DR}}}>\alpha_{2,3}^{\overline{\mathrm{MS}}}$ at the same scale to this order.

**Primary references:**

- D. M. Pierce, J. A. Bagger, K. T. Matchev, R.-J. Zhang, *Precision Corrections in the Minimal Supersymmetric Standard Model*, arXiv:`hep-ph/9606211`, DOI: `10.1016/S0550-3213(96)00683-9`, especially the gauge-unification section and Appendix C.
- M. Cahill-Rowley et al., *pMSSM Benchmark Models for Snowmass 2013*, arXiv:`1305.2419`, SLAC-PUB-15458.
- B. C. Allanach, *SOFTSUSY: a program for calculating supersymmetric spectra*, arXiv:`hep-ph/0104145`, DOI: `10.1016/S0010-4655(01)00460-9`.

## Project implementation validated by the audit

The audited implementation combines:

- a two-loop one-step SM/MSSM RGE trajectory;
- one-loop spectrum-resolved leading-log threshold corrections;
- the universal finite $\overline{\mathrm{MS}}\rightarrow\overline{\mathrm{DR}}$ conversion;
- a non-probabilistic matching-scale sensitivity envelope;
- propagated uncertainty from the pinned electroweak input covariance scenario.

The Snowmass spectrum was reproduced with SOFTSUSY 3.1.7. Its immutable provenance is:

| Item | SHA-256 |
|---|---|
| SOFTSUSY 3.1.7 source | `db2be9448b1bbbe61e54d81c226e82f9ad5e6f27793c08d269377c812cb69e11` |
| Snowmass input | `cd272c9c04d5aee8b830ccc5b069309de17c80410541c07264c2878f293fb0e9` |
| Generated SLHA output | `a72e4d43c71c7abb7cf0aa9936a7ea50dfd60c3df473202fa4a3245e287a679f` |

## Numerical result at the BCC scale

For

$$
M_{\mathrm{BCC}}=5\times10^{15}\ \mathrm{GeV},
$$

the audited inverse couplings are

$$
\alpha_1^{-1}=26.22290129\pm0.00544595,
$$

$$
\alpha_2^{-1}=25.40703687\pm0.00606329,
$$

$$
\alpha_3^{-1}=25.04950735\pm0.06532586.
$$

The uncertainty values above are propagated input sensitivities, not complete theory uncertainties.

The separate corrections at $M_{\mathrm{BCC}}$ are:

| Contribution | $\Delta\alpha_1^{-1}$ | $\Delta\alpha_2^{-1}$ | $\Delta\alpha_3^{-1}$ |
|---|---:|---:|---:|
| Spectrum-resolved leading logarithms | 0.04037059 | 0.23499564 | 0.39334012 |
| Finite scheme conversion | 0.00000000 | -0.05305165 | -0.07957747 |
| Total implemented one-loop matching correction | 0.04037059 | 0.18194399 | 0.31376265 |

The residual matching-scale envelope is

| Coupling | Envelope at $M_{\mathrm{BCC}}$ |
|---|---:|
| $\alpha_1^{-1}$ | [26.20049717, 26.24336281] |
| $\alpha_2^{-1}$ | [25.36915583, 25.44199214] |
| $\alpha_3^{-1}$ | [25.00371734, 25.09186100] |

This envelope is a factor-two scale-variation sensitivity scan, **not** a probability distribution or confidence interval.

## Regression evidence

The latest audit reported:

- RGE and matching regression tests: **14/14 PASS**;
- numerical scientific-contract tests: **6/6 PASS**;
- executable script smoke tests: **14/14 PASS**;
- generated PNG integrity checks: **13/13 PASS**;
- source provenance checks: **15/15 PASS**;
- full evaluator: **48 PASS, 0 FAIL, 9 INCONCLUSIVE, 4 NOT TESTABLE**;
- overall software status: **PASS**;
- overall scientific status: **INCONCLUSIVE**.

The added regression gates cover:

1. exact reproduction of $\Delta b_i$;
2. continuity of the leading-log corrections at each spectrum threshold;
3. cancellation of arbitrary one-loop matching-reference-scale dependence;
4. exact signs and magnitudes of the $\overline{\mathrm{MS}}/\overline{\mathrm{DR}}$ conversion;
5. prohibition of the label `full two-loop matching` for the current implementation.

## PBMZ scope limitation

The Snowmass SLHA contains the standard `NMIX`, `UMIX`, `VMIX`, `STOPMIX`, `SBOTMIX`, and `STAUMIX` blocks. However, the current minimal parser does not expose two-index mixing entries, and the RGE boundary condition is already expressed through an $\overline{\mathrm{MS}}$ input triplet.

A complete PBMZ extraction of $\overline{\mathrm{DR}}$ $g_1$ and $g_2$ requires a separately validated observable-basis implementation containing:

- $W$, $Z$, and mixed gauge-boson self-energies at the required momenta;
- non-universal vertex and box contributions;
- mixing-dependent chargino, neutralino, and sfermion couplings;
- Passarino-Veltman functions at non-zero momentum;
- electroweak observables and an iterative solution for $\hat\alpha$, $\hat s^2$, $\Delta\hat r$, and $\Delta\hat\rho$;
- explicit controls preventing double counting against the current $\overline{\mathrm{MS}}$ inputs.

Therefore, the complete PBMZ status is:

> **INCOMPLETE — not implemented in the production RGE path.**

## Assumption ledger

| Assumption | Classification | Impact |
|---|---|---|
| One-loop MSSM-minus-SM coefficients use GUT-normalized hypercharge | Established physics | Fixes the exact $\Delta b_i$ decomposition |
| Universal finite scheme conversion uses $C_A=(0,2,3)$ | Established physics | Shifts $\alpha_{2,3}^{-1}$ by fixed negative constants |
| Snowmass 2750334 is the primary benchmark | Project decision | Preserves historical reproducibility; it is not a current global best fit |
| pMSSM11 is cross-check-only | Project decision | Prevents an unreviewed production benchmark migration |
| DRbar `MSOFT/HMIX` parameters approximate multiplet threshold masses | Project approximation | Limits the result to leading-log spectrum treatment |
| Zero off-diagonal electroweak covariance entries define a sensitivity scenario | Unverified assumption | Input bands are not a measured joint confidence region |
| Complete PBMZ finite observable terms can be omitted from the current baseline | Controlled incompleteness | Prevents double counting but blocks precision-complete matching claims |

## Required next work

1. Build a separate mixing-aware SLHA parser and observable-basis PBMZ module.
2. Validate loop functions and gauge self-energies against an approved independent implementation such as a pinned SOFTSUSY calculation.
3. Add gold-standard tests for $g_1$, $g_2$, and $g_3$ matching before connecting the module to the production trajectory.
4. Add spectrum-parameter covariance and propagate it separately from the non-probabilistic matching-scale envelope.
5. Consider two-loop particle-by-particle decoupling only after the one-loop PBMZ module passes independent validation.

## Final status

**Software conclusion:** PASS for the implemented two-loop step RGE, one-loop spectrum-resolved leading logarithms, and finite $\overline{\mathrm{MS}}\rightarrow\overline{\mathrm{DR}}$ conversion.

**Scientific conclusion:** The result is suitable as a controlled Snowmass 2750334 reproducibility calculation, but it is not a precision-complete MSSM matching calculation. Any stronger claim remains unsupported until the complete PBMZ observable module and higher-order decoupling are implemented and validated.
