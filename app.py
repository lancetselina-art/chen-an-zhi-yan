# -*- coding: utf-8 -*-
# ============================================================
# 尘安智眼 v4 —— 工地环境与安全智能监测系统（Streamlit 重构版）
# 运行：python -m streamlit run app.py
# 模块：core.config / prompts / knowledge / analytics / charts
#       / vision_overlay / llm / demo / reporting
# ============================================================
import io
import os
import sys
import json
import requests
import pandas as pd
from PIL import Image
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import config as C
from core import knowledge as KB
from core import analytics as A
from core import charts as CH
from core import vision_overlay as VO
from core import reporting as R
from core import llm
from core import demo as DEMO

# 跨版本兼容：新版 Streamlit 用 width="stretch"，旧版用 **UW
import inspect
if "width" in inspect.signature(st.button).parameters:
    UW = {"width": "stretch"}
else:
    UW = {"use_container_width": True}

# ============================ 页面与样式 ============================
st.set_page_config(page_title=C.APP_TITLE, page_icon="🏗️", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown("""
<style>
    .block-container {padding-top: 1.6rem; max-width: 1280px;}
    .stButton>button {border-radius: 8px; font-weight: 600;}
    .stButton>button[kind="primary"] {background: linear-gradient(90deg,#e94560,#ff6b6b);
        border: none; color: #fff; padding: .55rem 0;}
    section[data-testid="stSidebar"] {background: #1a1a2e;}
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] .stCaption {color: #e2e8f0 !important;}
    .sev-red    {border-left:5px solid #dc2626; background:#fef2f2; padding:.7rem 1rem; border-radius:.5rem; margin:.4rem 0;}
    .sev-orange {border-left:5px solid #f97316; background:#fff7ed; padding:.7rem 1rem; border-radius:.5rem; margin:.4rem 0;}
    .sev-yellow {border-left:5px solid #eab308; background:#fefce8; padding:.7rem 1rem; border-radius:.5rem; margin:.4rem 0;}
    .flow-step {background:#f1f5f9; border-radius:10px; padding:.8rem .5rem; text-align:center; font-size:.9rem; height:100%;}
    .flow-arrow {text-align:center; font-size:1.4rem; color:#94a3b8; padding-top:1.2rem;}
</style>
""", unsafe_allow_html=True)


# ============================ 通用工具 ============================
@st.cache_data(show_spinner=False)
def _local_kb_cached():
    return KB.load_local_kb()


@st.cache_data(show_spinner=False)
def _digest_cached(kb_tuple):
    return KB.build_rule_digest(dict(kb_tuple))


def sev_badge(level: str) -> str:
    s = C.SEVERITY.get((level or "GREEN").upper(), C.SEVERITY["GREEN"])
    return f"<span style='background:{s['hex']};color:#fff;padding:1px 9px;border-radius:10px;font-size:.8rem'>{s['emoji']} {s['name']}</span>"


def init_state():
    st.session_state.setdefault("kb", _local_kb_cached())
    st.session_state.setdefault("kb_source", "本地 knowledge/ 目录")
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("vision_result", None)
    st.session_state.setdefault("sensor_result", None)


init_state()
KB_DICT = st.session_state["kb"]
KB_TUPLE = tuple(sorted(KB_DICT.items()))
RULE_DIGEST = _digest_cached(KB_TUPLE)


def get_weather(lat, lon):
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&current=temperature_2m,relative_humidity_2m&timezone=Asia%2FShanghai")
        d = requests.get(url, timeout=8).json()["current"]
        return d["temperature_2m"], d["relative_humidity_2m"]
    except Exception:
        return None, None


def add_history(kind, title, level, score, md, payload):
    st.session_state["history"].insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "kind": kind, "title": title,
        "level": (level or "GREEN").upper(), "score": score, "md": md,
        "json": json.dumps(payload, ensure_ascii=False, indent=2, default=str)})


def download_pair(md_text: str, payload: dict, name: str):
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📄 下载 Markdown 报告", md_text.encode("utf-8"),
                           file_name=f"{name}_{datetime.now():%Y%m%d_%H%M}.md",
                           mime="text/markdown", **UW)
    with c2:
        st.download_button("🔢 下载结构化 JSON",
                           json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
                           file_name=f"{name}_{datetime.now():%Y%m%d_%H%M}.json",
                           mime="application/json", **UW)


def render_gauge(score: int, level: str):
    fig = CH.risk_gauge(score or 0, (level or "GREEN").upper())
    if fig:
        st.plotly_chart(fig, **UW, config={"displayModeBar": False})
    else:
        st.progress(min((score or 0) / 100, 1.0))
        st.caption(f"综合风险分：{score}/100（{C.SEVERITY.get((level or 'GREEN').upper(),{}).get('name','')}）")


# ============================ 侧边栏 ============================
with st.sidebar:
    st.markdown("### 🏗️ 尘安智眼 v4")
    st.caption("多模态视觉 × 时序研判 × 规范 RAG")

    st.markdown("#### 🔑 模型服务")
    base_url = st.text_input("Base URL", value=C.DEFAULT_BASE_URL)
    api_key = st.text_input("API Key", type="password", value=os.getenv("ZHIPUAI_API_KEY", ""))
    vision_model = st.selectbox("视觉模型", C.VISION_MODELS, index=0)
    text_model = st.selectbox("文本/数据模型", C.TEXT_MODELS, index=0)
    temperature = st.slider("温度（越低越稳定）", 0.0, 1.0, 0.1, 0.05)
    timeout = st.number_input("超时（秒）", 10, 120, 45, 5)
    demo_mode = st.toggle("▶️ 演示模式（无需 API Key）", value=not api_key)

    st.divider()
    st.markdown("#### 📋 检查上下文")
    stage = st.selectbox("施工阶段", C.STAGES)
    work_type = st.selectbox("作业类型", list(C.WORK_TYPES.keys()))
    is_night = st.toggle("当前为夜间（22:00-次日6:00）", False)

    st.divider()
    st.markdown("#### 📚 知识库")
    kb_src = st.radio("知识来源", ["本地目录", "GitHub 实时同步"], label_visibility="collapsed")
    if kb_src == "GitHub 实时同步":
        gh_base = st.text_input("GitHub raw 目录地址", value=C.GITHUB_KB_HINT)
        if st.button("🔄 从 GitHub 同步", **UW):
            with st.spinner("同步规范知识库…"):
                gh_kb, failed = KB.fetch_github_kb(gh_base, timeout=8)
            if gh_kb:
                st.session_state["kb"] = gh_kb
                st.session_state["kb_source"] = f"GitHub：{gh_base}"
                st.success(f"已同步 {len(gh_kb)} 份规范文件")
                st.rerun()
            else:
                st.error(f"同步失败（{', '.join(failed[:3])}…），已保留本地知识库")
    st.caption(f"当前来源：{st.session_state['kb_source']}")
    st.caption(f"📚 {len(KB_DICT)} 份文件 · 精要 {len(RULE_DIGEST)} 字符（已压缩注入）")

cfg = llm.AppConfig(api_key=api_key, base_url=base_url, vision_model=vision_model,
                    text_model=text_model, temperature=temperature, timeout=int(timeout),
                    demo_mode=demo_mode)
CTX = {"stage": stage, "work_type": work_type, "is_night": is_night}

# ============================ 顶部 ============================
st.markdown(f"## 🏗️ {C.APP_TITLE}")
st.caption(C.APP_SUBTITLE)
if demo_mode:
    st.info("**演示模式已开启**：使用内置样例图片/数据与结构化结果演示完整链路，检测框、图表、法条映射、报告下载均可体验；填入 API Key 并关闭演示模式即接入真实大模型。")

tab_overview, tab_vision, tab_sensor, tab_kb, tab_history = st.tabs(
    ["📊 总览", "📷 视觉隐患识别", "🌡️ 传感器研判", "📚 知识库", "🗂️ 检查台账"])

# ============================ Tab 1 总览 ============================
with tab_overview:
    hist = st.session_state["history"]
    n_red = sum(1 for h in hist if h["level"] == "RED")
    n_finding = sum(h["score"] for h in hist if h["kind"] == "视觉")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("累计检查次数", len(hist))
    m2.metric("红线预警次数", n_red)
    m3.metric("视觉巡检风险分累计", n_finding)
    m4.metric("在线规范文件", len(KB_DICT))

    st.markdown("### ⚙️ 系统工作流")
    flow = ["① 多源采集\n照片 / 探头时序", "② 结构化 Prompt\n专家角色+JSON契约",
            "③ 多模态大模型\nGLM-5.3-Flash（视觉+文本）", "④ 知识库 RAG\n隐患→法条自动映射",
            "⑤ 分级处置\n检测框·预警·工单闭环"]
    cols = st.columns([2.2, 0.4, 2.2, 0.4, 2.2, 0.4, 2.2, 0.4, 2.2])
    for i, step in enumerate(flow):
        with cols[i * 2]:
            st.markdown(f"<div class='flow-step'>{step.replace(chr(10), '<br>')}</div>",
                        unsafe_allow_html=True)
        if i < 4:
            with cols[i * 2 + 1]:
                st.markdown("<div class='flow-arrow'>→</div>", unsafe_allow_html=True)

    st.markdown("### 📏 现行限值速查（陕西西安口径）")
    lim_df = pd.DataFrame([
        ["TSP 场界浓度", f"≤{C.STAGE_TSP_LIMIT['拆除/土方/地基处理']}（土方）/ {C.STAGE_TSP_LIMIT['基础/主体/装饰装修']}（主体）mg/m³", "DB61/1078-2017"],
        ["颗粒物无组织排放", f"≤{C.GB16297_TSP_LIMIT} mg/m³", "GB16297-1996"],
        ["施工场界噪声", f"昼 {C.NOISE_LIMIT['day']} / 夜 {C.NOISE_LIMIT['night']} dB(A)，夜间峰值≤{C.NOISE_LIMIT['night_peak']}", "GB12523-2025"],
        ["作业面噪声职业限值", f"{C.WORKER_NOISE_LIMIT} dB(A)/8h，+3dB 接触时间减半", "GBZ2.2-2007"],
        ["高温作业", "≥40℃停工；37~40℃室外≤6h；35~37℃轮休禁加班", "安监总安健〔2012〕89号"],
    ], columns=["监测对象", "限值/规则", "依据"])
    st.dataframe(lim_df, hide_index=True, **UW)
    st.caption("操作指引：左侧选择施工阶段/作业类型 → 「视觉隐患识别」上传照片 → 「传感器研判」上传 CSV 或录入时序 → 报告自动入台账。")

# ============================ Tab 2 视觉 ============================
with tab_vision:
    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("### 📷 现场照片")
        uploaded = st.file_uploader("上传施工现场照片", type=list(C.ALLOWED_IMAGE_EXT),
                                    label_visibility="collapsed")
        pil_img, img_bytes, mime = None, None, None
        if uploaded is not None:
            if uploaded.size > C.MAX_IMAGE_MB * 1024 * 1024:
                st.error(f"图片超过 {C.MAX_IMAGE_MB}MB，请压缩后上传")
            else:
                try:
                    pil_img = Image.open(io.BytesIO(uploaded.getvalue())).convert("RGB")
                    img_bytes = uploaded.getvalue()
                    ext = os.path.splitext(uploaded.name)[1].lstrip(".").lower()
                    mime = "jpeg" if ext in ("jpg", "jpeg") else ext if ext in ("png", "webp") else "jpeg"
                    st.image(pil_img, **UW, caption="原始现场照片")
                except Exception:
                    st.error("图片无法解析，请确认是未损坏的 JPG/PNG/WEBP 文件")
        elif demo_mode:
            pil_img = Image.open(DEMO.DEMO_IMAGE).convert("RGB")
            st.image(pil_img, **UW, caption="内置演示照片（data/demo_site.jpg）")
            buf = io.BytesIO(); pil_img.save(buf, format="JPEG"); img_bytes = buf.getvalue(); mime = "jpeg"
    with right:
        st.markdown("### 🎯 巡检配置")
        st.write(f"施工阶段：**{stage}**　作业类型：**{work_type}**　时段：**{'夜间' if is_night else '昼间'}**")
        st.caption("识别维度：安全帽/带、临边洞口、脚手架、动火明火、临时用电、吊装、"
                   "裸土覆盖、湿法作业、道路硬化、围挡、渣土车、尾气黑烟、污水、光污染等 18 类")
        run_vision = st.button("🚀 开始 AI 视觉巡检", type="primary", **UW)

    if run_vision:
        if img_bytes is None:
            st.warning("请先上传现场照片（或开启演示模式使用内置样例）")
        else:
            with st.status("AI 视觉巡检流水线", expanded=True) as status:
                try:
                    st.write("① 校验图像与上下文…")
                    v_ctx = dict(CTX, city="西安", inspect_time=datetime.now().strftime("%Y-%m-%d %H:%M"))
                    st.write("② 注入结构化专家 Prompt 与规范知识库精要…")
                    if cfg.demo_mode:
                        result = DEMO.demo_vision_result()
                    else:
                        result = llm.analyze_image(cfg, img_bytes, mime, v_ctx, RULE_DIGEST)
                    st.write("③ 结构化结果校验与隐患→法条映射…")
                    codes = [f.get("category_code") for f in result.get("findings", [])]
                    clause_files = KB.files_for_categories(codes)
                    st.write("④ 绘制检测框与风险标签…")
                    overlay = VO.draw_findings(pil_img, result)
                    status.update(label="✅ 巡检完成", state="complete", expanded=False)
                except llm.LLMError as e:
                    status.update(label="❌ 巡检失败", state="error", expanded=True)
                    st.error(f"调用失败：{e}")
                    st.stop()
                except Exception as e:  # noqa: BLE001
                    status.update(label="❌ 处理异常", state="error", expanded=True)
                    st.error(f"本地处理异常：{str(e)[:160]}")
                    st.stop()

            o = result.get("overall", {})
            st.markdown(f"### 🧾 {o.get('headline', '巡检结果')}")
            c_g, c_r, c_o, c_y = st.columns([1.1, 1, 1, 1])
            with c_g:
                render_gauge(o.get("risk_score", 0), o.get("risk_level", "GREEN"))
            stats = result.get("stats", {})
            c_r.metric("🔴 红线", stats.get("red", 0))
            c_o.metric("🟠 黄线", stats.get("orange", 0))
            c_y.metric("🟡 提醒", stats.get("yellow", 0))
            st.markdown(f"**处置意见**：{o.get('disposition','—')}")

            st.image(overlay, **UW, caption="AI 检测结果叠加图（框体位置由模型归一化坐标绘制）")

            st.markdown("### 🚨 隐患清单与整改工单")
            for f in result.get("findings", []):
                sev = (f.get("severity") or "YELLOW").upper()
                cls = {"RED": "sev-red", "ORANGE": "sev-orange"}.get(sev, "sev-yellow")
                refs = "、".join(r.get("code", "") for r in f.get("standard_refs", []))
                rect = f.get("rectification", {})
                with st.container(border=True):
                    st.markdown(
                        f"<div class='{cls}'><b>{f.get('id','')} {f.get('item','')}</b> "
                        f"{sev_badge(sev)}　危险值 <b>{f.get('danger_level','-')}/5</b>　"
                        f"置信度 {f.get('confidence','-')}　依据：{refs or '（无）'}</div>",
                        unsafe_allow_html=True)
                    a, b = st.columns(2)
                    a.markdown(f"**📍 位置**：{f.get('location_desc','—')}")
                    b.markdown(f"**👷 涉险人数（估）**：{f.get('affected_workers', 0)}")
                    st.markdown(f"**👁️ 画面证据**：{f.get('visual_evidence','—')}")
                    st.markdown(f"**⛓️ 事故链**：{f.get('accident_chain','—')}")
                    st.markdown(f"**🛠️ 整改**：{rect.get('action','—')}"
                                f"（{rect.get('responsible','')}，{rect.get('deadline_hours','-')}h 内）")
                    if rect.get("voice_prompt"):
                        st.success(f"🔊 现场语音提示：{rect['voice_prompt']}")
                    if f.get("immediate_danger"):
                        st.error("⚠️ immediate_danger=true：存在即刻危险，须先停止作业/撤离再处置")

            if clause_files:
                with st.expander(f"📖 自动匹配的规范条文（{len(clause_files)} 份，知识库联动）"):
                    for item in KB.get_clause_bundle(KB_DICT, clause_files):
                        st.markdown(f"#### 📄 {item['title']}")
                        st.markdown(item["content"])
            for u in result.get("uncertainties", []):
                st.warning(f"❓ 复检提示：{u}")

            md = R.vision_to_markdown(result, v_ctx)
            download_pair(md, result, "视觉巡检报告")
            add_history("视觉", o.get("headline", "视觉巡检")[:38], o.get("risk_level"),
                        o.get("risk_score", 0), md, result)
            st.success("报告已存入「检查台账」")

# ============================ Tab 3 传感器 ============================
with tab_sensor:
    st.markdown("### 🌡️ 监测数据输入")
    sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_sensor.csv")
    sample_df = pd.read_csv(sample_path)

    input_mode = st.radio("输入方式", ["上传 CSV 时序", "在线表格录入", "单点速测"], horizontal=True)
    raw_df, city = None, "西安"
    if input_mode == "上传 CSV 时序":
        c1, c2 = st.columns([2, 1])
        up = c1.file_uploader("上传探头时序 CSV（支持表头：时间/TSP/噪声/气温/湿度/PM10）", type=["csv"])
        with open(sample_path, "rb") as fh:
            c2.download_button("⬇️ 下载 CSV 模板", fh.read(), file_name="sample_sensor.csv",
                               mime="text/csv", **UW)
        if up is not None:
            try:
                raw_df = pd.read_csv(up)
            except Exception:
                st.error("CSV 解析失败，请检查编码（建议 UTF-8）与列格式")
        elif demo_mode:
            raw_df = sample_df
            st.caption("演示模式已载入内置示例时序（含 TSP 上升超标、噪声超标、高温过程）")
    elif input_mode == "在线表格录入":
        st.caption("可直接增删行列，时间格式 YYYY-MM-DD HH:MM；至少 2 行才能计算趋势")
        raw_df = st.data_editor(sample_df.head(8), num_rows="dynamic", **UW, hide_index=True)
    else:
        city = st.selectbox("项目城市（自动获取天气）", list(C.CITY_COORDS.keys()))
        sc1, sc2 = st.columns(2)
        if sc1.button("🌤️ 获取实时天气"):
            lat, lon = C.CITY_COORDS[city]
            t, h = get_weather(lat, lon)
            if t is not None:
                st.session_state["sp_temp"] = float(t); st.session_state["sp_hum"] = int(h)
                st.success(f"{city} 当前 {t}℃，湿度 {h}%，已填入下方")
                st.rerun()
            else:
                sc2.error("天气获取失败，请手动填写")
        p1, p2, p3, p4, p5 = st.columns(5)
        st.session_state.setdefault("sp_tsp", 0.0); st.session_state.setdefault("sp_noise", 0.0)
        st.session_state.setdefault("sp_temp", 25.0); st.session_state.setdefault("sp_hum", 50)
        st.session_state.setdefault("sp_pm10", 0.0)
        tsp0 = p1.number_input("TSP mg/m³", 0.0, 100.0, key="sp_tsp", step=0.1)
        noise0 = p2.number_input("噪声 dB(A)", 0.0, 120.0, key="sp_noise", step=0.5)
        temp0 = p3.number_input("气温 ℃", -20.0, 50.0, key="sp_temp", step=0.5)
        hum0 = p4.number_input("相对湿度 %", 0, 100, key="sp_hum")
        pm100 = p5.number_input("背景 PM10 mg/m³", 0.0, 2.0, key="sp_pm10", step=0.01)
        raw_df = pd.DataFrame([{"时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "TSP": tsp0, "噪声": noise0, "气温": temp0, "湿度": hum0, "PM10": pm100}])

    if raw_df is not None and not raw_df.empty:
        try:
            features = A.compute_features(raw_df, stage, work_type, is_night, city)
        except Exception as e:  # noqa: BLE001
            st.error(f"数据计算失败：{str(e)[:200]}（请检查列名与数值格式）")
            st.stop()

        L = features["latest"]
        st.markdown("### 📊 实时指标（程序确定性判定）")
        k = st.columns(5)
        tsp_status = CH.STATUS_CN.get(features["metrics"]["TSP"]["status"], "")
        k[0].metric("TSP mg/m³", L["TSP"] if L["TSP"] is not None else "—",
                    f"限值 {features['context']['tsp_limit']} · {tsp_status}", delta_color="inverse")
        k[1].metric("噪声 dB(A)", L["NOISE"] if L["NOISE"] is not None else "—",
                    f"限值 {features['context']['noise_limit']}")
        k[2].metric("气温 ℃", L["TEMP"] if L["TEMP"] is not None else "—", "高温线 35")
        k[3].metric("湿度 %", L["HUM"] if L["HUM"] is not None else "—")
        wb = features.get("wbgt") or {}
        k[4].metric("估算 WBGT ℃", wb.get("value", "—"))

        # 确定性预警（不依赖大模型，先算先报）
        for alert in features["deterministic_alerts"]:
            box = {"RED": st.error, "ORANGE": st.warning, "YELLOW": st.info}.get(alert["level"], st.info)
            box(f"{C.SEVERITY[alert['level']]['emoji']} **【{alert['metric']}】{alert['title']}**　{alert['detail']}")
        bz = features.get("breathing_zone")
        if bz:
            st.caption(f"🫁 呼吸带折算（{work_type}，系数 {bz['factor_low']}~{bz['factor_high']}）："
                       f"约 **{bz['estimated_low']}~{bz['estimated_high']} mg/m³**，"
                       f"{bz['dust_type']}职业接触限值 {bz['yellow_limit_respirable']} mg/m³，建议{bz['mask_advice']}")
        bg = features.get("background_correction")
        if bg:
            st.caption(f"🌫️ 背景修正：TSP/PM10={bg['ratio']}；{bg['conclusion']}")

        st.markdown("### 📈 时序曲线（阈值线 + 超标点）")
        dfc = A.canonicalize(raw_df)
        fig = CH.sensor_figure(dfc, features)
        if fig:
            st.plotly_chart(fig, **UW)
        else:
            st.caption("未安装 plotly，降级为内置折线图（pip install plotly 可获得阈值线与超标标注）")
            st.line_chart(dfc.set_index("TIME")[["TSP", "NOISE", "TEMP", "HUM"]].dropna(how="all"))
        with st.expander("🔍 查看特征工程明细（喂给大模型的 features JSON）"):
            st.json(features)

        if st.button("🧠 生成 AI 专业研判报告", type="primary", **UW):
            with st.status("AI 数据研判流水线", expanded=True) as status:
                try:
                    status.write("① 数据质控与特征工程（程序完成）")
                    s_ctx = dict(CTX, city=city)
                    status.write("② 注入数据分析专家 Prompt + 规范精要")
                    if cfg.demo_mode:
                        sresult = DEMO.demo_sensor_result(features)
                    else:
                        sresult = llm.analyze_sensors(cfg, features, s_ctx, RULE_DIGEST)
                    status.update(label="✅ 研判完成", state="complete", expanded=False)
                except llm.LLMError as e:
                    status.update(label="❌ 研判失败", state="error", expanded=True)
                    st.error(f"调用失败：{e}")
                    st.stop()
            so = sresult.get("overall", {})
            st.markdown(f"### 🧾 {so.get('headline','数据研判结果')}")
            cg, cd = st.columns([1, 2])
            with cg:
                render_gauge(so.get("risk_score", features["risk_score"]), so.get("risk_level", "GREEN"))
            with cd:
                for w in sresult.get("warnings", []):
                    box = {"RED": st.error, "ORANGE": st.warning, "YELLOW": st.info}.get(w.get("level"), st.info)
                    box(f"**【{w.get('metric')}】{w.get('title')}**　{w.get('detail')}")
            for m in sresult.get("metric_reports", []):
                with st.expander(f"{sev_badge(m.get('level'))} {m.get('metric_name')}　"
                                 f"现状 {m.get('current')} {m.get('unit','')}　趋势 {CH.TREND_CN.get(m.get('trend'), m.get('trend'))}"):
                    st.markdown(f"**趋势证据**：{m.get('trend_evidence','—')}")
                    st.markdown(f"**机理研判**：{m.get('physical_mechanism','—')}")
                    if m.get("actions"):
                        st.markdown("**处置措施**：" + "；".join(m["actions"]))
            pw = sresult.get("process_window", {})
            if pw:
                w1, w2 = st.columns(2)
                cp, ow = pw.get("concrete_pouring", {}), pw.get("outdoor_work", {})
                if cp:
                    (w1.success if cp.get("suitable") else w1.warning)(
                        f"**🧱 混凝土浇筑窗口：{'适宜' if cp.get('suitable') else '不适宜'}**\n\n{cp.get('reason','')}\n\n"
                        + "；".join(cp.get("measures", [])))
                if ow:
                    (w2.success if ow.get("suitable") else w2.warning)(
                        f"**👷 室外作业窗口：{'适宜' if ow.get('suitable') else '受限'}**\n\n{ow.get('reason','')}\n\n"
                        + "；".join(ow.get("measures", [])))
            if sresult.get("forecast"):
                st.info(f"🔮 **趋势外推**：{sresult['forecast']}")
            if sresult.get("coupled_synthesis"):
                st.markdown("### 🔗 多因子耦合研判")
                st.markdown(sresult["coupled_synthesis"])
            if sresult.get("report_markdown"):
                with st.expander("📝 完整 Markdown 研判报告"):
                    st.markdown(sresult["report_markdown"])
            md = R.sensor_to_markdown(sresult, features, s_ctx)
            download_pair(md, sresult, "传感器研判报告")
            add_history("数据", so.get("headline", "传感器研判")[:38], so.get("risk_level"),
                        so.get("risk_score", features["risk_score"]), md, sresult)
            st.success("报告已存入「检查台账」")

# ============================ Tab 4 知识库 ============================
with tab_kb:
    st.markdown("### 📚 规范知识库与隐患映射")
    q = st.text_input("🔍 关键词检索（如：裸土、噪声、高温、黑烟、沉淀池）")
    if q:
        hits = KB.search_kb(KB_DICT, q)
        if not hits:
            st.info("未命中相关文件")
        for name, score, snip in hits:
            with st.expander(f"📄 {name}（命中 {score} 次）"):
                st.caption(snip)
                st.markdown(KB_DICT.get(name, ""))
    else:
        fsel = st.selectbox("选择文件查看全文", sorted(KB_DICT.keys()))
        st.markdown(KB_DICT[fsel])
    st.markdown("### 🗺️ 隐患分类 → 知识库/标准 自动映射表")
    map_rows = []
    for code, (name, sev, files, stds, focus) in C.HAZARD_CATALOG.items():
        map_rows.append([code, name, C.SEVERITY[sev]["emoji"] + C.SEVERITY[sev]["name"],
                         "、".join(files) if files else "（待补全文）",
                         "、".join(s[0] for s in stds)])
    st.dataframe(pd.DataFrame(map_rows, columns=["分类码", "隐患", "默认等级", "知识库文件", "引用标准"]),
                 hide_index=True, **UW)
    st.caption("GitHub 联动：在侧边栏填入 raw 目录地址即可实时拉取团队维护的最新规范；同步失败自动降级本地库。")

# ============================ Tab 5 台账 ============================
with tab_history:
    st.markdown("### 🗂️ 本次会话检查台账")
    if not st.session_state["history"]:
        st.info("暂无记录，完成一次视觉巡检或传感器研判后自动归档（决赛可扩展 SQLite 持久化）")
    else:
        hist_df = pd.DataFrame(
            [[h["time"], h["kind"], sev_badge(h["level"]), h["score"], h["title"]] for h in st.session_state["history"]],
            columns=["时间", "类型", "等级", "风险分", "结论"])
        st.markdown(hist_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        names = [f"{h['time']}｜{h['kind']}｜{h['title'][:20]}" for h in st.session_state["history"]]
        pick = st.selectbox("选择记录查看/下载", names)
        if pick:
            h = st.session_state["history"][names.index(pick)]
            st.markdown(h["md"])
            download_pair(h["md"], json.loads(h["json"]), h["kind"] + "归档")
        if st.button("🗑️ 清空台账"):
            st.session_state["history"] = []
            st.rerun()

st.divider()
st.caption("尘安智眼 v4 · 海之子杯 AI 智能体挑战赛 ｜ 天气：Open-Meteo（免 Key）｜ 规范：GB/DB61/GBZ 现行标准 ｜ "
           "结构化 JSON 输出 · 知识库 RAG 映射 · 全链路错误兜底")
