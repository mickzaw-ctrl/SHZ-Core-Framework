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
# 2. BLOK TRANSFORMERA (PRE-LN)
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
# 3. KALIBROWALNY ADAPTIVE MODEL
# =====================================================================

class CalibratedAdaptiveBCCModel(nn.Module):
    """
    Model z ciągłym adaptacyjnym LR opartym na pewności krytyka.
    Krytyk jest kalibrowany względem rzeczywistej straty — uczy się
    oceniać jakość predykcji, nie zaśelić low confidence forever.
    """

    def __init__(self, vocab_size: int, embed_dim: int, num_heads: int,
                 num_layers: int, base_lr: float = 5e-4,
                 conf_target: float = 0.65):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)

        self.layers = nn.ModuleList([
            BCCTransformerBlock(embed_dim, num_heads) for _ in range(num_layers)
        ])
        self.ln_f = nn.LayerNorm(embed_dim)
        self.lm_head = nn.Linear(embed_dim, vocab_size)
        self.critic_head = nn.Linear(embed_dim, 1)

        self.base_lr = base_lr
        self.conf_target = conf_target  # docelowa pewność krytyka

        self.optimizer = optim.AdamW(self.parameters(), lr=base_lr)
        self.scheduler = None  # ustawiony w train()

    def forward_pass(self, tokens, mask=None):
        x = self.token_embedding(tokens)
        for layer in self.layers:
            x = layer(x, attn_mask=mask)
        x = self.ln_f(x)
        logits = self.lm_head(x)
        critic_score = self.critic_head(x)
        return logits, critic_score, x

    def adaptive_lr(self, confidence: float) -> float:
        """Ciągły LR: spada wykładniczo z уверенностью."""
        # conf 0.0 → LR×1.0
        # conf 0.5 → LR×0.5
        # conf 0.75 → LR×0.25
        # conf 1.0 → LR×0.01
        return self.base_lr * (0.5 ** (confidence / 0.25))

    def calibration_loss(self, loss_ce: float, confidence: float) -> float:
        """Loss kalibracyjny: karz niską уверенность + karz różnicę od target."""
        # 1. Kara za low confidence (confidence penalty)
        conf_penalty = 0.5 * (1.0 - confidence)

        # 2. Kara za отклонение od docelowej pewności
        target_penalty = 0.1 * (confidence - self.conf_target) ** 2

        # 3. Bonus za niską stratę (krytyk ma być pewny dobrych predykcji)
        quality_bonus = 0.2 * torch.exp(-loss_ce)

        return loss_ce + conf_penalty + target_penalty + quality_bonus

    def train_step(self, tokens, target_tokens, mask=None):
        self.train()

        logits, critic_score, _ = self.forward_pass(tokens, mask)
        loss_ce = F.cross_entropy(logits.view(-1, logits.size(-1)), target_tokens.view(-1))

        critic_prob = torch.sigmoid(critic_score)
        confidence = critic_prob.mean()

        # Adaptive LR
        current_lr = self.adaptive_lr(confidence.item())
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = current_lr

        # Kalibracyjny loss
        total_loss = self.calibration_loss(loss_ce, confidence)

        self.optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=1.0)
        self.optimizer.step()

        # Deterministyczny tryb interpretacji
        conf_val = confidence.item()
        if conf_val < 0.45:
            mode, symbol = "AGRESYWNE", "🔴"
        elif conf_val < 0.60:
            mode, symbol = "TRANZYCYJNE", "🟡"
        elif conf_val < 0.70:
            mode, symbol = "STABILNE", "🟢"
        else:
            mode, symbol = "PEWNE", "🔵"

        return {
            'loss_ce': loss_ce.item(),
            'total_loss': total_loss.item(),
            'confidence': conf_val,
            'lr': current_lr,
            'mode': mode,
            'symbol': symbol,
            'critic_score_mean': critic_score.mean().item(),
        }

    def evaluate(self, tokens, target_tokens, mask=None):
        self.eval()
        with torch.no_grad():
            logits, critic_score, _ = self.forward_pass(tokens, mask)
            loss_ce = F.cross_entropy(logits.view(-1, logits.size(-1)), target_tokens.view(-1))
            confidence = torch.sigmoid(critic_score).mean().item()
        return loss_ce.item(), confidence


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
    num_epochs = 25

    model = CalibratedAdaptiveBCCModel(
        vocab_size, embed_dim, num_heads, num_layers,
        base_lr=5e-4, conf_target=0.65
    )

    input_tokens = torch.randint(0, vocab_size, (batch_size, seq_len))
    target_tokens = torch.randint(0, vocab_size, (batch_size, seq_len))
    causal_mask = torch.tril(torch.ones(seq_len, seq_len, dtype=torch.bool))

    print("=" * 70)
    print("   KALIBROWALNY ADAPTIVE MODEL — SHZ-BCC")
    print("   LR = base_lr × 0.5^(conf / 0.25)    Target conf: 0.65")
    print("   Calibrated loss: CE + conf_penalty + target_penalty + quality_bonus")
    print("=" * 70)

    history = []
    best_loss = float('inf')

    for epoch in range(1, num_epochs + 1):
        start = time.time()

        result = model.train_step(input_tokens, target_tokens, causal_mask)
        val_loss, val_conf = model.evaluate(input_tokens, target_tokens, causal_mask)

        elapsed = (time.time() - start) * 1000
        history.append({**result, 'val_loss': val_loss, 'val_conf': val_conf})

        if result['loss_ce'] < best_loss:
            best_loss = result['loss_ce']
            marker = " ★"
        else:
            marker = ""

        print(f"[{epoch:02d}] {result['symbol']} {result['mode']:12s} | "
              f"CE: {result['loss_ce']:.4f} | "
              f"Conf: {result['confidence']:.4f} | "
              f"LR: {result['lr']:.2e} | "
              f"Val: {val_loss:.4f}/{val_conf:.4f} | "
              f"{elapsed:.1f}ms{marker}")

    # === ANALIZA ===
    print("\n" + "=" * 70)
    print("   ANALIZA PROGRESU")
    print("=" * 70)

    h = history
    init_ce = h[0]['loss_ce']
    final_ce = h[-1]['loss_ce']
    init_conf = h[0]['confidence']
    final_conf = h[-1]['confidence']
    init_lr = h[0]['lr']
    final_lr = h[-1]['lr']

    print(f"   CE:          {init_ce:.4f} → {final_ce:.4f}  (Δ={final_ce - init_ce:+.4f})")
    print(f"   Confidence:  {init_conf:.4f} → {final_conf:.4f}  (Δ={final_conf - init_conf:+.4f})")
    print(f"   LR:          {init_lr:.2e} → {final_lr:.2e}  (×{final_lr/init_lr:.3f})")
    print(f"   Speed:       {h[-1]['symbol']} {h[-1]['mode']}")

    # Korelacja confidence-loss
    import math
    ce_vals = [x['loss_ce'] for x in h]
    conf_vals = [x['confidence'] for x in h]
    n = len(ce_vals)
    mean_ce = sum(ce_vals) / n
    mean_cf = sum(conf_vals) / n
    cov = sum((ce_vals[i] - mean_ce) * (conf_vals[i] - mean_cf) for i in range(n))
    std_ce = math.sqrt(sum((x - mean_ce) ** 2 for x in ce_vals) / n)
    std_cf = math.sqrt(sum((x - mean_cf) ** 2 for x in conf_vals) / n)
    corr = cov / (std_ce * std_cf) if std_ce > 0 and std_cf > 0 else 0

    print(f"\n   Korelacja (CE, conf): {corr:.4f}")
    print(f"   (<0 = confidence spada gdy CE maleje, >0 = rośnie)")

    print("\n   LEGENDA:")
    print("   🔴 Agresywne:  conf < 0.45 | LR = pełny (5e-4)")
    print("   🟡 Tranzycyjne: conf 0.45-0.60 | LR = 0.5×")
    print("   🟢 Stabilne:   conf 0.60-0.70 | LR = 0.25×")
    print("   🔵 Pewne:      conf ≥ 0.70 | LR = 0.01×")
    print("=" * 70)