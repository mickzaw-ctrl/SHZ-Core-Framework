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

        # Maska parzystości dla wymiaru głowy
        parity = torch.ones(1, 1, 1, self.head_dim)
        parity[..., self.head_dim // 2:] = -1.0
        self.register_buffer('parity_mask', parity)

    def forward(self, x, attn_mask=None):
        B, S, E = x.size()

        # Projekcja QKV
        qkv = self.qkv_proj(x)
        q, k, v = qkv.split(self.embed_dim, dim=2)

        # Reshape dla multi-head
        q = q.view(B, S, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, S, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, S, self.num_heads, self.head_dim).transpose(1, 2)

        # Wariant z parity flip
        v_parity = v * self.parity_mask

        output_singlet = torch.zeros_like(q)
        dropout_p = self.dropout_p if self.training else 0.0

        # Iteracja przez 8 konfiguracji Z_2^3 (spin, numer, parzystość)
        for i_s in [False, True]:
            for i_n in [False, True]:
                for i_p in [False, True]:
                    # Konfiguracja q, k, v
                    q_curr = torch.flip(q, dims=[2]) if i_s else q
                    k_curr = torch.flip(k, dims=[2]) if i_s else k
                    v_curr = torch.flip(v_parity if i_p else v, dims=[2]) if i_s else (v_parity if i_p else v)

                    # Maska attention
                    curr_mask = attn_mask
                    if i_s and attn_mask is not None:
                        curr_mask = torch.flip(attn_mask, dims=[-2, -1])

                    # Swap q i k dla trybu "number" (zamiana)
                    q_final, k_final = (k_curr, q_curr) if i_n else (q_curr, k_curr)
                    mask_final = curr_mask.transpose(-2, -1) if (i_n and curr_mask is not None) else curr_mask

                    # Oblicz attention
                    attn_out = F.scaled_dot_product_attention(
                        q_final, k_final, v_curr,
                        attn_mask=mask_final,
                        dropout_p=dropout_p
                    )

                    # Odwrócenie wyniku jeśli spin flip
                    if i_s:
                        attn_out = torch.flip(attn_out, dims=[2])
                    # Aplikacja maski parzystości
                    if i_p:
                        attn_out = attn_out * self.parity_mask

                    output_singlet += attn_out

        # Normalizacja przez 8 konfiguracji
        output_singlet = output_singlet / 8.0

        # Flatten heads
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
# 3. INTELIGENTNY MODEL SAMODOSKONALĄCY SIĘ
# =====================================================================

class SelfImprovingBCCModel(nn.Module):
    def __init__(self, vocab_size: int, embed_dim: int, num_heads: int, num_layers: int):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)

        self.layers = nn.ModuleList([
            BCCTransformerBlock(embed_dim, num_heads) for _ in range(num_layers)
        ])
        self.ln_f = nn.LayerNorm(embed_dim)
        self.lm_head = nn.Linear(embed_dim, vocab_size)
        self.critic_head = nn.Linear(embed_dim, 1)

    def forward_pass(self, tokens, mask=None):
        x = self.token_embedding(tokens)
        for layer in self.layers:
            x = layer(x, attn_mask=mask)
        x = self.ln_f(x)
        logits = self.lm_head(x)
        critic_score = self.critic_head(x)
        return logits, critic_score, x

    def self_improve_step(self, tokens, target_tokens, mask=None, self_correction_threshold=0.5):
        self.train()
        self.optimizer.zero_grad()

        logits, critic_score, _ = self.forward_pass(tokens, mask)
        loss_ce = F.cross_entropy(logits.view(-1, logits.size(-1)), target_tokens.view(-1))

        critic_prob = torch.sigmoid(critic_score)
        mean_critic_confidence = critic_prob.mean()

        if mean_critic_confidence.item() < self_correction_threshold:
            self_repair_loss = loss_ce + (1.0 - mean_critic_confidence)
            self_repair_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=1.0)
            self.optimizer.step()

            status = f"🔄 AUTOKOREKTA (Pewność: {mean_critic_confidence.item():.4f})"
            improved = True
        else:
            status = f"✅ STABILNA (Pewność: {mean_critic_confidence.item():.4f})"
            improved = False

        return loss_ce.item(), mean_critic_confidence.item(), status, improved


# =====================================================================
# 4. KONFIGURACJA OPTYMIZATORA (zewnętrzna - zalecana)
# =====================================================================

def train_model(model, input_tokens, target_tokens, num_epochs=10,
                self_correction_threshold=0.52, lr=5e-4):
    optimizer = optim.AdamW(model.parameters(), lr=lr)

    print("--- INICJALIZACJA MODELU SAMODOSKONALĄCEGO SIĘ SHZ-BCC ---")
    print(f"Konfiguracja: vocab={model.token_embedding.num_embeddings}, "
          f"embed={model.ln_f.normalized_shape[0]}, "
          f"heads={model.layers[0].attn.num_heads}, "
          f"layers={len(model.layers)}\n")

    print("--- SYMULACJA PĘTLI AUTONOMICZNEJ (10 EPOK) ---")

    for epoch in range(1, num_epochs + 1):
        start = time.time()

        model.optimizer.zero_grad()
        logits, critic_score, _ = model.forward_pass(input_tokens, mask=causal_mask)
        loss_ce = F.cross_entropy(logits.view(-1, logits.size(-1)), target_tokens.view(-1))
        critic_prob = torch.sigmoid(critic_score)
        mean_critic_confidence = critic_prob.mean()

        if mean_critic_confidence.item() < self_correction_threshold:
            self_repair_loss = loss_ce + (1.0 - mean_critic_confidence)
            self_repair_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            model.optimizer.step()
            status = f"🔄 AUTOKOREKTA URUCHOMIONA"
            improved = True
        else:
            status = f"✅ REPREZENTACJA STABILNA"
            improved = False

        end = time.time()
        print(f"[Epoka {epoch:02d}] Strata: {loss_ce.item():.4f} | "
              f"Pewność: {mean_critic_confidence.item():.4f} | {status} | "
              f"Czas: {(end-start)*1000:.2f} ms")

    print("\n=== PODSUMOWANIE ===")
    print("1. Pętla treningowa wykonała 10 iteracji autonomicznej samokorekty.")
    print("2. Wewnętrzny Krytyk sterował aktywacją optymalizatora.")


# =====================================================================
# 5. MAIN - POBRAWIONE I ZAMKNIĘTE
# =====================================================================

if __name__ == "__main__":
    torch.manual_seed(1337)

    # Konfiguracja środowiska
    vocab_size = 1000
    embed_dim = 128
    num_heads = 4
    num_layers = 2
    seq_len = 16
    batch_size = 4

    # Inicjalizacja modelu
    model = SelfImprovingBCCModel(vocab_size, embed_dim, num_heads, num_layers)
    model.optimizer = optim.AdamW(model.parameters(), lr=5e-4)

    # Generowanie losowych danych
    input_tokens = torch.randint(0, vocab_size, (batch_size, seq_len))
    target_tokens = torch.randint(0, vocab_size, (batch_size, seq_len))

    # Maska dolnotrójkątna (Causal)
    causal_mask = torch.tril(torch.ones(seq_len, seq_len, dtype=torch.bool))

    # Uruchomienie treningu
    train_model(
        model, input_tokens, target_tokens,
        num_epochs=10,
        self_correction_threshold=0.52
    )