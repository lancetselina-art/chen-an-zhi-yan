# -*- coding: utf-8 -*-
"""
尘安智眼 v4 —— 知识库联动模块
解决旧版“全量知识库原样拼进 Prompt”的问题：
  1. 双源加载：优先本地 knowledge/，可选从 GitHub raw 实时同步（带超时与降级）；
  2. 规则精要（Digest）：只抽取限值表与 IF 判定规则等“可执行知识”，叙述性条文不进 Prompt；
  3. 隐患→法条映射：视觉结果返回 category_code 后，按 config.HAZARD_CATALOG 精确召回
     对应知识库全文，在界面“规范依据”面板逐条展示（先压缩注入、再按需召回的轻量 RAG，可离线复现）；
  4. 关键词检索：知识库 Tab 的搜索框复用同一套打分逻辑。
"""
from __future__ import annotations

import os
import re
import glob
from functools import lru_cache

import requests

from . import config as C

KB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge")


# ============================ 一、加载 ============================
@lru_cache(maxsize=2)
def load_local_kb(kb_dir: str = KB_DIR):
    """加载本地知识库，返回 {文件名: 内容}（按文件名排序）。"""
    kb = {}
    for path in sorted(glob.glob(os.path.join(kb_dir, "*.md"))):
        name = os.path.basename(path)
        if name.lower() == "readme.md":
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                kb[name] = f.read().strip()
        except OSError:
            continue
    return kb


def fetch_github_kb(raw_base: str, timeout: int = 8, token: str | None = None):
    """
    从 GitHub raw 目录同步知识库。
    raw_base 形如 https://raw.githubusercontent.com/<user>/<repo>/main/knowledge
    成功返回 {文件名: 内容}；任一核心文件失败则返回 None（由调用方降级本地库）。
    """
    raw_base = raw_base.rstrip("/")
    headers = {"Authorization": f"token {token}"} if token else {}
    kb, failed = {}, []
    for fname in C.KB_FILES:
        try:
            resp = requests.get(f"{raw_base}/{fname}", timeout=timeout, headers=headers)
            if resp.status_code == 200 and resp.text.strip():
                kb[fname] = resp.text.strip()
            else:
                failed.append(fname)
        except requests.RequestException:
            failed.append(fname)
    if failed:
        return None, failed
    return kb, []


# ============================ 二、规则精要压缩（轻量 RAG）============================
_RULE_KEYWORDS = ("限值", "禁止", "不得", "必须", "应", "100%", "罚款", "停工", "IF", "≥", "≤", ">", "<")


def _digest_one_file(name: str, text: str, per_file_cap: int = 760) -> str:
    """只保留章节标题、限值表格、IF 判定规则代码块与含强制语义的短条目；
    来源说明与叙述性段落不进 Prompt（命中隐患后再按需召回全文）。"""
    keep = []
    in_code = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if not s:
            continue
        if in_code:
            keep.append(s)            # 判定规则代码块：全部保留
        elif s.startswith("#"):
            keep.append(s)            # 章节标题
        elif s.startswith("|"):
            keep.append(s)            # 限值表格（核心可执行知识）
        elif s.startswith(">") and len(s) <= 40:
            keep.append(s)            # 极短来源标注
        elif s.startswith(("- ", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")) \
                and len(s) < 70 and any(k in s for k in _RULE_KEYWORDS):
            keep.append(s)            # 含强制语义的法定要求
    digest = f"\n▼ {name}\n" + "\n".join(keep)
    return digest[:per_file_cap] + ("\n…(节选)" if len(digest) > per_file_cap else "")


def build_rule_digest(kb: dict) -> str:
    """把知识库压缩为供 Prompt 使用的规则精要。"""
    if not kb:
        return ""
    parts = [_digest_one_file(name, text) for name, text in sorted(kb.items())]
    return "\n".join(parts)


# ============================ 三、隐患 → 知识库文件映射 ============================
def files_for_categories(category_codes) -> list[str]:
    """根据视觉结果中的 category_code 集合，召回需要展示全文的知识库文件（去重保序）。"""
    files, seen = [], set()
    for code in category_codes:
        meta = C.HAZARD_CATALOG.get(code)
        if not meta:
            continue
        for f in meta[2]:
            if f not in seen:
                seen.add(f)
                files.append(f)
    return files


def get_clause_bundle(kb: dict, files: list[str]) -> list[dict]:
    """返回 [{file, title, content}]，缺失文件给占位说明（提示知识库需补全）。"""
    bundle = []
    for f in files:
        content = kb.get(f)
        title = f.replace(".md", "")
        if content:
            bundle.append({"file": f, "title": title, "content": content})
        else:
            bundle.append({"file": f, "title": title,
                           "content": f"（{f} 未在当前知识库中找到，请检查 GitHub 同步或补充该条文）"})
    return bundle


# ============================ 四、关键词检索（知识库 Tab）============================
def search_kb(kb: dict, query: str, top_k: int = 6):
    """简单可解释的关键词命中打分（无外部依赖、可离线）；返回 [(文件名, 分数, 片段)]。"""
    if not query.strip():
        return [(name, 0, _first_paragraph(text)) for name, text in sorted(kb.items())[:top_k]]
    terms = [t for t in re.split(r"\s+", query.strip()) if t]
    results = []
    for name, text in kb.items():
        score = 0
        for t in terms:
            score += text.count(t) * 2
            if t in name:
                score += 5
        if score:
            results.append((name, score, _snippet(text, terms)))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def _first_paragraph(text: str) -> str:
    for line in text.splitlines():
        if line.strip() and not line.strip().startswith(("#", ">", "|", "```", "-")):
            return line.strip()[:120]
    return text[:120].replace("\n", " ")


def _snippet(text: str, terms: list[str], radius: int = 60) -> str:
    for t in terms:
        idx = text.find(t)
        if idx >= 0:
            return text[max(0, idx - radius):idx + radius].replace("\n", " ").strip()
    return _first_paragraph(text)
