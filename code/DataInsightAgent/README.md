# DataInsightAgent

DataInsightAgent 已升级为 LangChain 1.x Agent。大模型负责理解自然语言任务和选择工具，现有 Python 分析函数负责确定性的数据清洗、统计检验、异常识别与大屏生成。

支持两个业务场景：

- A/B 测试：数据清洗、转化率比较、双样本比例 Z-test、置信区间和稳定性趋势。
- 退款异常归因：金额分布、退款原因贡献、促销表现及 IQR 高额异常分析。

## Agent 模式

先配置模型：

```powershell
$env:OPENAI_API_KEY="你的 API Key"
$env:DATA_INSIGHT_MODEL="gpt-4.1-mini"
```

如使用兼容 OpenAI API 的服务，可额外配置：

```powershell
$env:OPENAI_BASE_URL="https://your-endpoint.example/v1"
```

运行默认完整任务：

```powershell
python .\code\DataInsightAgent\run.py
```

提交自然语言任务：

```powershell
python .\code\DataInsightAgent\run.py "只分析 A/B 实验，不生成大屏，并解释 p 值"
python .\code\DataInsightAgent\run.py "先查看有哪些数据，再完成全部分析"
```

Agent 可自主调用以下工具：数据目录扫描、A/B 实验分析、退款异常分析、完整业务分析、最近摘要读取。最近一次 Agent 对话轨迹保存在 `output/agent_last_result.json`。

## 无模型批处理模式

不配置 API Key 也可以保留原有固定流程：

```powershell
python .\code\DataInsightAgent\run.py --batch
python .\code\DataInsightAgent\run.py --batch --no-dashboard
```

## 输出

- `output/ab_test_dashboard.html`
- `output/refund_anomaly_dashboard.html`
- `output/analysis_summary.json`
- `output/ab_analysis_summary.json`
- `output/refund_analysis_summary.json`
- `output/agent_last_result.json`
- `output/ab_group_summary.csv`
- `output/refund_reason_summary.csv`
- `output/refund_anomaly_records.csv`

Pyecharts 与 LangChain 依赖已放在项目自己的 `vendor/` 目录，入口会优先加载。生成的大屏内嵌 ECharts，可离线打开。

`vendor/` 中的二进制依赖适用于 Python 3.10。使用官方 Python 3.12 时，请先安装项目依赖：

```powershell
py -3.12 -m pip install -r .\code\DataInsightAgent\requirements.txt
```

默认统计口径：A/B 数据删除分组页面不匹配记录并按时间保留用户最早记录；使用双侧 Z-test，显著性水平 0.05；高额退款阈值为 `Q3 + 1.5 × IQR`。
