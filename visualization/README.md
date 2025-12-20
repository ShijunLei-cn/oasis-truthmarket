# Visualization Module

模块化的可视化分析工具，用于分析市场仿真结果。

## 目录结构

```
visualization/
├── core/                      # 核心模块
│   ├── __init__.py           # 模块导出
│   ├── utils.py              # 工具函数
│   ├── data_loader.py        # 数据加载模块
│   ├── statistics.py         # 统计计算模块
│   ├── plotters.py           # 绘图模块
│   ├── single_run_analysis.py  # 单次运行分析
│   ├── multi_run_analysis.py   # 多次运行分析
│   └── comparison_analysis.py  # 比较分析
├── analyze_single.py         # 单次运行分析命令行接口
├── analyze_multi.py          # 多次运行分析命令行接口
├── compare_experiments.py    # 比较分析命令行接口
├── plot_communication_effects.py  # 通信效果可视化命令行接口
└── run_visul.sh              # 便捷脚本
```

## 使用方法

### 1. 使用便捷脚本（推荐）

```bash
# 分析单次运行
./visualization/run_visul.sh single experiments/exp_123/run_1.db

# 分析多次运行实验
./visualization/run_visul.sh multi exp_20251216_120000

# 比较两个实验
./visualization/run_visul.sh compare reputation_only:exp_123 reputation_warrant:exp_456

# 使用配置文件进行比较
./visualization/run_visul.sh compare-config comparison_config.json
```

### 2. 使用 Python 命令行接口

```bash
# 分析单次运行
python3 visualization/analyze_single.py experiments/exp_123/run_1.db

# 分析多次运行
python3 visualization/analyze_multi.py --experiment-id exp_20251216_120000

# 比较实验
python3 visualization/compare_experiments.py \
    --exp reputation_only:exp_123 \
    --exp reputation_warrant:exp_456

# 可视化通信效果（rep-only市场）
python3 visualization/plot_communication_effects.py \
    --experiments-dir experiments \
    --output experiments/communication_effects_rep_only.png
```

### 3. 使用 Python API

```python
from visualization.core import (
    analyze_single_run,
    MultiRunAnalyzer,
    ComparisonAnalyzer
)

# 分析单次运行
analyze_single_run('experiments/exp_123/run_1.db')

# 分析多次运行
analyzer = MultiRunAnalyzer('exp_20251216_120000')
analyzer.load_data()
stats = analyzer.generate_aggregated_statistics()
analyzer.save_aggregated_results()

# 比较实验
from visualization.core.comparison_analysis import compare_experiments
compare_experiments({
    'reputation_only': 'exp_123',
    'reputation_warrant': 'exp_456'
})
```

## 功能模块

### 数据加载 (`data_loader.py`)

- `DataLoader`: 加载单个数据库文件
- `ExperimentDataLoader`: 加载多次运行实验数据

### 统计计算 (`statistics.py`)

- `StatisticsCalculator`: 计算聚合统计信息、欺骗行为统计等

### 绘图 (`plotters.py`)

- `ReputationPlotter`: 声誉相关图表
- `PricePlotter`: 价格相关图表
- `ActionPlotter`: 行为相关图表
- `ManipulationPlotter`: 操纵行为图表

### 单次运行分析 (`single_run_analysis.py`)

- `SingleRunAnalyzer`: 分析单个仿真运行
- `analyze_single_run()`: 便捷函数

### 多次运行分析 (`multi_run_analysis.py`)

- `MultiRunAnalyzer`: 分析多次运行实验
- 生成聚合统计和可视化

### 比较分析 (`comparison_analysis.py`)

- `ComparisonAnalyzer`: 比较不同实验的结果
- `compare_experiments()`: 便捷函数

### 通信效果可视化 (`communication_effects.py`)

- `create_communication_effects_plot()`: 创建通信效果对比图
- 对比4种通信条件（无通信、买家通信、卖家通信、双向通信）
- 生成6个子图：卖家利润、买家效用、不诚实产品数量、交易评分、交易数量、总收益
- 使用带阴影区域的折线图显示均值±标准差

## 配置文件格式

比较分析配置文件（JSON）：

```json
{
  "reputation_only": "exp_20251216_120000",
  "reputation_warrant": "exp_20251216_130000"
}
```

## 输出目录

- 单次运行分析：`analysis/outputs/<timestamp>/`
- 多次运行分析：`experiments/<experiment_id>/analysis/aggregated/`
- 比较分析：`analysis/comparison_<timestamp>/`

## 依赖

- pandas
- numpy
- matplotlib
- seaborn

## 注意事项

1. 确保数据库文件路径正确
2. 实验 ID 格式应为：`exp_YYYYMMDD_HHMMSS`
3. 配置文件使用 UTF-8 编码
