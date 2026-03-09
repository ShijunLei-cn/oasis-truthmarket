# 论文实验可视化方案（修订版）

> 本版本根据 presentation feedback 修订，重点调整：
> 以 RQ 结论驱动图设计，每图一个信息，颜色按语义而非条件编码，补充统计显著性规划，所有图标题均为可直接带走的结论。

---

## 1. 实验结构与数据基础

参考 `scripts/run_exp4paper_main.sh`，当前 `experiments/gpt-4o-mini/paper` 的实验组织可分为三组：

- **RQ1**：基础机制对比——`r_wo`（Reputation Only）vs `rw_wo`（Reputation + Warrant）
- **RQ2**：卖家通信与约束——3 类约束（Policy-Making / Pressure-Quick-Profits / Psychological-Attack）× 4 类条件（Rep / Rep+Comm / Rep+Warrant / Rep+Warrant+Comm）
- **RQ3**：买家通信——4 类条件（`r_wbc_F` / `r_wbc_R` / `rw_wbc_F` / `rw_wbc_R`）

每个条件 5 次重复运行。关键数值如下（均值，供图标题撰写参考）：

| 条件 | 卖家利润 | 买家效用 | 欺骗次数 |
|---|---|---|---|
| Rep（RQ1） | 979 | 967 | 26.6 |
| Rep+Warrant（RQ1） | 1523 | 1523 | 0 |
| Rep, pressure, Comm | 1173 | 1035 | 45.4 |
| Rep+Warrant, pressure, Comm | 1516 | 1332 | 23.0 |
| Rep, buyer Comm（RQ3） | 1580 | 1546 | 3.4 |
| Rep+Warrant, buyer Comm（RQ3） | 1565 | 1565 | 0 |

---

## 2. 总体设计原则（根据反馈调整）

### 2.1 每张图只传递一个结论

不把多个对比并排进一张图，除非结论本身就是"这些条件没有差异"。

- **论文图**：可以用 2x2 分面，但每个子图对应同一个结论的不同维度验证
- **幻灯片图**：一张图一个子图，一个结论，一个标题

### 2.2 图标题 = 读者直接带走的结论

每张图的标题不是描述图内容，而是描述图的核心发现。例如：

| 错误示例 | 正确示例 |
|---|---|
| Round Evolution Comparison | Warrant Eliminates Deception — Profits Rise 55% |
| Manipulation Detection by Vulnerability Type | Sellers Exploit "Exit Loophole" 4× More Without Warrant |
| Buyer Communication Effects | Buyer Coordination Cuts Deception Without Requiring Warrant |

### 2.3 颜色按语义含义编码，不按条件名称编码

**核心原则：颜色传递判断，线型区分条件。**

| 使用场景 | 颜色规则 |
|---|---|
| 表示"好结果"的指标（诚实利润、真品销售、买家效用） | 绿色系（深浅区分变体） |
| 表示"坏结果"的指标（欺骗次数、假货、低效用） | 红色系 |
| 中性背景或基准柱/线 | 灰色 |
| 条件对比中的两条线（Rep vs Rep+Warrant） | 实线 vs 虚线，**同一色相的深浅**，不引入第二套色相 |

**禁止混用**：如果蓝色已经用于柱状图中性背景，就不能同时用蓝色表示"Rep 条件"；选一种含义，全局统一。

**不要过度使用绿色**：绿色只用于强调关键的"好结果"对比点，背景或次要指标保持灰色中性。

### 2.4 统计显著性是每个比较图的必要元素

凡是两组之间的比较图，都必须标注显著性：

- **比例类指标**（操纵检测率、欺骗比例、假货比例）：用 **z-score 检验**，比较两个比例是否显著不同
- **总量类指标**（利润、效用、交易量）：用 **Mann-Whitney U 检验**（5次运行，非正态分布假设更安全）
- 显著性标注方式：在图中对比柱/线上方加 `*` / `**` / `***`（p < 0.05 / 0.01 / 0.001），或在 round 演化图上在差异出现的 round 处画小星号
- **不允许在没有统计检验的情况下用描述性语言说"条件 A 好于条件 B"**

### 2.5 在图上加注释引导视线

对于信息量稍多的图（例如轮次演化图），要用以下方式帮助读者找到重点：

- 箭头指向关键转折点
- 文字框标注关键数值（如"Deceptions = 0 throughout"）
- 用阴影框圈出需要重点关注的 round 区间

---

## 3. 分 RQ 的图片方案

每张图按以下格式描述：
- **结论标题**（幻灯片标题 = 读者带走的结论）
- 这张图在回答哪个 RQ 子问题
- 图型和编码方案
- 统计检验计划
- 如何在图上加注释

---

### RQ1：Warrant 机制能否系统性压制欺骗并改善市场？

---

#### 图 1：`Warrant Eliminates Deception Entirely; Honest Trade Rises by 55%`

**回答的问题**：RQ1 的核心结论是什么——Warrant 比 Reputation-only 好多少？

**图型**：两张并排的柱状图（每个 RQ 主图只做两根柱，不做 2x2）

- 左图：卖家总利润（`Rep` vs `Rep+Warrant`）
- 右图：总欺骗次数（`Rep` vs `Rep+Warrant`）

**颜色**：
- 利润柱：绿色（代表"好结果"）——深绿 = Rep+Warrant，浅绿 = Rep；差值用绿色箭头标注 +55%
- 欺骗柱：红色（代表"坏结果"）——Rep 一根红柱，Rep+Warrant 一根接近零的浅灰柱
- 误差条用黑色细线

**统计**：利润用 Mann-Whitney U（n=5），欺骗比例用 z-score 检验，在柱上方标 `***`

**注释**：在欺骗图的 Rep+Warrant 柱旁加文字框 `"0 deceptions in all 5 runs"`

---

#### 图 2：`Sellers Exploit the 'Exit Loophole' 4× More Without Warrant`

**回答的问题**：机制差异体现在哪种操纵心理上？是否具体到某一类漏洞？

**图型**：单图分组柱状图

- x 轴：5 类漏洞（IW / RL / VI / RE / ES）
- y 轴：manipulation detection rate（%）
- 两组柱：Rep（浅色）vs Rep+Warrant（深色）

**颜色**：
- 所有柱用红色系——高检测率 = 操纵倾向高 = 坏结果
- Rep：深红；Rep+Warrant：浅红（接近粉色）
- 在 `Exit Strategy` 柱上加箭头，标注 `41.2% vs 11.2%`

**不要在这张图里混入其他颜色**：绿色不出现（这张图全部是"坏倾向"的测量）

**统计**：5 类漏洞各自做 z-score 检验，只在差异显著的漏洞柱上方标 `*`

**注释**：用一个矩形框圈住 `Exit Strategy` 组，旁边加小标签 `"Primary vulnerability"`

---

#### 图 3（附录）：`Warrant Shifts Market Output to Authentic HQ — Counterfeit Disappears`

**回答的问题**：利润和欺骗的变化，体现在卖出的商品构成上吗？

**图型**：100% 堆叠柱（两根柱：Rep vs Rep+Warrant）

**颜色**：
- HQ authentic sold：绿色
- LQ authentic sold：灰绿色
- HQ counterfeit sold：红色

**统计**：对各类型商品占比做 z-score 检验，标在堆叠段旁边

**这张图定位为附录**：主文两张图已经说清楚结论，这张是机制解释层面的支撑

---

### RQ2：卖家通信是否放大欺骗？不同约束下效果一致吗？

---

#### 图 4：`Under Pressure, Seller Chat Amplifies Deception — Warrant Provides Robust Defense`

**回答的问题**：三类约束下，通信+机制组合谁最危险、谁最稳？

**图型**：3 行 × 1 列的分面柱状图（不做热力图——热力图需要读者解码色深，信息负担太高）

- 每个分面 = 一种约束
- x 轴：4 个条件（Rep / Rep+Comm / Rep+Warrant / Rep+Warrant+Comm）
- y 轴：欺骗次数

**颜色**：
- 只用红色系（欺骗 = 坏结果）
- 颜色深浅按欺骗数量自动分级，不按条件名称分色
- Rep+Warrant 和 Rep+Warrant+Comm 整体颜色更浅（欺骗更少）

**统计**：每个约束内，4 个条件两两做 Mann-Whitney U 检验；在差异显著的柱对之间画横线标 `*`

**注释**：
- 在 `pressure_quickprofits` 分面内，用文字框圈出 `Rep+Comm`（欺骗最高点），标 `"Peak: 45.4"`
- 在 `Rep+Warrant+Comm` 柱旁加绿色小箭头，标注 `"Warrant holds"`

**拆分建议**：在幻灯片中建议一次只展示一个约束分面，然后翻页逐一呈现另外两个

---

#### 图 5：`Warrant Ensures Profit Comes from Honest Trade, Not Deception`

**回答的问题**：高利润背后，是因为机制更健康，还是因为欺骗更赚钱？

**图型**：3 行 × 1 列分面，每个分面 = 一种约束，每个分面内是堆叠柱

- x 轴：4 个条件
- y 轴：卖家总利润
- 堆叠：诚实利润（绿色）+ 欺骗利润（红色）

**颜色**：
- 诚实利润：绿色
- 欺骗利润：红色
- 读者应该一眼看到：Rep+Warrant 系列柱子几乎全绿，Rep 系列柱子有明显红色段

**统计**：对诚实利润比例（honest_profit / total_profit）做 z-score 检验，在柱顶标注

**注释**：在 `pressure_quickprofits` 的 `Rep+Comm` 柱上加文字框 `"45% from deception"`

---

#### 图 6（附录）：`Product Mix Shifts: Warrant Removes Counterfeit Supply`

**回答的问题**：卖家通信如何影响商品构成？

**图型**：3 行分面，100% 堆叠柱（同图 3 结构）

**颜色**：与图 3 一致（绿=HQ authentic，灰绿=LQ authentic，红=HQ counterfeit）

**这张图定位为附录**：图 4 和图 5 已经说清楚，这张是质量维度的补充

---

### RQ3：买家通信能否在没有 Warrant 的情况下形成集体防御？

---

#### 图 7：`Buyer Communication Alone Can Suppress Deception Almost as Effectively as Warrant`

**回答的问题**：买家通信的边际效果——能否替代 Warrant？

**图型**：dumbbell plot（哑铃图）

- y 轴：4 个条件组（Rep / Rep+BComm / Rep+Warrant / Rep+Warrant+BComm）
- x 轴：欺骗次数（或 hq_counterfeit_sold）
- 每条线的左端=无通信，右端=有通信，箭头方向=通信带来的变化方向

**颜色**：
- 线条和点：左端（无通信）灰色，右端（有通信）绿色（如果欺骗减少）或红色（如果欺骗增加）
- 通过箭头颜色直接传达"通信是否有帮助"

**统计**：每对（无通信 vs 有通信）做 Mann-Whitney U，在哑铃线上方标显著性

**注释**：在 `Rep+BComm` 的点旁边加标签 `"3.4 deceptions (≈ Rep+Warrant)"`，说明买家通信近似达到 Warrant 效果

---

#### 图 8（附录）：`Buyer Coordination Builds Gradually — Deception Drops Round by Round`

**回答的问题**：买家通信是即时效果，还是逐轮学习的积累效果？

**图型**：折线图

- x 轴：round 1–10
- y 轴：每 round 的欺骗次数
- 只画两条线：`Rep` vs `Rep + Buyer Comm`

**颜色**：
- `Rep`：实线，灰色
- `Rep + Buyer Comm`：实线，绿色（因为欺骗越来越少是好结果）
- 不画第三四条线，避免信息过载

**统计**：在每个 round 做双样本 Mann-Whitney U，在差异显著的 round 标 `*`（可以只标后几轮，如果前期差异不显著就不标）

**注释**：如果趋势线有明显转折点，用箭头标出 `"Buyers learn to coordinate"`

---

## 4. 图片优先级与幻灯片分配建议

### 主文图（最重要，每张对应一个结论）

| 编号 | 图标题（= 幻灯片标题） | 对应 RQ |
|---|---|---|
| 图 1 | Warrant Eliminates Deception; Honest Trade Rises 55% | RQ1 核心结论 |
| 图 2 | Sellers Exploit the 'Exit Loophole' 4× More Without Warrant | RQ1 机制解释 |
| 图 4 | Under Pressure, Seller Chat Amplifies Deception — Warrant Provides Robust Defense | RQ2 核心结论 |
| 图 5 | Warrant Ensures Profit Comes from Honest Trade, Not Deception | RQ2 机制解释 |
| 图 7 | Buyer Communication Alone Can Suppress Deception Almost as Effectively as Warrant | RQ3 核心结论 |

### 附录图（机制解释，幻灯片可跳过）

- 图 3：Warrant Shifts Market Output to Authentic HQ（RQ1 质量结构）
- 图 6：Product Mix Shifts: Warrant Removes Counterfeit Supply（RQ2 质量结构）
- 图 8：Buyer Coordination Builds Gradually（RQ3 动态演化）

### 幻灯片展示建议

- 图 4 如果要在幻灯片里用，建议 **分 3 张幻灯片**，每张展示一个约束，逐步积累结论
- 图 1 建议把利润和欺骗分成 **两张独立幻灯片**，先讲利润，再讲欺骗，标题各自服务于不同结论
- 图 2 建议在展示时用动画 **逐步高亮** Exit Strategy 柱，先把其他漏洞置灰，再聚焦

---

## 5. 统计检验规划汇总

| 图 | 检验对象 | 检验方法 | 标注位置 |
|---|---|---|---|
| 图 1 | 利润 / 欺骗次数 | Mann-Whitney U | 柱顶 `***` |
| 图 2 | 各漏洞操纵检测率 | z-score（比例检验） | 差异显著的柱对间横线 + `*` |
| 图 4 | 各约束内欺骗次数 | Mann-Whitney U | 柱对间横线 + `*` |
| 图 5 | 诚实利润占比 | z-score（比例检验） | 柱顶 `*` |
| 图 7 | 有/无通信的欺骗次数 | Mann-Whitney U | 哑铃线旁 `*` |
| 图 8 | 每 round 欺骗次数 | Mann-Whitney U（逐轮） | 折线图各 round 上方 `*` |

---

## 6. 落地实现注意事项

- **Probe 数据位置**：`rq1/r_wo` 和 `rq1/rw_wo` 目录内有 `run_*_cognitive_probes.json`，不在独立的 `rq1_probe` 目录；脚本路径需要对应修改
- **条件分组依据**：以 `experiment_config.json` 的**顶层字段**（`market_type`、`communication_type`、`posts4seller`）为准，不用嵌套 `simulation_config` 内的字段（后者可能显示默认值）
- **可复用的已有函数**：`paper_data_utils.py` 中的 `market_run_stats_with_breakdown`、`product_quality_run_stats`、`aggregate_by_run` 可直接支持以上图的数据提取，只需新写绘图层

---

## 7. 建议的输出文件命名

文件名对应图的结论，而不是图的形式：

- `rq1_warrant_vs_rep_deception_and_profit.png`
- `rq1_exit_loophole_vulnerability.png`
- `rq2_seller_comm_deception_by_constraint.png`
- `rq2_profit_decomposition_honest_vs_dishonest.png`
- `rq3_buyer_comm_dumbbell.png`
- `rq1_product_mix_appendix.png`
- `rq2_product_mix_appendix.png`
- `rq3_round_adaptation_appendix.png`
