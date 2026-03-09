# 实验数据可视化和表格生成指南

本指南说明如何使用可视化脚本从实验数据库中提取数据并生成论文表格和图片。

## 目录结构

```
visualization/scripts/
├── export_results_from_db.py           # 从SQLite数据库导出结果到JSON
├── batch_export_results.sh             # 批量导出所有实验结果
├── generate_rq1_paper_tables.py        # 生成RQ1论文表格（包含认知探测数据）
├── generate_basic_comparison_tables.py # 生成基本比较表格（不需要认知探测数据）
├── generate_paper_figures.py           # 生成论文图片
├── run_paper_visualization_main.sh     # 主可视化脚本（一键生成所有表格和图片）
├── paper_table_generator.py            # LaTeX表格生成工具
└── README.md                           # 本文档
```

## 快速开始

### 完整流程（一键运行）

```bash
# 1. 导出所有实验结果
./visualization/scripts/batch_export_results.sh

# 2. 生成所有表格和图片
./visualization/scripts/run_paper_visualization_main.sh
```

### 单独运行各个步骤

#### 步骤1：导出数据

从SQLite数据库中导出市场结果数据：

```bash
# 导出所有实验结果
./visualization/scripts/batch_export_results.sh

# 或者导出单个实验目录
python3 visualization/scripts/export_results_from_db.py experiments/gpt-4o-mini/paper_largescale/rq1/r_wo
```

这将为每个实验目录中的每个 `run_*.db` 文件创建相应的 `run_*_results.json` 文件。

#### 步骤2：生成表格

**RQ1表格（包含认知探测分析）**

```bash
python3 visualization/scripts/generate_rq1_paper_tables.py \
    --r-market-dir experiments/gpt-4o-mini/paper_largescale/rq1/r_wo \
    --r-probe-dir experiments/gpt-4o-mini/paper_largescale/rq1/r_wo \
    --rw-market-dir experiments/gpt-4o-mini/paper_largescale/rq1/rw_wo \
    --rw-probe-dir experiments/gpt-4o-mini/paper_largescale/rq1/rw_wo \
    --output-dir visualization/table/paper/rq1
```

**RQ2/RQ3/RQ4基本比较表格**

```bash
python3 visualization/scripts/generate_basic_comparison_tables.py \
    --r-market-dir experiments/gpt-4o-mini/paper_largescale/rq2/r_wo \
    --rw-market-dir experiments/gpt-4o-mini/paper_largescale/rq2/rw_wo \
    --output-dir visualization/table/paper/rq2 \
    --table-prefix rq2
```

#### 步骤3：生成图片

```bash
python3 visualization/scripts/generate_paper_figures.py \
    --r-dir experiments/gpt-4o-mini/paper_largescale/rq1/r_wo \
    --rw-dir experiments/gpt-4o-mini/paper_largescale/rq1/rw_wo \
    --output-dir visualization/figs/gpt-4o-mini/paper_largescale
```

## 输出文件

### 表格

生成的LaTeX表格位于 `visualization/table/paper/`：

**RQ1 表格** (`rq1/`)
- `rq1_summary_stats.tex` - 汇总统计（交易量、利润、效用、声誉）
- `rq1_summary_comparison.tex` - 操纵检测比较（5种漏洞类型）
- `rq1_product_quality.tex` - 产品质量分析（真品/假货销售情况）

**RQ2 表格** (`rq2/`)
- `rq2_market_comparison.tex` - 市场结果比较

**RQ3 表格** (`rq3/`)
- `rq3_market_comparison.tex` - 卖家沟通条件下的市场比较

**RQ4 表格** (`rq4/`)
- `rq4_market_comparison.tex` - 买卖家沟通条件下的市场比较

### 图片

生成的PNG图片位于 `visualization/figs/gpt-4o-mini/paper_largescale/`：
- `round_evolution_comparison_pressure.png` - 关键市场指标的轮次演化图
  - 声誉演化
  - 交易量演化
  - 卖家利润演化
  - 买家效用演化

所有图片均为300 DPI高分辨率，适合直接用于论文。

## 实验目录结构

脚本期望以下实验目录结构：

```
experiments/gpt-4o-mini/paper_largescale/
├── rq1/                          # RQ1: 基础机制比较
│   ├── r_wo/                     # Reputation Only
│   │   ├── run_1.db
│   │   ├── run_1_cognitive_probes.json
│   │   ├── run_1_results.json    # 由导出脚本生成
│   │   ├── run_1_actions.json
│   │   └── ... (run_2-5)
│   └── rw_wo/                    # Reputation + Warrant
│       └── ...
├── rq2/                          # RQ2: 无沟通基准
│   ├── r_wo/
│   └── rw_wo/
├── rq3/                          # RQ3: 卖家沟通条件
│   ├── r_wsc_F/                  # Rep with Seller Comm (Fixed)
│   ├── r_wsc_R/                  # Rep with Seller Comm (Rational)
│   ├── rw_wsc_F/                 # Rep+Warrant with Seller Comm (Fixed)
│   ├── rw_wsc_R/                 # Rep+Warrant with Seller Comm (Rational)
│   ├── r_wsc_R_policy_making/    # 带政策约束
│   ├── r_wsc_R_pressure_quickprofits/  # 带快速盈利压力
│   ├── r_wsc_R_psychological-based-attack/  # 带心理攻击
│   └── ... (其他条件变体)
└── rq4/                          # RQ4: 买卖家沟通
    ├── r_wbc_F/
    ├── r_wbc_R/
    ├── rw_wbc_F/
    └── rw_wbc_R/
```

## 数据库结构

脚本从以下SQLite表中提取数据：

- **`user`** - 用户/代理信息
  - `user_id`, `agent_id`, `role` (seller/buyer)
  - `thumbs_up_count`, `thumbs_down_count` - 声誉评分
  - `budget`, `profit_utility_score` - 财务状态

- **`product`** - 产品列表和销售信息
  - `product_id`, `user_id` (seller)
  - `true_quality`, `advertised_quality` - 真实和广告质量
  - `price`, `cost`, `has_warrant` - 定价和保修信息
  - `is_sold`, `status`, `round_number` - 销售状态

- **`transactions`** - 交易详情
  - `transaction_id`, `product_id`, `seller_id`, `buyer_id`
  - `rating`, `is_challenged` - 评价和挑战
  - `seller_profit`, `buyer_utility` - 利润和效用

## 环境变量

- `EXPERIMENT_PREFIX` - 实验路径前缀（默认：`gpt-4o-mini/paper_largescale`）
  ```bash
  export EXPERIMENT_PREFIX="gpt-4o-mini/paper_largescale"
  ```

- `PYTHONPATH` - 确保包含项目根目录

## 故障排查

### 问题1：导出的结果为空

**现象**：`Exported 0 results to run_X_results.json`

**原因**：数据库可能没有产品数据或实验尚未完成。

**解决方案**：
```bash
# 检查数据库是否有数据
sqlite3 experiments/path/to/run_1.db "SELECT COUNT(*) FROM product;"

# 检查数据库表结构
sqlite3 experiments/path/to/run_1.db ".tables"
```

### 问题2：缺少认知探测数据

**现象**：`ERROR: No cognitive probe result files found`

**原因**：某些实验（如RQ2-RQ4）可能没有运行认知探测测试。

**解决方案**：
- RQ2-RQ4使用 `generate_basic_comparison_tables.py`（不需要probe数据）
- RQ1使用 `generate_rq1_paper_tables.py`（需要probe数据）

### 问题3：表格生成失败

**现象**：Python脚本报错

**原因**：可能缺少依赖包。

**解决方案**：
```bash
pip install pandas numpy matplotlib seaborn
```

### 问题4：JSON文件格式错误

**现象**：`json.decoder.JSONDecodeError`

**原因**：导出的JSON文件可能为空或格式错误。

**解决方案**：
```bash
# 重新导出数据
python3 visualization/scripts/export_results_from_db.py <experiment_dir>

# 检查JSON文件内容
head -20 <experiment_dir>/run_1_results.json
```

## 依赖包

```bash
pip install pandas numpy matplotlib seaborn
```

## 脚本说明

### `export_results_from_db.py`

从SQLite数据库导出市场结果到JSON格式。

**功能**：
- 从 `product`, `transactions`, `user` 表中提取数据
- 计算每个产品的利润、效用、声誉等指标
- 生成与表格生成脚本兼容的JSON格式

**输入**：`run_*.db` 文件
**输出**：`run_*_results.json` 文件

### `batch_export_results.sh`

批量导出所有实验目录的结果。

**功能**：
- 遍历所有RQ1-RQ4实验目录
- 调用 `export_results_from_db.py` 导出每个目录
- 生成完整的导出日志

### `generate_rq1_paper_tables.py`

生成RQ1的详细分析表格（需要认知探测数据）。

**输出表格**：
- 汇总统计表
- 操纵检测比较表
- 产品质量分析表

### `generate_basic_comparison_tables.py`

生成基本市场比较表格（不需要认知探测数据）。

**功能**：
- 比较Reputation vs Reputation+Warrant的市场指标
- 适用于RQ2-RQ4
- 只需要市场结果数据

### `generate_paper_figures.py`

生成论文用的可视化图片。

**功能**：
- 生成轮次演化对比图（4个子图）
- 学术风格（衬线字体、专业配色）
- 高分辨率输出（300 DPI）

### `run_paper_visualization_main.sh`

一键运行主脚本。

**功能**：
- 自动生成RQ1-RQ4所有表格
- 自动生成所有图片
- 复制结果到论文目录（如果存在）
- 生成完整的执行摘要

## 注意事项

1. **数据导出必须先于表格生成**：确保先运行 `batch_export_results.sh`。

2. **RQ4数据可能为空**：如果RQ4实验尚未运行或失败，导出的结果可能为空。这是正常的。

3. **认知探测数据是可选的**：
   - RQ1需要认知探测数据（`*_cognitive_probes.json`）
   - RQ2-RQ4不需要，可以只使用市场结果数据

4. **图片格式**：
   - 所有图片均为PNG格式，300 DPI
   - 适合直接用于论文发表
   - 如需PDF格式，可以使用matplotlib的savefig参数修改

5. **LaTeX表格**：
   - 使用 `\input{}` 命令在论文中引用表格文件
   - 需要在LaTeX preamble中包含 `\usepackage{booktabs}`

## 示例：在LaTeX中使用生成的表格

```latex
\documentclass{article}
\usepackage{booktabs}  % 必需

\begin{document}

% 引用RQ1汇总统计表
\input{visualization/table/paper/rq1/rq1_summary_stats.tex}

% 引用图片
\begin{figure}
    \centering
    \includegraphics[width=\textwidth]{visualization/figs/gpt-4o-mini/paper_largescale/round_evolution_comparison_pressure.png}
    \caption{Round Evolution Comparison}
\end{figure}

\end{document}
```

## 更新历史

- **2026-02-06**:
  - 创建数据导出脚本
  - 创建批量导出脚本
  - 创建基本比较表格生成器
  - 更新主可视化脚本以适配新的实验目录结构
  - 添加RQ4表格生成支持

## 联系方式

如有问题或建议，请在项目仓库中提交Issue。
