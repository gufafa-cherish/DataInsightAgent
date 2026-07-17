from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
import re
from typing import Iterable

from pyecharts import options as opts
from pyecharts.globals import ThemeType


ECHARTS_BUNDLE = Path(__file__).resolve().parent / "vendor" / "echarts.min.js"


def chart_init(height: str = "340px") -> opts.InitOpts:
    return opts.InitOpts(
        width="100%", height=height, theme=ThemeType.DARK,
        bg_color="transparent",
        animation_opts=opts.AnimationOpts(animation_duration=500),
    )


def axis_opts(name: str = "") -> opts.AxisOpts:
    return opts.AxisOpts(
        name=name,
        axislabel_opts=opts.LabelOpts(color="#b7c7dc"),
        axisline_opts=opts.AxisLineOpts(
            linestyle_opts=opts.LineStyleOpts(color="#35506f")
        ),
        splitline_opts=opts.SplitLineOpts(
            is_show=True,
            linestyle_opts=opts.LineStyleOpts(color="#203752", opacity=0.55),
        ),
    )


def chart_embed(chart) -> str:
    """Return chart markup without Pyecharts' repeated remote ECharts loader."""
    embedded = chart.render_embed()
    return re.sub(
        r'<script[^>]+src=["\'][^"\']+["\'][^>]*></script>',
        "",
        embedded,
        flags=re.IGNORECASE,
    )


def render_dashboard(
    output_path: Path,
    title: str,
    subtitle: str,
    metrics: Iterable[dict[str, str]],
    sections: Iterable[dict],
    insight_title: str,
    insights: Iterable[str],
) -> None:
    metric_html = "".join(
        "<article class='metric-card'>"
        f"<div class='metric-label'>{escape(item['label'])}</div>"
        f"<div class='metric-value'>{escape(item['value'])}</div>"
        f"<div class='metric-detail'>{escape(item.get('detail', ''))}</div>"
        "</article>" for item in metrics
    )
    section_html = "".join(
        f"<section class='chart-panel {'wide' if item.get('wide') else ''}'>"
        f"<h2>{escape(item['title'])}</h2>"
        f"<p>{escape(item.get('caption', ''))}</p>"
        f"{chart_embed(item['chart'])}"
        "</section>" for item in sections
    )
    insight_html = "".join(f"<li>{escape(text)}</li>" for text in insights)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not ECHARTS_BUNDLE.exists():
        raise FileNotFoundError(f"缺少离线 ECharts 运行库: {ECHARTS_BUNDLE}")
    echarts_javascript = ECHARTS_BUNDLE.read_text(encoding="utf-8").replace(
        "</script>", "<\\/script>"
    )
    document = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <script>{echarts_javascript}</script>
  <style>
    :root {{ color-scheme: dark; --bg:#07111f; --panel:#0e1f34; --border:rgba(85,143,198,.28); --text:#e8f1fb; --muted:#96abc2; --accent:#4dc3ff; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; min-width:320px; background:radial-gradient(circle at 12% 0%,rgba(27,93,150,.25),transparent 34%),radial-gradient(circle at 88% 6%,rgba(24,145,133,.18),transparent 28%),var(--bg); color:var(--text); font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif; }}
    .dashboard {{ max-width:1880px; margin:0 auto; padding:24px; }}
    .header {{ display:flex; justify-content:space-between; gap:24px; align-items:flex-end; padding:4px 4px 20px; border-bottom:1px solid var(--border); }}
    h1 {{ margin:0 0 8px; font-size:clamp(24px,2.3vw,42px); font-weight:600; }}
    .subtitle,.generated,.chart-panel p,.metric-detail {{ color:var(--muted); }}
    .subtitle {{ margin:0; }} .generated {{ white-space:nowrap; font-size:13px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:14px; margin:20px 0; }}
    .metric-card,.chart-panel,.insight-panel {{ background:linear-gradient(145deg,rgba(17,38,63,.96),rgba(9,24,42,.94)); border:1px solid var(--border); border-radius:14px; box-shadow:0 12px 32px rgba(0,0,0,.18); }}
    .metric-card {{ padding:18px; min-height:126px; }} .metric-label {{ color:var(--muted); font-size:14px; }}
    .metric-value {{ margin:12px 0 8px; color:var(--accent); font-size:30px; font-weight:600; }} .metric-detail {{ font-size:13px; }}
    .grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; }}
    .chart-panel {{ padding:18px; min-width:0; overflow:hidden; }} .chart-panel.wide {{ grid-column:1/-1; }}
    .chart-panel h2,.insight-panel h2 {{ margin:0 0 6px; font-size:18px; font-weight:600; }}
    .chart-panel p {{ margin:0 0 8px; min-height:20px; font-size:13px; }}
    .insight-panel {{ margin-top:16px; padding:20px 24px; }} .insight-panel ul {{ margin:12px 0 0; padding-left:22px; display:grid; gap:8px; color:#c9d8e8; }}
    @media (max-width:900px) {{ .dashboard {{ padding:14px; }} .header {{ align-items:flex-start; flex-direction:column; }} .grid {{ grid-template-columns:1fr; }} .chart-panel.wide {{ grid-column:auto; }} .generated {{ white-space:normal; }} }}
  </style>
</head>
<body>
  <main class="dashboard">
    <header class="header"><div><h1>{escape(title)}</h1><p class="subtitle">{escape(subtitle)}</p></div><div class="generated">生成时间：{generated_at}</div></header>
    <section class="metrics">{metric_html}</section>
    <section class="grid">{section_html}</section>
    <section class="insight-panel"><h2>{escape(insight_title)}</h2><ul>{insight_html}</ul></section>
  </main>
  <script>window.addEventListener('resize',function(){{document.querySelectorAll('[_echarts_instance_]').forEach(function(el){{var instance=echarts.getInstanceByDom(el);if(instance)instance.resize();}});}});</script>
</body>
</html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
