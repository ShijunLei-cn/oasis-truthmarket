**Summary Statistics Comparison by Temperature**

| Temperature | Buyer Utility (Mean ± Std) | Seller Profit (Mean ± Std) | Transactions (Mean ± Std) | Deception Rate (Mean ± Std) | Market Efficiency (Mean ± Std) |
|---|---|---|---|---|---|
| 0.0 | 212.8 ± 25.6 | 212.8 ± 25.6 | 53.2 ± 6.4 | 34.4 ± 29.9 | 425.6 ± 51.2 |
| 0.5 | 280.0 ± 0.0 | 280.0 ± 0.0 | 70.0 ± 0.0 | 27.0 ± 0.0 | 560.0 ± 0.0 |
| 1.0 | 387.2 ± 191.0 | 387.2 ± 191.0 | 96.8 ± 47.8 | 19.6 ± 19.5 | 774.4 ± 382.1 |

```latex
\begin{table}[htbp]
\centering
\caption{Summary Statistics Comparison by Temperature}
\label{tab:temp_summary_stats}
\begin{tabular}{cccccc}
\toprule
Temperature & Buyer Utility (Mean ± Std) & Seller Profit (Mean ± Std) & Transactions (Mean ± Std) & Deception Rate (Mean ± Std) & Market Efficiency (Mean ± Std) \\
\midrule
0.0 & 212.8 ± 25.6 & 212.8 ± 25.6 & 53.2 ± 6.4 & 34.4 ± 29.9 & 425.6 ± 51.2 \\
0.5 & 280.0 ± 0.0 & 280.0 ± 0.0 & 70.0 ± 0.0 & 27.0 ± 0.0 & 560.0 ± 0.0 \\
1.0 & 387.2 ± 191.0 & 387.2 ± 191.0 & 96.8 ± 47.8 & 19.6 ± 19.5 & 774.4 ± 382.1 \\
\bottomrule
\end{tabular}
\end{table}
```

**Summary Statistics with Gini Coefficient**

| Temperature | Transaction Count | Profit | Profit | Profit margin | Profit margin | Gini Coefficient | Gini Coefficient |
|  |  | Seller | Buyer | Seller | Buyer | Seller | Buyer |
|---|---|---|---|---|---|---|---|
| 0.0 | 53.2±6.4 | 212.8±25.6 | 212.8±25.6 | 0.5±0.0 | 0.5±0.0 | 0.375 | 0.039 |
| 0.5 | 70.0±0.0 | 280.0±0.0 | 280.0±0.0 | 0.5±0.0 | 0.5±0.0 | 0.520 | 0.229 |
| 1.0 | 96.8±47.8 | 387.2±191.0 | 387.2±191.0 | 0.5±0.0 | 0.5±0.0 | 0.371 | 0.307 |

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
0.0 & 53.2±6.4 & 212.8±25.6 & 212.8±25.6 & 0.5±0.0 & 0.5±0.0 & 0.375 & 0.039 \\
0.5 & 70.0±0.0 & 280.0±0.0 & 280.0±0.0 & 0.5±0.0 & 0.5±0.0 & 0.520 & 0.229 \\
1.0 & 96.8±47.8 & 387.2±191.0 & 387.2±191.0 & 0.5±0.0 & 0.5±0.0 & 0.371 & 0.307 \\
\bottomrule
\end{tabular}
\end{table}
```