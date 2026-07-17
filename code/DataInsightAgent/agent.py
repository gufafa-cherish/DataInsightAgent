from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from bootstrap import add_vendor_path

add_vendor_path()

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from agent_tools import DATA_INSIGHT_TOOLS
from config import (
    AGENT_RECURSION_LIMIT,
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    LAST_AGENT_RESULT_PATH,
)


SYSTEM_PROMPT = """你是 DataInsightAgent，一名严谨的中文业务数据分析 Agent。

你的职责是理解用户的分析目标，自主选择工具，并基于工具返回的真实结果给出结论。

工作规则：
1. 涉及数据内容、统计结果或产物状态时必须先调用工具，禁止猜测或编造数字。
2. 当文件或字段不明确时，先调用 list_available_datasets。
3. 用户要求同时分析 A/B 测试和退款异常时，优先调用 run_complete_business_analysis。
4. 用户只问单一场景时，调用对应的专项分析工具，避免无关计算。
5. 统计显著性不等于业务收益；解释 A/B 结果时同时说明效应方向、p 值和建议。
6. 解释退款异常时说明异常阈值、异常数量/占比、金额影响和主要归因。
7. 只有工具明确返回产物路径后，才能声称文件已经生成。
8. 最终回答使用中文，先给结论，再列关键指标和产物路径；不要暴露内部思维过程。
"""


def build_chat_model(
    model_name: str | None = None,
    base_url: str | None = None,
) -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "未检测到 OPENAI_API_KEY。请先配置环境变量，"
            "或使用 run.py --batch 执行不依赖模型的固定分析流程。"
        )
    kwargs: dict[str, Any] = {
        "model": model_name or DEFAULT_MODEL,
        "api_key": api_key,
        "temperature": 0,
        "max_retries": 2,
    }
    resolved_base_url = base_url or DEFAULT_BASE_URL
    if resolved_base_url:
        kwargs["base_url"] = resolved_base_url
    return ChatOpenAI(**kwargs)


def build_data_insight_agent(
    model: Any | None = None,
    *,
    model_name: str | None = None,
    base_url: str | None = None,
    debug: bool = False,
):
    chat_model = model or build_chat_model(model_name, base_url)
    return create_agent(
        model=chat_model,
        tools=DATA_INSIGHT_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        debug=debug,
        name="data_insight_agent",
    )


def _message_text(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text") or block.get("output_text")
                if text:
                    parts.append(str(text))
        return "\n".join(parts)
    return str(content)


def _message_trace(messages: list[Any]) -> list[dict[str, Any]]:
    trace = []
    for message in messages:
        item: dict[str, Any] = {
            "type": getattr(message, "type", message.__class__.__name__),
            "content": _message_text(message),
        }
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            item["tool_calls"] = tool_calls
        tool_name = getattr(message, "name", None)
        if tool_name:
            item["tool_name"] = tool_name
        trace.append(item)
    return trace


def run_agent(
    prompt: str,
    *,
    model_name: str | None = None,
    base_url: str | None = None,
    debug: bool = False,
) -> str:
    agent = build_data_insight_agent(
        model_name=model_name,
        base_url=base_url,
        debug=debug,
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config={"recursion_limit": AGENT_RECURSION_LIMIT},
    )
    messages = result.get("messages", [])
    if not messages:
        raise RuntimeError("Agent 未返回任何消息")
    final_answer = _message_text(messages[-1]).strip()
    audit = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": model_name or DEFAULT_MODEL,
        "prompt": prompt,
        "final_answer": final_answer,
        "message_trace": _message_trace(messages),
    }
    LAST_AGENT_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAST_AGENT_RESULT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return final_answer
