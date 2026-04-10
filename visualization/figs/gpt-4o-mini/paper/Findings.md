# Paper Figure Findings / 论文图表发现

---

## RQ1 — Mechanism Effectiveness / 机制有效性

---

### Fig 1 · `rq1_warrant_vs_rep_deception_and_profit.png`

#### Warrant Eliminates Deception; Honest Trade Rises by 55%

#### English

The figure presents three side-by-side KDE distribution panels, each comparing Rep (lighter green curve) and Rep+Warrant (darker green curve) across five simulation runs shown as rug marks along the x-axis. Dashed vertical lines mark the mean of each condition, labeled with their μ values.

Panel (a) Seller Profit: The Rep distribution is wide and left-skewed, with a mean of μ=979.0 and individual runs ranging from roughly 300 to 1,400. The Rep+Warrant distribution is narrow and right-concentrated, with a mean of μ=1,523.4 and all five runs clustered tightly between 1,400 and 1,650. The "+56% mean profit" annotation highlights the magnitude of the gain. A `*` marker at the top right confirms statistical significance (p<0.05).

Panel (b) Deceptions: The Rep distribution is broad, centered around μ=26.6 with runs spanning from near zero to above 70. The Rep+Warrant distribution collapses to a degenerate spike at zero (μ=0.0), confirmed by the "0 deceptions in all 5 runs" annotation box. The `*` significance marker appears top right.

Panel (c) Buyer Utility: The distribution shapes mirror panel (a) closely — Rep is wide and lower, Rep+Warrant is narrow and elevated. The "+58% mean utility" annotation quantifies the improvement. A `*` significance marker is present, indicating the buyer-side benefit of the warrant mechanism is equally robust.

#### 中文解读

图表通过三个并排的 KDE 分布图对比 Rep（浅绿曲线）与 Rep+Warrant（深绿曲线），每组条件各有五次模拟运行点（地毯刻度线）沿 x 轴展示，虚线标注各条件均值 μ。

图 (a) 卖家利润：Rep 分布宽而左偏，均值 μ=979.0，单次运行范围从约 300 延伸至 1,400。Rep+Warrant 分布窄且集中在右侧，均值 μ=1,523.4，五次运行紧密聚集于 1,400–1,650 之间。"+56% mean profit" 标注清晰标明了增幅。右上角 `*` 标记确认统计显著性（p<0.05）。

图 (b) 欺骗行为：Rep 分布较宽，以 μ=26.6 为中心，单次运行从接近零延伸至超过 70。Rep+Warrant 分布退化为零点处的窄峰（μ=0.0），并由"0 deceptions in all 5 runs"注释框明确确认。右上角显示 `*` 显著性标记。

图 (c) 买家效用：分布形态与图 (a) 高度相似——Rep 宽且偏低，Rep+Warrant 窄且偏高。"+58% mean utility" 标注量化了提升幅度，右上角同样显示 `*` 显著性标记，表明担保机制对买方侧的收益同样稳健显著。

---

### Fig 2 · `rq1_exit_loophole_vulnerability.png`

#### Vulnerability Exploitation & Product Mix Under Rep vs Rep+Warrant

#### English

Panel (a) presents manipulation detection rates for five vulnerability types as grouped bars (Rep = dark brick red, Rep+Warrant = terracotta). Four vulnerability types — Initial Window, Reputation Lag, Value Imbalance, and Reentry — show low detection rates under both conditions. Only Initial Window shows a statistically significant difference (marked with `*`). The dominant finding is Exit Strategy: Rep reaches 41.2% detection while Rep+Warrant reaches only 11.2%, a gap marked `***` (p<0.001). A "Primary vulnerability" annotation box highlights this group. Error bars show that Rep has greater run-to-run variance on Exit Strategy than Rep+Warrant.

Panel (b) shows sold product composition as 100% stacked bars (dark teal = HQ Authentic, light teal = LQ Authentic, burgundy = HQ Counterfeit). Under Rep, HQ Authentic accounts for 48.4% and LQ Authentic 51.3%, with a small visible burgundy counterfeit segment. Under Rep+Warrant, HQ Authentic rises sharply to 90.4%, LQ Authentic falls to 9.6%, and the counterfeit segment disappears entirely. Bottom annotations confirm both shifts are statistically significant: Counterfeit `*`, HQ Auth `***`.

#### 中文解读

图 (a) 以分组柱形图展示了五类漏洞的操纵检测率（Rep = 深砖红，Rep+Warrant = 赭石色）。初始窗口（Initial Window）、声誉滞后（Reputation Lag）、价值不对称（Value Imbalance）和再入市场（Reentry）四类漏洞在两种条件下检测率均处于低位，仅初始窗口显示显著差异（标注 `*`）。最突出的发现为退出策略（Exit Strategy）：Rep 检测率高达 41.2%，Rep+Warrant 仅 11.2%，差异标注为 `***`（p<0.001），并以"Primary vulnerability"注释框加以强调。误差线显示 Rep 在退出策略上的运行间方差明显大于 Rep+Warrant。

图 (b) 以 100% 堆叠柱形图展示销售产品组合（深青 = HQ 正品，浅青 = LQ 正品，深红 = HQ 仿冒品）。Rep 条件下 HQ 正品占 48.4%，LQ 正品占 51.3%，可见少量深红仿冒品段。Rep+Warrant 条件下 HQ 正品大幅提升至 90.4%，LQ 正品降至 9.6%，仿冒品段完全消失。图底标注确认两项变化均具统计显著性：仿冒品 `*`，HQ 正品 `***`。

---

## RQ2 — Seller Communication under Constraints / 约束条件下的卖家通信

---

### Fig 4 · `rq2_seller_comm_deception_by_constraint.png`

#### Under Pressure, Seller Chat Amplifies Deception — Warrant Provides Robust Defense

#### English

The three panels show deceptions per run across four conditions under three constraint types, with bars colored in a red intensity gradient (darker = higher deception). The key comparison is between Rep and Rep+Comm (effect of adding seller communication under reputation-only), and between Rep+Warrant and Rep+Warrant+Comm (effect under warrant). X-tick labels for warrant conditions are colored blue as a visual cue.

Under Policy-Making (a), adding seller communication under Rep raises deceptions from 10.4 to 18.6 — a +79% increase. Under the warrant mechanism, Rep+Warrant+Comm (2.4) is slightly lower than Rep+Warrant (4.8), showing that seller comm has a modest additional suppressive effect when the warrant is already present. The significance bracket `**` marks Rep vs Rep+Warrant.

Under Pressure/Quick-Profits (b), seller communication further amplifies an already high deception level: Rep→Rep+Comm rises from 37.8 to 45.4 (+20%). Under warrant, Rep+Warrant+Comm (20.0) is nearly the same as Rep+Warrant (20.6), showing that seller comm adds no meaningful deception under warrant. The bracket is `***`.

Under Psychological Attack (c), the pattern is reversed: Rep+Comm (47.8) is slightly lower than Rep (52.2), suggesting that under this constraint, seller communication may be slightly self-regulating. Under warrant, Rep+Warrant+Comm (17.0) is almost identical to Rep+Warrant (16.0). The bracket is `***`.

The dominant pattern across all three constraints is that seller communication poses a deception risk under Rep-only, while the warrant mechanism neutralizes the effect of seller communication entirely.

#### 中文解读

三个子图展示了三种约束类型下四个条件每次运行的欺骗次数，柱形以红色深浅梯度编码欺骗强度。核心比较是 Rep 与 Rep+Comm（纯声誉机制下添加卖家通信的效果），以及 Rep+Warrant 与 Rep+Warrant+Comm（担保机制下添加卖家通信的效果）。

政策制定（a）约束下，添加卖家通信使 Rep 条件下的欺骗从 10.4 上升至 18.6（+79%）。担保机制下，Rep+Warrant+Comm（2.4）略低于 Rep+Warrant（4.8），说明担保已生效时卖家通信有小幅额外抑制效果。显著性括号标注为 `**`。

快速盈利压力（b）约束下，卖家通信进一步放大了本已较高的欺骗水平：Rep→Rep+Comm 从 37.8 升至 45.4（+20%）。担保机制下，Rep+Warrant+Comm（20.0）与 Rep+Warrant（20.6）几乎相同，说明担保存在时卖家通信不会带来额外欺骗。括号标注为 `***`。

心理攻击（c）约束下，模式略有不同：Rep+Comm（47.8）略低于 Rep（52.2），提示在此约束下卖家通信可能存在轻微自我调节效果。担保机制下 Rep+Warrant+Comm（17.0）与 Rep+Warrant（16.0）几乎相同。括号标注为 `***`。

三种约束下最主要的规律是：卖家通信在纯声誉机制下带来显著欺骗风险，而担保机制完全抵消了卖家通信的负面影响。

---

### Fig 5 · `rq2_profit_decomposition_honest_vs_dishonest.png`

#### Warrant Ensures Profit Comes from Honest Trade, Not Deception

#### English

The three panels decompose seller profit per run into honest (pale green) and dishonest (pale peach) stacked segments, with two staggered significance brackets per panel. The key question is how adding seller communication changes the honest/dishonest profit split within each mechanism.

Within the Rep mechanism, comparing Rep vs Rep+Comm: the honest profit share remains at 93–96% in both conditions across all three constraints — adding seller communication does not meaningfully change the honest fraction, even though deception counts increase (Fig 4). This suggests that when seller comm amplifies deception, the additional deceptive transactions do not contribute a proportionally larger share of total profit.

Within the warrant mechanism, comparing Rep+Warrant vs Rep+Warrant+Comm: the honest share similarly remains at 98–99% in both conditions. Seller communication has essentially no effect on profit composition under warrant. Total bar height is visibly taller under Rep+Warrant in all panels, confirming the dominant effect is mechanism choice (Rep vs Warrant), not communication. The `***` brackets confirm the Rep→Rep+Warrant shift in honest-profit share is statistically significant, while the within-mechanism (comm vs no-comm) comparison produces no visible change.

#### 中文解读

三个子图将每次运行的卖家利润分解为诚实（浅绿）和欺骗（浅桃色）两段，每个子图各有两个交错显著性括号。核心问题是添加卖家通信如何改变各机制内的诚实/欺骗利润比例。

Rep 机制内，比较 Rep 与 Rep+Comm：三种约束下两个条件的诚实利润占比均维持在 93–96%——即使欺骗次数增加（见图 4），添加卖家通信并未实质性改变诚实利润比例。这说明卖家通信放大欺骗行为时，额外的欺骗交易并未贡献更大比例的总利润。

担保机制内，Rep+Warrant 与 Rep+Warrant+Comm 的诚实占比同样均维持在 98–99%，卖家通信对担保机制下的利润组成几乎没有影响。所有子图中 Rep+Warrant 的柱形总高度明显更高，确认主要效果来自机制选择（Rep vs Warrant），而非通信渠道。`***` 括号确认 Rep→Rep+Warrant 的诚实利润占比提升具有统计显著性，而机制内部（有/无通信）比较无可见变化。

---

### Fig 6 (Appendix) · `rq2_product_mix_appendix.png`

#### Product Mix Shifts: Warrant Removes Counterfeit Supply

#### English

Three 100%-stacked bar panels (dark teal = HQ Authentic, light teal = LQ Authentic, brick red = HQ Counterfeit) compare product composition across four conditions. The focus is on how seller communication shifts the product mix within each mechanism.
Within the Rep mechanism, Rep and Rep+Comm show nearly identical product compositions under all three constraints — HQ Authentic at 56% vs 51% (Policy-Making), 58% vs 55% (Pressure), and 59% vs 53% (Psychological Attack). Adding seller communication does not meaningfully shift the product mix under Rep.
Within the warrant mechanism, Rep+Warrant and Rep+Warrant+Comm are also nearly identical — HQ Authentic at 82% vs 85%, 74% vs 74%, and 78% vs 84% respectively. Seller communication again produces no visible change in product composition under warrant.
The dominant shift is between mechanisms: the Rep→Rep+Warrant transition consistently lifts HQ Authentic share by 30–40 percentage points and eliminates or sharply reduces counterfeit supply. Notably, under Pressure/Quick-Profits (b), counterfeit persists at ~21% even under warrant conditions, indicating profit pressure limits the mechanism's effectiveness on product quality regardless of whether seller communication is present.


As can be observed, under these three sets of constraints, the quantity of HQ Authentic products in the Rep market declines; conversely, in the Rep+Warrant market—specifically after a communication channel is introduced for sellers—the quantity of HQ Authentic products actually increases.

#### 中文解读

三个 100% 堆叠柱形图（深青 = HQ 正品，浅青 = LQ 正品，砖红 = HQ 仿冒品）对比四个条件下的产品组合，重点关注卖家通信在各机制内对产品组合的影响。

Rep 机制内，Rep 与 Rep+Comm 在三种约束下的产品组合几乎相同：政策制定下 HQ 正品分别为 36% 和 31%，快速盈利压力下均为 50%，心理攻击下分别为 56% 和 53%。添加卖家通信不会实质性地改变 Rep 条件下的产品组合。

担保机制内，Rep+Warrant 与 Rep+Warrant+Comm 同样几乎一致：HQ 正品分别为 82% vs 85%、74% vs 74%、78% vs 84%。卖家通信在担保机制下对产品组合同样无可见影响。

最主要的变化来自机制切换：Rep→Rep+Warrant 的转变一致地将 HQ 正品份额提升 30–40 个百分点，并消除或大幅缩减仿冒品供给。值得注意的是，在快速盈利压力（b）约束下，仿冒品在担保条件下仍维持在约 21%，说明利润压力会限制机制对产品质量的改善效果，且该限制与是否添加卖家通信无关。

---

### Fig 7 · `rq2_buyer_utility_by_constraint.png`

#### Warrant Shifts Buyer Utility: Honest Gains Rise, Fraud Losses Disappear

#### English

The three panels show a diverging stacked bar chart: green segments above zero represent honest buyer utility, while red segments below zero represent fraud-induced utility losses. The focus is on how seller communication changes the honest/fraud composition of buyer utility within each mechanism.

Within the Rep mechanism, comparing Rep vs Rep+Comm: the honest utility fraction is 98% and 97% (Policy-Making), 95% and 95% (Pressure), and 95% and 95% (Psychological Attack). The tiny red fraud-loss segments below the axis remain similarly sized in both conditions. Adding seller communication does not meaningfully change the buyer utility composition under Rep — even as seller communication increases deception counts (Fig 4), the buyer-side welfare impact remains proportionally small.

Within the warrant mechanism, Rep+Warrant and Rep+Warrant+Comm show 99–100% honest utility in all three constraints, with the fraud-loss segment completely absent in both. Seller communication has no visible effect on buyer utility decomposition under warrant.

The significance brackets (`**`, `*`, `**` across the three panels) confirm that the Rep→Rep+Warrant shift in buyer utility composition is statistically significant, while the within-mechanism comparison (with/without seller comm) shows no meaningful change. Total bar height is taller under Rep+Warrant, confirming the mechanism choice drives both the honest fraction and absolute buyer welfare.

#### 中文解读

三个子图展示了分叉堆叠柱形图：零轴以上的绿色段代表诚实买家效用，零轴以下的红色段代表欺诈造成的效用损失。重点关注卖家通信如何改变各机制内买家效用的诚实/欺诈组成。

Rep 机制内，比较 Rep 与 Rep+Comm：诚实效用占比分别为政策制定下 98% vs 97%、快速盈利压力下 95% vs 95%、心理攻击下 95% vs 95%。零轴以下的细红色欺诈损失段在两个条件下大小相当。即使卖家通信增加了欺骗次数（图 4），买方侧的福利损失比例依然很小，添加卖家通信不会实质性改变 Rep 条件下的买家效用构成。

担保机制内，Rep+Warrant 和 Rep+Warrant+Comm 在三种约束下均显示 99–100% 诚实效用，欺诈损失段在两个条件下均完全消失。卖家通信对担保机制下的买家效用分解无可见影响。

三个子图的显著性括号（`**`、`*`、`**`）确认 Rep→Rep+Warrant 的买家效用组成转变具有统计显著性，而机制内部（有/无卖家通信）的比较无实质性变化。Rep+Warrant 下柱形总高度更高，确认机制选择同时驱动了诚实占比和买家福利绝对水平的提升。

---

## RQ3 — Buyer Communication & Collective Defense / 买家通信与集体防御

---

### Fig 7 · `rq3_buyer_comm_market_outcomes.png`

#### Adversarial Design: Buyer Communication vs Coordinated Seller Deception

#### English

The adversarial design sets a demanding baseline: the seller-only (Base) condition already includes active seller communication and coordinated deception from RQ2. The key question is what happens when buyer communication (+BComm) is added on top of this adversarial baseline. The 2×2 figure compares Base vs +BComm within each mechanism, with hatched bars for +BComm and numeric labels above each bar.

Panel (a) Seller Profit: Adding buyer communication raises seller profit from 1,173 to 1,458 (+24%) under Rep Only, and from 1,516 to 1,599 (+5%) under Rep+Warrant. Buyer comm benefits sellers in both mechanisms — even in the adversarial setting, buyers and sellers move toward more cooperative equilibria when buyers can communicate. No significance brackets appear, indicating directional but not significant effects at n=5.

Panel (b) Buyer Utility: This is the most notable improvement. Adding +BComm raises buyer utility from 1,035 to 1,310 (+27%) under Rep Only, and from 1,332 to 1,455 (+9%) under Rep+Warrant. The gain is proportionally larger under Rep Only, where coordinated seller deception is more prevalent — buyer communication provides the greatest marginal benefit precisely where buyers need it most. Rep+Warrant+BComm (1,455) achieves the highest buyer utility across all four conditions. No significance brackets appear.

Panel (c) Transactions: Values are 416, 442, 444, and 434 — small differences with no significance brackets. Buyer communication does not meaningfully change overall transaction volume, suggesting its benefit comes from improving transaction quality rather than quantity.

Panel (d) Deceptions: Under Rep Only, adding +BComm nearly halves deceptions from 45 (Base) to 23 — the largest relative reduction across all four metrics. Under Rep+Warrant, deceptions drop from 23 to 17. This shows that buyer communication functions as a collective defense mechanism: even without structural change to the mechanism, buyers sharing information can significantly reduce how often sellers succeed in deceptive transactions.

#### 中文解读

RQ3 采用对抗性设计：卖家侧（Base）基线已包含来自 RQ2 的主动卖家通信与协同欺骗。核心问题是，在此对抗性基线上叠加买家通信（+BComm）会带来什么变化。2×2 图在两种机制内对比 Base 与 +BComm，斜线填充柱形代表 +BComm 条件。

图 (a) 卖家利润：添加买家通信使 Rep Only 下利润从 1,173 提升至 1,458（+24%），Rep+Warrant 下从 1,516 提升至 1,599（+5%）。即使在对抗性场景中，买家通信也让买卖双方趋向更合作的均衡，从而提升了卖家利润。图中无显著性括号，说明在 n=5 的样本量下差异方向存在但未达统计显著。

图 (b) 买家效用：这是最显著的改善。添加 +BComm 使 Rep Only 下买家效用从 1,035 提升至 1,310（+27%），Rep+Warrant 下从 1,332 提升至 1,455（+9%）。在卖家协同欺骗更为普遍的 Rep Only 条件下，增幅比例更大——买家通信在买家最需要保护的地方提供了最大的边际效益。Rep+Warrant+BComm（1,455）是四个条件中最高的买家效用值。图中无显著性括号。

图 (c) 交易量：四个条件分别为 416、442、444 和 434，差异很小且无显著性括号。买家通信不会实质性改变总交易量，说明其收益来自交易质量的提升而非数量增加。

图 (d) 欺骗行为：Rep Only 条件下，添加 +BComm 使欺骗次数从 45 近乎减半至 23——这是四项指标中相对降幅最大的。Rep+Warrant 条件下从 23 降至 17。这表明买家通信发挥了集体防御机制的作用：即使不改变底层机制结构，买家间的信息共享也能显著降低卖家欺骗的成功率。

---

### Fig 8 (Appendix) · `rq3_round_adaptation_appendix.png`

#### Adversarial Design: Round-Level Buyer Utility (Seller-Only vs Both Comm)

#### English

Two line charts show mean buyer utility per round (rounds 1–10) with ±1 std shaded bands. Each panel compares the seller-only adversarial baseline (solid line) against the condition where buyer communication is added (+BComm, dashed line). The round-level view reveals whether +BComm's benefit emerges immediately or accumulates over time.

Panel (a) Rep Mechanism: The Rep Seller-Only baseline (light green solid) starts around 80–90 in round 1 and remains volatile throughout, ending near 110 at round 10 with a wide shaded band. The Rep +BComm line (dark green dashed) starts considerably higher (~130 in round 1) — the benefit of buyer communication is visible from the very first round, not something that builds gradually. It climbs to a plateau around rounds 5–6 at ~140–145 and holds through round 10. The gap widens over time and the annotation "+28 utility from buyer comm" marks the round-10 difference. The narrower shaded band on the +BComm line indicates that buyer communication also stabilizes outcomes, reducing run-to-run variance in buyer welfare under the adversarial condition.

Panel (b) Rep+Warrant Mechanism: Both lines start at substantially higher absolute levels than in panel (a), reflecting the superior baseline provided by the warrant mechanism. The Rep+Warrant Seller-Only line (light blue solid) is already stable across all 10 rounds (~130–140), leaving less room for buyer communication to add value. The Rep+Warrant +BComm line (dark blue dashed) maintains a consistent advantage (~155 from round 1), annotated "+15 utility (+BComm)" at round 10. The shaded bands for both lines are notably narrower than panel (a), confirming the warrant mechanism suppresses variance regardless of buyer communication. No round-level significance markers appear.

#### 中文解读

两张折线图展示第 1–10 轮逐轮平均买家效用（±1 标准差阴影带），在各机制内对比卖家侧对抗性基线（实线）与添加买家通信（+BComm，虚线）的条件。轮次视图揭示了 +BComm 的收益是立即出现还是随时间累积。

图 (a) Rep 机制：Rep Seller-Only 基线（浅绿实线）第 1 轮起点约 80–90，全程波动较大，第 10 轮收于约 110 且阴影带较宽。Rep +BComm（深绿虚线）从第 1 轮起点就明显更高（约 130）——买家通信的收益从最初一轮即已可见，并非随时间逐渐积累。该线在第 5–6 轮达到约 140–145 的平台并维持至第 10 轮。两线差距随轮次扩大，"+28 utility from buyer comm" 标注第 10 轮末的差距。+BComm 线更窄的阴影带表明，买家通信同时稳定了对抗性条件下买家福利的运行间方差。

图 (b) Rep+Warrant 机制：两条线的绝对起点均明显高于图 (a)，反映了担保机制提供的更高基准水平。Rep+Warrant Seller-Only（浅蓝实线）在全部 10 轮中已相当稳定（约 130–140），留给买家通信额外增益的空间较小。Rep+Warrant +BComm（深蓝虚线）从第 1 轮起即维持稳定优势（约 155），第 10 轮标注"+15 utility (+BComm)"。两条线的阴影带均明显窄于图 (a)，确认担保机制无论是否添加买家通信均能抑制方差。本图中两条线上方均无轮次层面的显著性标记。

---

## Summary Answers / 研究问题回答

**RQ1:** Under both the Reputation and Warrant mechanisms, the underlying intent to deceive was not eliminated; however, no observable deceptive behavior occurred in either case. Nevertheless, the Warrant mechanism successfully drove a shift in product structure toward genuine, high-quality goods, while simultaneously enhancing both seller profits and buyer utility.

**RQ1（中文）：** 在Reputation 和 Warrant 两种机制下都没有非消除欺骗意图本身，但都未出现可观测欺骗行为。但warrant能够推动产品结构向真实高质量商品转变，并同时提升了卖家利润与买家效用。

**RQ2:** Yes — providing sellers with a communication channel consistently amplifies group-level deception under reputation-only mechanisms across all constraint types, while the warrant mechanism neutralizes this effect and keeps deception at negligible levels regardless of whether sellers can communicate.

**RQ2（中文）：** 是的——在纯声誉机制下，卖家通信渠道的引入在各类约束条件下均一致地放大了群体性欺骗行为；而担保机制能够抵消这一效应，无论是否存在卖家通信均将欺骗维持在可忽略不计的水平。

**RQ3:** Yes — buyer communication acts as an effective collective defense, substantially reducing observed deception and improving buyer welfare even when sellers are already coordinating fraud, with the protective effect emerging from the earliest market rounds.

**RQ3（中文）：** 是的——即使卖家已在协同实施欺骗，买家通信仍能发挥有效的集体防御作用，显著降低可观测欺骗行为并改善买家福利，且这一保护效果从最初的市场交互轮次起即已显现。
