# -*- coding: utf-8 -*-
"""
尘安智眼 v4 —— 视觉结果检测框叠加（比赛演示的“第一眼震撼点”）
把大模型返回的归一化 bbox 直接画回原图：红/橙/黄框 + 隐患标签 + 危险值 + 顶部统计条。
纯 PIL 实现，无需 OpenCV，断网可用。
"""
from __future__ import annotations

import os
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from . import config as C

# Windows 常见中文字体，逐个尝试，全部失败则退回位图默认字体
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf", "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _font(size: int):
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _hex(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def draw_findings(image: Image.Image, result: dict[str, Any]) -> Image.Image:
    """在原图副本上绘制检测结果，返回新的 PIL.Image（RGB）。"""
    img = image.convert("RGB")
    W, H = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    findings = result.get("findings", []) or []

    line_w = max(3, int(W * 0.004))
    font = _font(max(16, int(W * 0.017)))
    font_small = _font(max(13, int(W * 0.013)))

    # 第一遍：画框；第二遍统一摆放标签并做标签防重叠
    boxes, occupied = [], []
    for f in findings:
        sev = (f.get("severity") or "YELLOW").upper()
        rgb = _hex(C.SEVERITY.get(sev, C.SEVERITY["YELLOW"])["hex"])
        bbox = f.get("bbox")
        label = f"{f.get('id','')} {f.get('item','隐患')} · 危险值{f.get('danger_level','?')}"
        rect = None
        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            try:
                x1 = max(0, min(999, int(bbox[0]))) / 999 * W
                y1 = max(0, min(999, int(bbox[1]))) / 999 * H
                x2 = max(0, min(999, int(bbox[2]))) / 999 * W
                y2 = max(0, min(999, int(bbox[3]))) / 999 * H
                if x2 > x1 and y2 > y1:
                    draw.rectangle([x1, y1, x2, y2], fill=rgb + (28,),
                                   outline=rgb + (255,), width=line_w)
                    rect = (x1, y1, x2, y2)
                else:
                    _draw_corner_legend(draw, font_small, f, rgb, W, H)
            except (TypeError, ValueError):
                _draw_corner_legend(draw, font_small, f, rgb, W, H)
        else:
            _draw_corner_legend(draw, font_small, f, rgb, W, H)
        boxes.append((rect, label, rgb, f))

    for rect, label, rgb, f in boxes:
        if rect is not None:
            _place_label(draw, font, rect, label, rgb, occupied, W, H)

    out = Image.alpha_composite(img.convert("RGBA"), overlay)
    out = _draw_top_banner(out.convert("RGB"), result, font, font_small)
    return out


def _rects_overlap(a, b, gap: int = 6) -> bool:
    return not (a[2] + gap < b[0] or b[2] + gap < a[0] or
                a[3] + gap < b[1] or b[3] + gap < a[1])


def _place_label(draw, font, box, text, rgb, occupied, W, H):
    """在检测框四周挑选不与已有标签重叠的位置摆放标签。"""
    pad = 5
    tb = draw.textbbox((0, 0), text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    x1, y1, x2, y2 = box
    lw, lh = tw + 2 * pad, th + 2 * pad
    candidates = [
        (x1, max(0, y1 - lh - 3)),            # 框上方（首选）
        (x1, min(y1 + 5, H - lh)),            # 框内顶部
        (max(0, x2 - lw), min(y2 - lh - 4, H - lh)),  # 框内右下角
        (x1, min(y2 - lh - 4, H - lh)),       # 框内左下角
    ]
    for x, y in candidates:
        rect = (x, y, x + lw, y + lh)
        if not any(_rects_overlap(rect, r) for r in occupied):
            draw.rectangle(rect, fill=rgb + (235,))
            draw.text((x + pad, y + pad), text, fill=(255, 255, 255, 255), font=font)
            occupied.append(rect)
            return
    # 兜底：直接画在框上方（允许重叠也不丢失信息）
    x, y = x1, max(0, y1 - lh - 3)
    draw.rectangle((x, y, x + lw, y + lh), fill=rgb + (235,))
    draw.text((x + pad, y + pad), text, fill=(255, 255, 255, 255), font=font)
    occupied.append((x, y, x + lw, y + lh))


def _draw_corner_legend(draw, font, finding, rgb, W, H):
    """无 bbox 时在右上角列出口头定位的隐患（不遮挡画面）。"""
    text = f"{finding.get('id','')} {finding.get('item','')}（{finding.get('location_desc','方位未明')}）"
    draw.text((W * 0.02, H * 0.92), text, fill=rgb + (255,), font=font)


def _draw_top_banner(img: Image.Image, result: dict, font, font_small) -> Image.Image:
    """顶部信息条：统计 + 一句话结论。注意 PIL 常规字体不含彩色 emoji，统一用中文。"""
    stats = result.get("stats", {}) or {}
    overall = result.get("overall", {}) or {}
    level = (overall.get("risk_level") or "GREEN").upper()
    rgb = _hex(C.SEVERITY.get(level, C.SEVERITY["GREEN"])["hex"])
    banner = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(banner)
    W, H = img.size
    bh = int(H * 0.115)
    d.rectangle([0, 0, W, bh], fill=(15, 23, 42, 220))
    txt = (f"AI 视觉巡检    红线 {stats.get('red', 0)} 项   黄线 {stats.get('orange', 0)} 项   "
           f"提醒 {stats.get('yellow', 0)} 项    综合风险分 {overall.get('risk_score', 0)}/100")
    d.text((16, 10), txt, fill=(255, 255, 255, 255), font=font)
    headline = overall.get("headline", "")
    if headline:
        line2_y = 12 + max(16, int(W * 0.017)) + 8
        max_chars = max(24, int(W / (max(13, int(W * 0.013)) * 1.1)))
        d.text((16, line2_y), headline[:max_chars * 2], fill=rgb + (255,), font=font_small)
    return Image.alpha_composite(img.convert("RGBA"), banner).convert("RGB")
