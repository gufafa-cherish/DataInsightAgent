from __future__ import annotations

import argparse
import json

from bootstrap import add_vendor_path

add_vendor_path()

from agent import run_agent
from pipeline import run_full_pipeline


DEFAULT_AGENT_PROMPT = (
    "请检查 data 目录中的业务数据，运行 A/B 测试和退款异常归因分析，"
    "生成需要的离线大屏，并给出面向业务负责人的关键结论与建议。"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DataInsightAgent：LangChain 数据分析 Agent"
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="交给 Agent 的自然语言任务；省略时运行默认完整分析任务",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="不调用大模型，按固定顺序执行两套分析",
    )
    parser.add_argument(
        "--model",
        help="覆盖 DATA_INSIGHT_MODEL / OPENAI_MODEL 配置",
    )
    parser.add_argument(
        "--base-url",
        help="覆盖 OPENAI_BASE_URL，适用于兼容 OpenAI API 的服务",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="批处理模式下 A/B 检验显著性水平，默认 0.05",
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="不生成 HTML 大屏",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="开启 LangChain Agent 调试输出",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.batch:
        result = run_full_pipeline(
            alpha=args.alpha,
            generate_dashboards=not args.no_dashboard,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    prompt = " ".join(args.prompt).strip() or DEFAULT_AGENT_PROMPT
    if args.no_dashboard:
        prompt += "\n本次不要生成 HTML 大屏。"
    answer = run_agent(
        prompt,
        model_name=args.model,
        base_url=args.base_url,
        debug=args.debug,
    )
    print(answer)


if __name__ == "__main__":
    main()
