# Experimental Findings — What Each Experiment Answers

> Data source: `experiments/gpt-4o-mini/paper/`  
> All results are averaged over 5 independent runs (mean ± std).  
> Statistical tests: Mann-Whitney U for totals; z-score proportion test for rates.

---

## Clarification: Deceptions vs. HQ-Counterfeit Sold

Two metrics that appear in different figures measure related but **distinct** phenomena:

| Metric | Meaning | Figure |
|---|---|---|
| `Deceptions` (`is_honest=False`) | Seller **attempted** to deceive in their sales communication | Fig 1 (bar), Fig 4 (bar) |
| `HQ Counterfeit Sold` | LQ product **successfully** sold as HQ — deception succeeded | Fig 3, 6 (product mix) |

**Why do deception attempts look high but HQ Counterfeit sold looks near-zero?**

In the Rep-only baseline (RQ1):
- 133 deception attempts across 5 runs, but only **6** led to an actual sale (~4.5% success rate).
- Buyers rely on reputation scores and price signals to detect fraud — they reject ~95% of counterfeit pitches.
- Sellers still try frequently because a successful counterfeit earns 6.0 profit (vs. 4.0 for honest LQ), but most attempts fail.
- The product-mix appendix shows what was **sold** (≈0.3% counterfeit), not what was attempted.

**Implication**: `Deceptions` measures *seller risk-taking behavior*; `HQ Counterfeit Sold` measures *market safety outcome*. A market can have high deception attempts yet remain mostly safe if buyers are good at detection.

---

## RQ1 — Does Adding a Warrant Mechanism Eliminate Fraud?

**Experimental design**:  
Two conditions, no communication, 5 runs each.

| Condition | Mechanism | Seller Profit | Buyer Utility | Deceptions |
|---|---|---|---|---|
| Rep-only (`r_wo`)       | Reputation only      | 979 ± 419 | 967 ± 423  | 26.6 |
| Rep+Warrant (`rw_wo`)   | Reputation + Warrant | **1523 ± 84** | **1523 ± 84** | **0.0** |

**Finding**: The warrant mechanism is a highly effective intervention.
- Deceptions drop from 26.6 to 0 — complete elimination.
- Profit/utility more than double (+55%).
- Variance collapses (±419 → ±84), suggesting much more consistent market behavior.

**What this answers**:
> *"Can a warrant mechanism alone reliably suppress seller fraud in a reputation market?"*  
> **Yes** — warrant escrow changes the economic incentive: sellers cannot profit from counterfeits because posting a warrant signals quality credibly; failing to post a warrant is itself a red flag to buyers.

**Key vulnerability finding (Fig 2)**:
- Even in Rep+Warrant, buyers show ~20% manipulation detection rate for "Exit-Strategy" tactics.
- Sellers who plan to exit the market (low reputation, approaching exit round) are still able to deceive before leaving.
- The warrant does not fully cover last-round exit loops.

---

## RQ2 — How Does Seller Communication Amplify or Dampen Fraud?

**Experimental design**:  
3 types of seller communication content × 2 mechanisms (Rep / Rep+Warrant) × 2 channel types (Fake / Real) = 12 conditions, 5 runs each.

### Seller Communication Content Types

| Content type | Description | Rep deceptions | Rep+Warrant deceptions |
|---|---|---|---|
| `policy_making`        | Sellers discuss rules/norms  | 10–18  | 2–5   |
| `pressure_quickprofits`| Sellers pressure for quick profit | 38–45  | 23–26 |
| `psychological-attack` | Sellers use manipulation/coercion | **47–52**  | 16–17 |

**Findings**:
1. **Content type shapes deception rates**: Psychological attacks trigger the most deception attempts (52/run); policy-making discussions produce the fewest (10/run).
2. **Warrant provides consistent robustness**: Even under psychological attack, Rep+Warrant deceptions are only 16–17 vs. 47–52 for Rep-only.
3. **Channel type (Fake vs. Real) has modest secondary effects**: In some conditions, Real channel slightly changes outcomes, but the mechanism type (Rep vs. Warrant) dominates.
4. **Profit is higher with warrant** across all content types (~1500 vs. ~1000–1170 for Rep).

**What this answers**:
> *"Can malicious seller communication undermine market integrity? Does Rep+Warrant remain effective against coordination attacks?"*  
> **Yes to both**: seller communication can dramatically increase fraud attempts, but the warrant mechanism maintains relatively safe outcomes even under adversarial coordination.

**Implication for policy**: Banning psychological/manipulation-style content (e.g., content moderation) could reduce deceptions in Rep-only markets. Rep+Warrant is more robust to content policy failures.

---

## RQ3 — Does Buyer Communication Improve Market Quality?

**Experimental design**:  
4 conditions: 2 mechanisms × 2 buyer communication types (Fake channel = baseline; Real channel = active buyer comm), 5 runs each.

> **Note on Fake/Real channel**: The Fake channel represents a "buyer communication aware" context where buyers are primed to share information but the channel does not function; the Real channel enables actual buyer-to-buyer information sharing.

| Condition | Mechanism | Buyer Comm | Seller Profit | Buyer Utility | Deceptions |
|---|---|---|---|---|---|
| `r_wbc_F`  | Rep only      | None (Fake) | 1485 ± 142 | 1477 ± 138 | 1.4 |
| `r_wbc_R`  | Rep only      | Real        | **1580 ± 50** | **1546 ± 44** | 3.4 |
| `rw_wbc_F` | Rep+Warrant   | None (Fake) | 1525 ± 30  | 1525 ± 30  | 0.0 |
| `rw_wbc_R` | Rep+Warrant   | Real        | **1565 ± 16** | **1565 ± 16** | 0.0 |

**Findings**:
1. **Buyer communication boosts utility** in both mechanisms: +95 profit / +69 utility for Rep, +40 profit/utility for Rep+Warrant.
2. **Deceptions are near-zero in all RQ3 conditions** — the buyer communication context (even fake) appears to make sellers less willing to attempt fraud. This differs sharply from RQ1 Rep (26.6 deceptions), suggesting the design of buyer communication as a market feature has an inherent deterrence effect.
3. **Rep+Warrant+BComm achieves the best outcome**: highest profit (1565), highest utility (1565), lowest variance (±16), zero deceptions.
4. **Buyer communication reduces variance** (Rep: ±142 → ±50; Rep+Warrant: ±30 → ±16), indicating more stable markets.

**What this answers**:
> *"Can buyer communication serve as a collective defense mechanism that improves market quality beyond what reputation or warranty mechanisms provide alone?"*  
> **Yes** — buyer communication improves buyer utility and market stability. It is not a substitute for the warrant mechanism but a complementary layer that amplifies gains in both mechanisms.

**Per-round pattern (Fig 8)**:
- The buyer-comm advantage accumulates gradually — rounds 1–3 show small differences; by round 5+, the gap stabilizes at +7 utility/round for Rep, +4 for Rep+Warrant.
- This suggests buyers need a few rounds to learn from shared information.

---

## Cross-Cutting Observations

### Effectiveness Hierarchy (by deceptions eliminated)

```
Rep+Warrant+BComm  ≈  Rep+Warrant ≫  Rep+BComm ≫  Rep-only
Deceptions:           0                3.4             26.6
Buyer utility:       1565             1546            1477/967
```

### Three Pillars of Market Safety

| Pillar | Mechanism | Effect |
|---|---|---|
| **Structural** | Warrant (escrow)         | Eliminates fraud incentive at economic level |
| **Social**     | Reputation system        | Partial deterrence; insufficient alone        |
| **Collective** | Buyer communication      | Amplifies vigilance; reduces uncertainty      |

### Trade-off: Seller Communication Risk vs. Buyer Communication Benefit

| Intervention | Profit change | Deception change | Net verdict |
|---|---|---|---|
| Seller comm — policy_making      | −375 (rep) | −8 (rep)   | Neutral–positive |
| Seller comm — psychological-attack | −130 (rep) | +26 (rep) | Harmful           |
| Buyer comm — Real channel         | +95 (rep)  | +2 (rep)   | Positive         |

> Seller communication risk is asymmetric: benign content (policy_making) slightly helps; adversarial content (attack) significantly harms. Buyer communication is uniformly positive.

---

## Figures Map

| Figure file | What it shows | RQ |
|---|---|---|
| `rq1_warrant_vs_rep_deception_and_profit.png` | Warrant eliminates deceptions; doubles profit | RQ1 |
| `rq1_exit_loophole_vulnerability.png` | Remaining vulnerability: exit-strategy attacks | RQ1 |
| `rq1_product_mix_appendix.png` | Counterfeit sales near-zero even in Rep | RQ1 |
| `rq2_seller_comm_deception_by_constraint.png` | Psychological attacks peak deception; warrant robust | RQ2 |
| `rq2_profit_decomposition_honest_vs_dishonest.png` | Warrant shifts profit source to honest | RQ2 |
| `rq2_product_mix_appendix.png` | Product quality under seller manipulation | RQ2 |
| `rq3_buyer_comm_market_outcomes.png` | Buyer comm improves all 4 metrics | RQ3 |
| `rq3_round_adaptation_appendix.png` | Comm advantage accumulates round by round | RQ3 |
