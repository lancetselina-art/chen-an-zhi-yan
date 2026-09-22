# -*- coding: utf-8 -*-
"""
尘安智眼 v4 —— 结构化结果 → Markdown 报告（用于下载归档与整改工单）
"""
from __future__ import annotations

from datetime import datetime

from . import config as C


def _sev(level: str) -> str:
    s = C.SEVERITY.get((level or "").upper())
    return f"{s['emoji']} {s['name']}" if s else level


def vision_to_markdown(data: dict, context: dict) -> str:
    o = data.get("overall", {})
    lines = [
        "# 🏗️ 尘安智眼 · 现场视觉巡检报告",
        f"\n**生成时间**：{datetime.now():%Y-%m-%d %H:%M:%S}",
        f"**施工阶段**：{context.get('stage','')}　**作业类型**：{context.get('work_type','')}"
        f"　**时段**：{'夜间' if context.get('is_night') else '昼间'}",
        f"**综合结论**：{_sev(o.get('risk_level'))}（风险分 {o.get('risk_score','-')}/100）　{o.get('disposition','')}",
        f"\n> {o.get('headline','')}",
        "\n| 序号 | 隐患项 | 分类 | 等级 | 危险值 | 置信度 | 位置 | 违反标准 | 整改要求 | 时限 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for f in data.get("findings", []):
        refs = "；".join(r.get("code", "") for r in f.get("standard_refs", []))
        rect = f.get("rectification", {})
        lines.append(
            f"| {f.get('id','')} | {f.get('item','')} | {f.get('category_code','')} | {_sev(f.get('severity'))} "
            f"| {f.get('danger_level','')} | {f.get('confidence','')} | {f.get('location_desc','')} "
            f"| {refs} | {rect.get('action','')} | {rect.get('deadline_hours','')}h |")
    for f in data.get("findings", []):
        refs = "；".join(r.get("code", "") for r in f.get("standard_refs", []))
        rect = f.get("rectification", {})
        lines += [
            f"\n## {f.get('id','')} {_sev(f.get('severity'))} {f.get('item','')}",
            f"- **画面证据**：{f.get('visual_evidence','')}",
            f"- **事故链分析**：{f.get('accident_chain','')}",
            f"- **依据**：{refs}",
            f"- **整改**：{rect.get('action','')}（责任人：{rect.get('responsible','')}，{rect.get('deadline_hours','')}h 内）",
        ]
        if rect.get("voice_prompt"):
            lines.append(f"- **现场语音提示**：{rect['voice_prompt']}")
    if data.get("uncertainties"):
        lines.append("\n## 复检与不确定项")
        lines += [f"- {u}" for u in data["uncertainties"]]
    lines.append("\n---\n*本报告由尘安智眼自动生成，环保类结论依据知识库现行规范，安全类结论需安全员现场复核。*")
    return "\n".join(lines)


def sensor_to_markdown(data: dict, features: dict, context: dict) -> str:
    o = data.get("overall", {})
    lines = [
        "# 🌡️ 尘安智眼 · 传感器数据研判报告",
        f"\n**生成时间**：{datetime.now():%Y-%m-%d %H:%M:%S}",
        f"**监测时段**：{features.get('time_range','')}　**城市**：{context.get('city','')}",
        f"**施工阶段**：{context.get('stage','')}　**作业类型**：{context.get('work_type','')}",
        f"**综合结论**：{_sev(o.get('risk_level'))}（风险分 {o.get('risk_score','-')}/100）　{o.get('disposition','')}",
        f"\n> {o.get('headline','')}",
        "\n## 一、预警清单",
    ]
    for w in data.get("warnings", []):
        lines.append(f"- {_sev(w.get('level'))} **【{w.get('metric','')}】{w.get('title','')}**：{w.get('detail','')}")
    lines.append("\n## 二、分项研判")
    for m in data.get("metric_reports", []):
        lines += [
            f"\n### {m.get('metric_name','')}（{_sev(m.get('level'))}，趋势 {m.get('trend','')}）",
            f"- 当前 {m.get('current')} {m.get('unit','')}，限值 {m.get('threshold')} {m.get('unit','')}",
            f"- 趋势证据：{m.get('trend_evidence','')}",
            f"- 机理解读：{m.get('physical_mechanism','')}",
            f"- 处置：{'；'.join(m.get('actions', []))}",
        ]
    if data.get("coupled_synthesis"):
        lines += ["\n## 三、多因子耦合研判", data["coupled_synthesis"]]
    pw = data.get("process_window", {})
    if pw:
        cp, ow = pw.get("concrete_pouring", {}), pw.get("outdoor_work", {})
        lines.append("\n## 四、工艺窗口")
        if cp:
            lines.append(f"- **混凝土浇筑**：{'适宜' if cp.get('suitable') else '不适宜'} — {cp.get('reason','')}；"
                         f"措施：{'；'.join(cp.get('measures', []))}")
        if ow:
            lines.append(f"- **室外露天作业**：{'适宜' if ow.get('suitable') else '受限'} — {ow.get('reason','')}；"
                         f"措施：{'；'.join(ow.get('measures', []))}")
    if data.get("forecast"):
        lines += ["\n## 五、趋势外推", data["forecast"]]
    lines.append("\n---\n*数值结论由程序按现行规范确定性计算，机理研判由大模型生成，存档请以监测原始数据为准。*")
    return "\n".join(lines)
