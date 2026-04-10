# 论文结果部分 Proposal（对齐新版 3 RQ）

> 本版完全按当前重构后的研究问题组织，不再沿用旧版 RQ 映射。

---

## 1. 新版研究问题（建议用于论文正文）

### RQ1（Intent）
在 **reputation-only market** 中，卖家是否表现出利用市场漏洞（vulnerabilities）的意图？

- 关注点：意图与操纵检测率（manipulation detection），而非机制对比。
- 数据范围：仅使用 reputation-only 条件下的 cognitive probing 与动作结果。

### RQ2（Welfare）
引入 warrant 后，市场总体 welfare 是否改善？

- 关注点：`seller profit`、`buyer utility`、`product quality`、`transaction count`。
- 对比关系：Rep vs Rep+Warrant（无 seller communication 干扰的基础设定）。

### RQ3（Resilience Under Seller Communication）
当 seller 受到 communication 干扰（policy-making / pressure / psychology）后，两类市场（Rep 与 Rep+Warrant）对 deception 的抵抗能力如何？

- 先做宏观：welfare 与 deception 量化变化。
- 再做微观：个体行为组成变化（如 honest/dishonest profit、产品结构、关键动作）。

### English RQ Statements (for paper text)

- **RQ1 (Intent in Reputation-Only Market):** Do sellers in a reputation-only market exhibit explicit intent to exploit known market vulnerabilities?
- **RQ2 (Warrant and Welfare):** Does introducing a warrant mechanism improve overall market welfare, in terms of seller profit, buyer utility, product quality, and transaction volume?
- **RQ3 (Resilience Under Seller Communication Interference):** Under seller-side communication interference (e.g., policy-making, pressure, and psychological prompts), which market design (reputation-only vs. reputation+warrant) is more resilient to deception, and why at both macro and micro behavioral levels?

---

## 2. 结果章节结构（建议）

### 4.1 RQ1: Vulnerability Exploitation Intent in Reputation-Only Market
- 先给总体结论：是否存在系统性操纵意图。
- 再给分漏洞类型对比：5类 vulnerability 的 detection rate。
- 最后给行为证据：对应 action 频次或典型案例（可放附录）。

### 4.2 RQ2: Warrant Improves Market Welfare
- 先给四个 welfare 指标的总览对比（Rep vs Rep+Warrant）。
- 再给机制解释图：商品质量构成、交易结构、收益来源变化。
- 强调“收益改善是否来自更诚实交易而非策略性欺骗”。

### 4.3 RQ3: Market Resilience to Seller Communication Interference
- 先做跨约束横向比较（3 类干扰 × 2 市场机制）。
- 再做宏观到微观解释链路：
- 宏观：deception/welfare 指标变化。
- 微观：profit decomposition、product mix、关键行为变化。

---

## 3. 图表规划（按新版 RQ）

### RQ1 图组（Intent only）
- `rq1_intent_rep_only_manipulation_detection.png`（主图）
  - reputation-only 下 5 类 vulnerability detection rate
- `rq1_intent_rep_only_action_evidence.png`（可选）
  - 与漏洞相关动作频次/占比（增强可解释性）

建议标题风格：
- “Sellers Show Clear Vulnerability Exploitation Intent in Reputation-Only Market”

### RQ2 图组（Welfare）
- `rq2_warrant_vs_rep_welfare_overview.png`（主图）
  - 四指标并列：seller profit / buyer utility / quality / transactions
- `rq2_warrant_vs_rep_deception_and_profit.png`（主图）
  - 核心四指标联合分布图：seller profit / HQ products counts / buyer utility / transaction count
- `rq2_listed_vs_sold_quality.png`（主图）
  - 左侧对比 listed product quality composition，右侧对比 sold-out product quality composition
  - 均使用 HQ authentic / LQ authentic / counterfeit 三类构成，避免“quality”语义重复与歧义
- `rq2_product_quality_over_rounds.png`（主图）
  - 三个子图分别跟踪 HQ authentic / LQ authentic / HQ counterfeit 随 round 的变化（Rep vs Rep+Warrant）

建议标题风格：
- “Warrant Improves Welfare Across Profit, Utility, Quality, and Transactions”

### RQ3 图组（Seller communication resilience）
- `rq3_welfare_overview.png`（主图）
  - 结构与 RQ2 welfare overview 对齐，但采用 market type × constraint 的 grouped 形式
- `rq3_seller_comm_deception_by_constraint.png`（主图）
  - 三类干扰下 deception 指标对比
- `rq3_profit_decomposition_honest_vs_dishonest.png`（主图）
  - grouped 对比 honest 与 dishonest profit
- `rq3_all_constraints_grouped.png`（主图）
  - grouped 2×2 汇总（deception / seller profit / buyer utility / transaction count）
- `rq3_product_mix_appendix.png`（附录）
  - grouped 形式展示产品结构变化（HQ authentic / LQ authentic / counterfeit）

建议标题风格：
- “Warrant Market Remains More Resilient Under Seller Communication Interference”

---

## 4. 误差棒与不确定性表达（简化版）

- 主文图统一采用误差棒表达跨 run 波动，不再作为结果叙述重点强调显著性检验。
- 误差棒口径建议统一为 `SEM`（standard error of mean），并在图注里一次性说明。
- 对于比例类图（quality composition / detection rate），优先展示每-run聚合后再求均值与误差棒，保持与总量指标口径一致。

---

## 5. 数据与路径约束（当前必须遵守）

- 可视化与统计仅使用：
- `/home/lsj/Projects/Gitself/oasis-truthmarket/experiments/paper_important_results`
- 不再读取 `experiments/gpt-4o-mini/...` 等旧路径。
- run 脚本、绘图脚本、统计脚本都保持同一数据根目录。

---

## 6. 命名与读者认知一致性（强约束）

- 文件名与图题均使用语义命名（intent / welfare / resilience），避免继续扩大 `rqX` 技术债。
- 颜色语义全局统一：
- deception / counterfeit = 暖色
- welfare positive（profit/utility/HQ authentic）= 冷静正向色
- 中性 baseline/参考 = 灰色

---

## 7. 一句话总结（可放结果章节开头）

我们将论文结果重构为“**Intent → Welfare → Resilience**”三层逻辑：先确认 reputation-only 下的漏洞利用意图（RQ1），再验证 warrant 的整体 welfare 改善（RQ2），最后检验在 seller communication 干扰下两类市场的抗欺骗韧性并给出宏观-微观解释（RQ3）。
