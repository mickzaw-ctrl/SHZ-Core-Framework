import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import time

# =====================================================================
# 1. WARSTWA HOLOGRAFICZNEJ UWAGI (SHZ-BCC Z_2^3)
# =====================================================================

class BCCMultiHeadAttentionOptimized(nn.Module):
    def __init__(self, embed_dim: int, num_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.dropout_p = dropout

        self.qkv_proj = nn.Linear(embed_dim, 3 * embed_dim)
        self.out_proj = nn.Linear(embed_dim, embed_dim)

        parity = torch.ones(1, 1, 1, self.head_dim)
        parity[..., self.head_dim // 2:] = -1.0
        self.register_buffer('parity_mask', parity)

    def forward(self, x, attn_mask=None):
        B, S, E = x.size()

        qkv = self.qkv_proj(x)
        q, k, v = qkv.split(self.embed_dim, dim=2)

        q = q.view(B, S, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, S, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, S, self.num_heads, self.head_dim).transpose(1, 2)

        v_parity = v * self.parity_mask

        output_singlet = torch.zeros_like(q)
        dropout_p = self.dropout_p if self.training else 0.0

        for i_s in [False, True]:
            for i_n in [False, True]:
                for i_p in [False, True]:
                    q_curr = torch.flip(q, dims=[2]) if i_s else q
                    k_curr = torch.flip(k, dims=[2]) if i_s else k
                    v_curr = torch.flip(v_parity if i_p else v, dims=[2]) if i_s else (v_parity if i_p else v)

                    curr_mask = attn_mask
                    if i_s and attn_mask is not None:
                        curr_mask = torch.flip(attn_mask, dims=[-2, -1])

                    q_final, k_final = (k_curr, q_curr) if i_n else (q_curr, k_curr)
                    mask_final = curr_mask.transpose(-2, -1) if (i_n and curr_mask is not None) else curr_mask

                    attn_out = F.scaled_dot_product_attention(
                        q_final, k_final, v_curr,
                        attn_mask=mask_final,
                        dropout_p=dropout_p
                    )

                    if i_s:
                        attn_out = torch.flip(attn_out, dims=[2])
                    if i_p:
                        attn_out = attn_out * self.parity_mask

                    output_singlet += attn_out

        output_singlet = output_singlet / 8.0
        out = output_singlet.transpose(1, 2).contiguous().view(B, S, E)
        return self.out_proj(out)


# =====================================================================
# 2. BLOK TRANSFORMERA (PRE-LN AXIS)
# =====================================================================

class BCCTransformerBlock(nn.Module):
    def __init__(self, embed_dim: int, num_heads: int = 8):
        super().__init__()
        self.ln1 = nn.LayerNorm(embed_dim)
        self.attn = BCCMultiHeadAttentionOptimized(embed_dim, num_heads)
        self.ln2 = nn.LayerNorm(embed_dim)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, 4 * embed_dim),
            nn.GELU(),
            nn.Linear(4 * embed_dim, embed_dim)
        )

    def forward(self, x, attn_mask=None):
        x = x + self.attn(self.ln1(x), attn_mask=attn_mask)
        x = x + self.mlp(self.ln2(x))
        return x


# =====================================================================
# 3. ADAPTIVE SELF-IMPROVING MODEL
# =====================================================================

class AdaptiveBCCModel(nn.Module):
    def __init__(self, vocab_size: int, embed_dim: int, num_heads: int, num_layers: int):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)

        self.layers = nn.ModuleList([
            BCCTransformerBlock(embed_dim, num_heads) for _ in range(num_layers)
        ])
        self.ln_f = nn.LayerNorm(embed_dim)
        self.lm_head = nn.Linear(embed_dim, vocab_size)
        self.critic_head = nn.Linear(embed_dim, 1)

        self.base_lr = 5e-4

    def forward_pass(self, tokens, mask=None):
        x = self.token_embedding(tokens)
        for layer in self.layers:
            x = layer(x, attn_mask=mask)
        x = self.ln_f(x)
        logits = self.lm_head(x)
        critic_score = self.critic_head(x)
        return logits, critic_score, x

    def adaptive_step(self, tokens, target_tokens, mask=None):
        self.train()

        logits, critic_score, _ = self.forward_pass(tokens, mask)
        loss_ce = F.cross_entropy(logits.view(-1, logits.size(-1)), target_tokens.view(-1))

        critic_prob = torch.sigmoid(critic_score)
        mean_confidence = critic_prob.mean()

        # === ADAPTIVE LEARNING RATE ===
        conf = mean_confidence.item()

        if conf < 0.52:
            # STAN NIESTABILNY — pełny LR + penalty
            lr_multiplier = 1.0
            penalty = 1.0 - conf
            mode = "🔥 AGRESYWNE UCZENIE"
            status_symbol = "🔴"

        elif conf < 0.75:
            # STAN PRZEJŚCIOWY — zredukowany LR
            lr_multiplier = 0.1
            penalty = 0.0
            mode = "🟡 KONSERWATYWNE UCZENIE"
            status_symbol = "🟡"

        else:
            # STAN STABILNY — minimalny LR (utrzymanie)
            lr_multiplier = 0.01
            penalty = 0.0
            mode = "🟢 DEGRADACJA / KONSERWACJA"
            status_symbol = "🟢"

        # Optymalizator z adaptacyjnym LR
        optimizer = optim.AdamW(self.parameters(), lr=self.base_lr * lr_multiplier)
        optimizer.zero_grad()

        total_loss = loss_ce + penalty
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=1.0)
        optimizer.step()

        return {
            'loss': loss_ce.item(),
            'confidence': conf,
            'lr_multiplier': lr_multiplier,
            'mode': mode,
            'status': status_symbol,
            'penalty': penalty
        }


# =====================================================================
# 4. MAIN
# =====================================================================

if __name__ == "__main__":
    torch.manual_seed(1337)

    vocab_size = 1000
    embed_dim = 128
    num_heads = 4
    num_layers = 2
    seq_len = 16
    batch_size = 4

    model = AdaptiveBCCModel(vocab_size, embed_dim, num_heads, num_layers)

    input_tokens = torch.randint(0, vocab_size, (batch_size, seq_len))
    target_tokens = torch.randint(0, vocab_size, (batch_size, seq_len))
    causal_mask = torch.tril(torch.ones(seq_len, seq_len, dtype=torch.bool))

    print("=" * 65)
    print("   ADAPTIVE LEARNING RATE — SHZ-BCC MODEL")
    print("   Progi: 🔴 <0.52 | 🟡 0.52-0.75 | 🟢 ≥0.75")
    print("=" * 65)

    results = []

    for epoch in range(1, 21):
        start = time.time()

        result = model.adaptive_step(
            tokens=input_tokens,
            target_tokens=target_tokens,
            mask=causal_mask
        )

        elapsed = (time.time() - start) * 1000
        results.append(result)

        print(f"[{epoch:02d}] Strata: {result['loss']:.4f} | "
              f"Pewność: {result['confidence']:.4f} | "
              f"LR×{result['lr_multiplier']:.2f} | "
              f"{result['status']} {result['mode']} | "
              f"{elapsed:.1f}ms")

    # === STATYSTYKI ===
    print("\n" + "=" * 65)
    print("   PODSUMOWANIE STATYSTYCZNE")
    print("=" * 65)

    confidences = [r['confidence'] for r in results]
    losses = [r['loss'] for r in results]

    print(f"   Strata końcowa:    {losses[-1]:.4f} (start: {losses[0]:.4f})")
    print(f"   Pewność końcowa:  {confidences[-1]:.4f} (start: {confidences[0]:.4f})")
    print(f"   Poprawa straty:   {(losses[0] - losses[-1]):.4f}")

    modes = [r['mode'] for r in results]
    print(f"\n   Rozkład trybów:")
    for mode, count in zip(*torch.unique_consecutive(
        torch.tensor([modes.index(m) for m in modes]), return_counts=True
    )):
        print(f"     {modes[mode.item()]:25s} × {count.item()} epok")

    print("\n   🔴 <0.52 — agresywne (pełny LR)")
    print("   🟡 0.52-0.75 — konserwatywne (0.1× LR)")
    print("   🟢 ≥0.75 — degradacja (0.01× LR)")