from pathlib import Path

from pyecharts import options as opts
from pyecharts.charts import Bar, Line, Pie

from dashboard_common import axis_opts, chart_init, render_dashboard


BLUE, GREEN, ORANGE, RED = "#4dc3ff", "#79e2c6", "#ffb86b", "#ff6b7a"


def build_refund_dashboard(result: dict, output_path: Path) -> None:
    histogram = result["histogram"]
    distribution_chart = (
        Bar(init_opts=chart_init())
        .add_xaxis(histogram["range"].tolist())
        .add_yaxis("退款笔数", histogram["count"].astype(int).tolist(), category_gap="18%",
            itemstyle_opts=opts.ItemStyleOpts(color=BLUE), label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(name="退款金额区间（元）",
                axislabel_opts=opts.LabelOpts(color="#b7c7dc",rotate=25),
                axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(color="#35506f"))),
            yaxis_opts=axis_opts("退款笔数"), legend_opts=opts.LegendOpts(is_show=False))
    )

    reasons = result["reason_summary"].sort_values("refund_amount",ascending=True)
    reason_chart = (
        Bar(init_opts=chart_init("410px"))
        .add_xaxis(reasons.refund_reason.tolist())
        .add_yaxis("退款金额",reasons.refund_amount.round(2).tolist(),
            itemstyle_opts=opts.ItemStyleOpts(color=GREEN),
            label_opts=opts.LabelOpts(is_show=True,position="right",formatter="¥{c}"))
        .reversal_axis()
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis",axis_pointer_type="shadow"),
            xaxis_opts=axis_opts("退款金额（元）"),
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#b7c7dc")),
            legend_opts=opts.LegendOpts(is_show=False))
    )
    reason_pie = (
        Pie(init_opts=chart_init("410px"))
        .add("退款笔数占比",[(row.refund_reason,int(row.refund_count)) for _,row in result["reason_summary"].iterrows()],
            radius=["38%","68%"],center=["50%","50%"])
        .set_global_opts(legend_opts=opts.LegendOpts(orient="vertical",pos_left="2%",pos_top="12%",
            textstyle_opts=opts.TextStyleOpts(color="#c5d4e5")))
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}\n{d}%",color="#dce8f5"))
    )

    promo = result["promo_summary"]
    promo_chart = (
        Bar(init_opts=chart_init())
        .add_xaxis(promo.promo_name.tolist())
        .add_yaxis("退款笔数",promo.refund_count.astype(int).tolist(),
            itemstyle_opts=opts.ItemStyleOpts(color=BLUE),label_opts=opts.LabelOpts(is_show=True,position="top"))
        .extend_axis(yaxis=opts.AxisOpts(name="平均退款额（元）",axislabel_opts=opts.LabelOpts(color="#b7c7dc")))
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis"),xaxis_opts=axis_opts(),
            yaxis_opts=axis_opts("退款笔数"),
            legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="#c5d4e5")))
    )
    promo_line = (Line().add_xaxis(promo.promo_name.tolist())
        .add_yaxis("平均退款额",promo.avg_refund_amount.round(2).tolist(),yaxis_index=1,
            symbol="diamond",symbol_size=10,linestyle_opts=opts.LineStyleOpts(width=3,color=ORANGE),
            itemstyle_opts=opts.ItemStyleOpts(color=ORANGE),label_opts=opts.LabelOpts(is_show=True,formatter="¥{c}")))
    promo_chart.overlap(promo_line)

    daily = result["daily_summary"]
    daily_chart = (
        Bar(init_opts=chart_init("390px"))
        .add_xaxis(daily.refund_date.tolist())
        .add_yaxis("退款金额",daily.refund_amount.round(2).tolist(),
            itemstyle_opts=opts.ItemStyleOpts(color="#315d82",opacity=.7),label_opts=opts.LabelOpts(is_show=False))
        .extend_axis(yaxis=opts.AxisOpts(name="退款笔数",axislabel_opts=opts.LabelOpts(color="#b7c7dc")))
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis"),xaxis_opts=axis_opts("退款日期"),
            yaxis_opts=axis_opts("退款金额（元）"),datazoom_opts=[opts.DataZoomOpts(type_="inside")],
            legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="#c5d4e5")))
    )
    daily_line = (Line().add_xaxis(daily.refund_date.tolist())
        .add_yaxis("退款笔数",daily.refund_count.astype(int).tolist(),yaxis_index=1,is_smooth=True,symbol="none",
            linestyle_opts=opts.LineStyleOpts(width=3,color=GREEN),label_opts=opts.LabelOpts(is_show=False)))
    daily_chart.overlap(daily_line)

    anomaly_reasons = result["anomaly_reason_summary"].sort_values("refund_count",ascending=True)
    anomaly_chart = (
        Bar(init_opts=chart_init("390px"))
        .add_xaxis(anomaly_reasons.refund_reason.tolist())
        .add_yaxis("异常笔数",anomaly_reasons.refund_count.astype(int).tolist(),
            itemstyle_opts=opts.ItemStyleOpts(color=RED),label_opts=opts.LabelOpts(is_show=True,position="right"))
        .reversal_axis()
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis",axis_pointer_type="shadow"),
            xaxis_opts=axis_opts("异常退款笔数"),
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#b7c7dc")),
            legend_opts=opts.LegendOpts(is_show=False))
    )

    metrics = [
        {"label":"累计退款金额","value":f"¥{result['total_refund_amount']:,.0f}","detail":f"共 {result['clean_rows']:,} 笔退款"},
        {"label":"平均退款金额","value":f"¥{result['average_refund_amount']:.2f}","detail":f"中位数 ¥{result['median_refund_amount']:.2f}"},
        {"label":"高额异常退款","value":f"{result['anomaly_count']} 笔","detail":f"占全部退款 {result['anomaly_rate']:.2%}"},
        {"label":"异常金额贡献","value":f"{result['anomaly_amount_share']:.2%}","detail":f"IQR 阈值 ¥{result['iqr_upper_fence']:.2f}"},
    ]
    sections = [
        {"title":"退款金额分布","caption":f"P95=¥{result['p95']:.0f}，P99=¥{result['p99']:.0f}，最大值=¥{result['amount_max']:.0f}","chart":distribution_chart},
        {"title":"退款原因笔数占比","caption":"识别最常见的退款动因","chart":reason_pie},
        {"title":"退款原因金额贡献","caption":"按退款金额排序，衡量各原因的资金影响","chart":reason_chart},
        {"title":"促销活动退款表现","caption":"同时比较退款笔数与平均退款金额","chart":promo_chart},
        {"title":"退款时间趋势","caption":"按退款日期观察金额与笔数的同步变化","chart":daily_chart,"wide":True},
        {"title":"高额异常退款原因","caption":f"展示超过 IQR 上界 ¥{result['iqr_upper_fence']:.2f} 的异常记录","chart":anomaly_chart,"wide":True},
    ]
    insights = [
        f"退款金额主要集中在 ¥{result['q1']:.2f}–¥{result['q3']:.2f}，高额异常阈值为 ¥{result['iqr_upper_fence']:.2f}。",
        f"最主要退款原因是“{result['top_reason']}”，占退款笔数 {result['top_reason_count_share']:.2%}、退款金额 {result['top_reason_amount_share']:.2%}。",
        f"高额异常退款共 {result['anomaly_count']} 笔，金额合计 ¥{result['anomaly_amount']:,.2f}。",
        f"退款商品只有 {result['product_unique_count']} 个品类，商品维度不具备区分度，应重点关注促销、原因、退款数量和退款时延。",
        f"订单到退款的中位时延为 {result['median_refund_delay_minutes']:.1f} 分钟。",
    ]
    render_dashboard(output_path,"退款异常归因分析大屏","DataInsightAgent · 金额分布、原因贡献与高额异常特征",
        metrics,sections,"异常归因结论",insights)
