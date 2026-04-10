**Summary Statistics with Gini Coefficient**

| Condition | Transaction Count | Profit | Profit | Profit margin | Profit margin | Gini Coefficient | Gini Coefficient |
|  |  | Seller | Buyer | Seller | Buyer | Seller | Buyer |
|---|---|---|---|---|---|---|---|
| Reputation-Only, Fake Channel | 2110.0±419.6 | 5523.8±1059.0 | 5023.8±1114.5 | 0.4±0.1 | 0.4±0.2 | 0.225 | 0.537 |
| Reputation-Only, Real Channel | 2212.0±187.0 | 5832.8±550.0 | 5158.8±471.1 | 0.4±0.1 | 0.4±0.2 | 0.189 | 0.585 |
| Reputation+Warrant, Fake Channel | 2309.4±117.8 | 7385.2±146.5 | 7179.2±91.4 | 0.5±0.1 | 0.4±0.1 | 0.077 | 0.720 |
| Reputation+Warrant, Real Channel | 2258.6±63.2 | 7435.8±177.9 | 7241.8±140.0 | 0.5±0.1 | 0.5±0.1 | 0.075 | 0.651 |

```latex
\begin{table}[htbp]
\centering
\caption{Summary Statistics with Gini Coefficient}
\label{tab:rq3_summary_stats}
\begin{tabular}{cccccccc}
\toprule
Condition & Transaction Count & \multicolumn{2}{c}{Profit} & \multicolumn{2}{c}{Profit margin} & \multicolumn{2}{c}{Gini Coefficient} \\
\cmidrule(lr){3-4} \cmidrule(lr){5-6} \cmidrule(lr){7-8}
 &  & Seller & Buyer & Seller & Buyer & Seller & Buyer \\
\midrule
Reputation-Only, Fake Channel & 2110.0±419.6 & 5523.8±1059.0 & 5023.8±1114.5 & 0.4±0.1 & 0.4±0.2 & 0.225 & 0.537 \\
Reputation-Only, Real Channel & 2212.0±187.0 & 5832.8±550.0 & 5158.8±471.1 & 0.4±0.1 & 0.4±0.2 & 0.189 & 0.585 \\
Reputation+Warrant, Fake Channel & 2309.4±117.8 & 7385.2±146.5 & 7179.2±91.4 & 0.5±0.1 & 0.4±0.1 & 0.077 & 0.720 \\
Reputation+Warrant, Real Channel & 2258.6±63.2 & 7435.8±177.9 & 7241.8±140.0 & 0.5±0.1 & 0.5±0.1 & 0.075 & 0.651 \\
\bottomrule
\end{tabular}
\end{table}
```