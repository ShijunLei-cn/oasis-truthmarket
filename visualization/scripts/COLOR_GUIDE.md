# Visualization Color Guide

> All figures in this project follow a **semantic color system**:  
> color encodes **meaning** (good / bad / neutral), NOT condition names.  
> Condition variants (Rep vs Rep+Warrant) are distinguished by hue saturation  
> and line style, not by an unrelated second color.

---

## Core Semantic Palette

| Color role | Hex | Usage |
|---|---|---|
| `good_dark`  | `#1a7a3a` | Best / Rep+Warrant positive bars; key "good outcome" emphasis |
| `good_mid`   | `#4caf72` | Rep positive bars (lighter shade of same green hue) |
| `good_light` | `#a8d8b8` | Stacked honest-profit segment inside bars |
| `bad_dark`   | `#c0392b` | Deception bars (Rep), high-manipulation probe bars |
| `bad_mid`    | `#e57373` | Deception bars (Rep+Warrant, near-zero) |
| `bad_light`  | `#ffcdd2` | Stacked dishonest-profit segment inside bars |
| `neutral`    | `#9e9e9e` | Baseline / no-comm end of dumbbell; gray line in evolution plots |
| `neutral_dark`| `#424242`| Dark annotation text, secondary axis labels |

## Product Quality Colors

| Color role | Hex | Usage |
|---|---|---|
| `hq_auth`    | `#2e7d32` | HQ Authentic sold — green (genuinely good product) |
| `lq_auth`    | `#66bb6a` | LQ Authentic sold — lighter green (honest, lower quality) |
| `counterfeit`| `#c62828` | HQ Counterfeit sold — red (fraud: advertised HQ, delivered LQ) |

## RQ3 Mechanism Colors

Used in Fig 7 and Fig 8 to distinguish the two market mechanisms:

| Condition | Color | Line style | Rationale |
|---|---|---|---|
| Rep (no comm)       | `#81c784` (light green)   | solid   | Mechanism base, positive metric |
| Rep + Buyer Comm    | `#2e7d32` (dark green)    | dashed  | Same mechanism, darker = improvement |
| Rep+Warrant (no comm)| `#64b5f6` (light blue)  | solid   | Blue = warrant mechanism |
| Rep+Warrant + Comm  | `#1565c0` (dark blue)     | dashed  | Same warrant, darker = with comm |

> **Why two hues for RQ3?**  
> RQ3 compares two *mechanisms* (Rep vs Rep+Warrant) each with/without buyer  
> communication. Using green for Rep and blue for Rep+Warrant makes the  
> mechanism contrast visually immediate. Both hues are applied dark→light for  
> the communication contrast within each mechanism.

## Significance Marker Convention

All significance markers use **black text** positioned above the compared bars:

| Marker | Threshold | Test |
|---|---|---|
| `*`   | p < 0.05  | Mann-Whitney U (for total counts/sums) |
| `**`  | p < 0.01  | Mann-Whitney U |
| `***` | p < 0.001 | Mann-Whitney U or z-score proportion test |
| *(none)* | p ≥ 0.05 | Not shown (no marker drawn) |

- **Mann-Whitney U**: used for total quantities per run (profit, utility, transactions, deductions count).  
- **z-score proportion test**: used for rates and fractions (probe detection rate, honest-profit %, counterfeit share).

Each figure includes a footnote at the bottom explaining the markers:  
> *"Significance markers: \* p<0.05,  \*\* p<0.01,  \*\*\* p<0.001 (Mann-Whitney U for totals; z-score proportion test for rates)"*

## Rules That Must NOT Be Violated

1. **Never use green for a "bad" metric** (deceptions, counterfeit).
2. **Never use red for a "good" metric** (profit, utility, authentic products).
3. **Never use the same hue for two semantically different roles** in the same figure  
   (e.g., do not use blue for a histogram background AND blue for a condition label).
4. **Do not add line breaks (`\n`) to axis tick labels or subplot titles** unless the  
   label is genuinely too long for the available width at 300 DPI.
5. **Arrows must not extend into adjacent bars.** Use compact text-box annotations  
   above the target bar instead of long diagonal arrows crossing bar regions.

## File Naming Convention

Output filenames encode the finding, not the chart type:

| File | Description |
|---|---|
| `rq1_warrant_vs_rep_deception_and_profit.png` | RQ1 main: profit & deceptions |
| `rq1_exit_loophole_vulnerability.png` | RQ1: probe detection by vulnerability |
| `rq1_product_mix_appendix.png` | RQ1 appendix: sold product composition |
| `rq2_seller_comm_deception_by_constraint.png` | RQ2: deceptions × constraint × condition |
| `rq2_profit_decomposition_honest_vs_dishonest.png` | RQ2: honest vs dishonest profit split |
| `rq2_product_mix_appendix.png` | RQ2 appendix: product quality by constraint |
| `rq3_buyer_comm_market_outcomes.png` | RQ3 main: 2×2 multi-metric comparison |
| `rq3_round_adaptation_appendix.png` | RQ3 appendix: per-round buyer utility |
