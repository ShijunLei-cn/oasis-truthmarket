**Summary Statistics Comparison by Temperature**

| Temperature | Buyer Utility (Mean ± Std) | Seller Profit (Mean ± Std) | Transactions (Mean ± Std) | Deception Rate (Mean ± Std) | Market Efficiency (Mean ± Std) |
|---|---|---|---|---|---|
| 0.0 | 198.4 ± 3.2 | 200.4 ± 0.8 | 50.0 ± 0.0 | 51.2 ± 22.7 | 398.8 ± 2.4 |
| 0.5 | 200.0 ± 0.0 | 200.0 ± 0.0 | 50.0 ± 0.0 | 71.0 ± 0.0 | 400.0 ± 0.0 |
| 1.0 | 258.0 ± 80.8 | 278.0 ± 70.3 | 70.0 ± 16.7 | 33.8 ± 10.3 | 536.0 ± 150.4 |

```latex
\begin{table}[htbp]
\centering
\caption{Summary Statistics Comparison by Temperature}
\label{tab:temp_summary_stats}
\begin{tabular}{cccccc}
\toprule
Temperature & Buyer Utility (Mean ± Std) & Seller Profit (Mean ± Std) & Transactions (Mean ± Std) & Deception Rate (Mean ± Std) & Market Efficiency (Mean ± Std) \\
\midrule
0.0 & 198.4 ± 3.2 & 200.4 ± 0.8 & 50.0 ± 0.0 & 51.2 ± 22.7 & 398.8 ± 2.4 \\
0.5 & 200.0 ± 0.0 & 200.0 ± 0.0 & 50.0 ± 0.0 & 71.0 ± 0.0 & 400.0 ± 0.0 \\
1.0 & 258.0 ± 80.8 & 278.0 ± 70.3 & 70.0 ± 16.7 & 33.8 ± 10.3 & 536.0 ± 150.4 \\
\bottomrule
\end{tabular}
\end{table}
```

**Summary Statistics with Gini Coefficient**

| Temperature | Transaction Count | Profit | Profit | Profit margin | Profit margin | Gini Coefficient | Gini Coefficient |
|  |  | Seller | Buyer | Seller | Buyer | Seller | Buyer |
|---|---|---|---|---|---|---|---|
| 0.0 | 50.0±0.0 | 200.4±0.8 | 198.4±3.2 | 0.5±0.0 | 0.5±0.1 | 0.325 | 0.007 |
| 0.5 | 50.0±0.0 | 200.0±0.0 | 200.0±0.0 | 0.5±0.0 | 0.5±0.0 | 0.493 | 0.000 |
| 1.0 | 70.0±16.7 | 278.0±70.3 | 258.0±80.8 | 0.5±0.1 | 0.5±0.2 | 0.456 | 0.202 |

```latex
\begin{table}[htbp]
\centering
\caption{Summary Statistics with Gini Coefficient}
\label{tab:temp_summary_stats_gini}
\begin{tabular}{cccccccc}
\toprule
Temperature & Transaction Count & Profit & Profit & Profit margin & Profit margin & Gini Coefficient & Gini Coefficient \\
\cmidrule(lr){2-3} \cmidrule(lr){4-5} \cmidrule(lr){6-7} \cmidrule(lr){8-9}
 &  & Seller & Buyer & Seller & Buyer & Seller & Buyer \\
\midrule
0.0 & 50.0±0.0 & 200.4±0.8 & 198.4±3.2 & 0.5±0.0 & 0.5±0.1 & 0.325 & 0.007 \\
0.5 & 50.0±0.0 & 200.0±0.0 & 200.0±0.0 & 0.5±0.0 & 0.5±0.0 & 0.493 & 0.000 \\
1.0 & 70.0±16.7 & 278.0±70.3 & 258.0±80.8 & 0.5±0.1 & 0.5±0.2 & 0.456 & 0.202 \\
\bottomrule
\end{tabular}
\end{table}
```