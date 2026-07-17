from pathlib import Path

from pyecharts import options as opts
from pyecharts.charts import Bar, Line

from dashboard_common import axis_opts, chart_init, render_dashboard


CONTROL_COLOR = "#4dc3ff"
TREATMENT_COLOR = "#79e2c6"


def build_ab_dashboard(result: dict, output_path: Path) -> None:
    group = result["group_summary"]
    labels = ["对照组", "实验组"]
    rates = (group.conversion_rate * 100).round(3).tolist()
    samples = group.sample_size.astype(int).tolist()
    conversions = group.conversions.astype(int).tolist()

    conversion_chart = (
        Bar(init_opts=chart_init())
        .add_xaxis(labels)
        .add_yaxis("转化率", rates, category_gap="45%",
            itemstyle_opts=opts.ItemStyleOpts(color=CONTROL_COLOR),
            label_opts=opts.LabelOpts(is_show=True, position="top", formatter="{c}%"))
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=axis_opts(), yaxis_opts=axis_opts("转化率（%）"),
            legend_opts=opts.LegendOpts(is_show=False))
    )
    sample_chart = (
        Bar(init_opts=chart_init())
        .add_xaxis(labels)
        .add_yaxis("未转化", [samples[i]-conversions[i] for i in range(2)], stack="total",
            itemstyle_opts=opts.ItemStyleOpts(color="#355d82"))
        .add_yaxis("已转化", conversions, stack="total",
            itemstyle_opts=opts.ItemStyleOpts(color=TREATMENT_COLOR))
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
            xaxis_opts=axis_opts(), yaxis_opts=axis_opts("用户数"),
            legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="#c5d4e5")))
    )

    daily = result["daily_rates"]
    daily_chart = (
        Line(init_opts=chart_init("380px"))
        .add_xaxis(daily.date.tolist())
        .add_yaxis("对照组", (daily.control*100).round(3).tolist(), is_smooth=True,
            symbol="circle", symbol_size=6,
            linestyle_opts=opts.LineStyleOpts(width=2,color=CONTROL_COLOR),
            itemstyle_opts=opts.ItemStyleOpts(color=CONTROL_COLOR), label_opts=opts.LabelOpts(is_show=False))
        .add_yaxis("实验组", (daily.treatment*100).round(3).tolist(), is_smooth=True,
            symbol="diamond", symbol_size=6,
            linestyle_opts=opts.LineStyleOpts(width=2,color=TREATMENT_COLOR),
            itemstyle_opts=opts.ItemStyleOpts(color=TREATMENT_COLOR), label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis"), xaxis_opts=axis_opts("日期"),
            yaxis_opts=axis_opts("转化率（%）"), datazoom_opts=[opts.DataZoomOpts(type_="inside")],
            legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="#c5d4e5")))
    )
    cumulative = result["cumulative_rates"]
    cumulative_chart = (
        Line(init_opts=chart_init("380px"))
        .add_xaxis(cumulative.date.tolist())
        .add_yaxis("对照组累计转化率", (cumulative.control*100).round(3).tolist(), is_smooth=True,
            symbol="none", linestyle_opts=opts.LineStyleOpts(width=3,color=CONTROL_COLOR), label_opts=opts.LabelOpts(is_show=False))
        .add_yaxis("实验组累计转化率", (cumulative.treatment*100).round(3).tolist(), is_smooth=True,
            symbol="none", linestyle_opts=opts.LineStyleOpts(width=3,color=TREATMENT_COLOR), label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis"), xaxis_opts=axis_opts("日期"),
            yaxis_opts=axis_opts("累计转化率（%）"),
            legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="#c5d4e5")))
    )

    metrics = [
        {"label":"对照组转化率","value":f"{result['control_rate']:.3%}","detail":f"样本 {samples[0]:,}"},
        {"label":"实验组转化率","value":f"{result['treatment_rate']:.3%}","detail":f"样本 {samples[1]:,}"},
        {"label":"相对提升率","value":f"{result['relative_lift']:+.2%}","detail":f"绝对差异 {result['absolute_difference']:+.3%}"},
        {"label":"双侧 Z-test","value":"显著" if result['significant'] else "不显著","detail":f"p={result['p_value']:.4f}，z={result['z_score']:.3f}"},
    ]
    sections = [
        {"title":"分组转化率对比","caption":"实验组与对照组的整体转化率","chart":conversion_chart},
        {"title":"样本与转化构成","caption":"清洗后两组样本量及已转化用户数","chart":sample_chart},
        {"title":"每日转化率趋势","caption":"观察实验期间两组波动与稳定性","chart":daily_chart,"wide":True},
        {"title":"累计转化率收敛","caption":"判断实验结果是否随样本累积趋于稳定","chart":cumulative_chart,"wide":True},
    ]
    insights = [
        f"清洗后有效样本 {result['clean_rows']:,} 条；剔除分组页面不匹配 {result['mismatch_rows']:,} 条、重复用户 {result['duplicate_rows_removed']:,} 条。",
        f"转化率差异的 95% 置信区间为 [{result['ci_low']:.3%}, {result['ci_high']:.3%}]。",
        result["conclusion"], result["recommendation"],
    ]
    render_dashboard(output_path,"A/B 测试决策大屏","DataInsightAgent · 转化率、显著性检验与实验稳定性",
        metrics,sections,"统计结论与业务建议",insights)

