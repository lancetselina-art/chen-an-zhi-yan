# -*- coding: utf-8 -*-
"""
尘安智眼 v4 —— 图表模块
优先使用 Plotly（阈值参考线 + 超标红点 + 三联子图 + 风险仪表盘）；
环境未安装 plotly 时 HAS_PLOTLY=False，由 app.py 降级为 st.line_chart，保证可运行。
"""
from __future__ import annotations

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except Exception:  # pragma: no cover - 依赖缺失时降级
    HAS_PLOTLY = False

from . import config as C

TREND_CN = {"RISING": "上升", "FALLING": "下降", "STABLE": "平稳",
            "VOLATILE": "波动", "NO_DATA": "无数据"}
STATUS_CN = {"EXCEED": "超标", "NEAR": "临近", "NORMAL": "正常", "NO_DATA": "无数据"}


def sensor_figure(df, features: dict):
    """TSP / 噪声 / 气温（叠加湿度）三联时序图，阈值线 + 超标点标红。"""
    if not HAS_PLOTLY:
        return None
    ctx = features["context"]
    t = df["TIME"].dt.strftime("%m-%d %H:%M") if "TIME" in df and df["TIME"].notna().any() else df.index.astype(str)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.09,
                        subplot_titles=(
                            f"场界 TSP（限值 {ctx['tsp_limit']}，国标 {ctx['gb16297_tsp_limit']} mg/m³）",
                            f"场界噪声（{'夜间' if ctx['is_night'] else '昼间'}限值 {ctx['noise_limit']} dB(A)）",
                            "气温 ℃ 与相对湿度 %（35℃ 高温红线）"))

    _add_metric(fig, t, df["TSP"], features["metrics"]["TSP"], row=1, color="#dc2626", ylabel="mg/m³")
    fig.add_hline(y=ctx["tsp_limit"], line_dash="dash", line_color="#dc2626", row=1, col=1,
                  annotation_text="地标限值", annotation_position="top left")
    fig.add_hline(y=ctx["gb16297_tsp_limit"], line_dash="dot", line_color="#7f1d1d", row=1, col=1)

    _add_metric(fig, t, df["NOISE"], features["metrics"]["NOISE"], row=2, color="#2563eb", ylabel="dB(A)")
    fig.add_hline(y=ctx["noise_limit"], line_dash="dash", line_color="#dc2626", row=2, col=1,
                  annotation_text="排放限值", annotation_position="top left")

    _add_metric(fig, t, df["TEMP"], features["metrics"]["TEMP"], row=3, color="#f97316", ylabel="℃")
    fig.add_trace(go.Scatter(x=t, y=df["HUM"], name="湿度%", mode="lines+markers",
                             line=dict(color="#0891b2", dash="dot", width=1.5),
                             marker=dict(size=4), yaxis="y4"), row=3, col=1)
    fig.add_hline(y=35, line_dash="dash", line_color="#dc2626", row=3, col=1,
                  annotation_text="高温阈值", annotation_position="top left")

    fig.update_layout(
        height=620, margin=dict(l=50, r=50, t=60, b=10), showlegend=False,
        hovermode="x unified",
        plot_bgcolor="#f8fafc", paper_bgcolor="white",
        font=dict(family="Microsoft YaHei, Arial", size=12, color="#1e293b"))
    fig.update_yaxes(zeroline=False, gridcolor="#e2e8f0")
    # 第三行右轴给湿度
    fig.update_layout(yaxis4=dict(title="湿度%", overlaying="y3", side="right", range=[0, 100], showgrid=False))
    return fig


def _add_metric(fig, t, s, meta, row, color, ylabel):
    s = s.astype(float)
    fig.add_trace(go.Scatter(x=t, y=s, name=ylabel, mode="lines+markers",
                             line=dict(color=color, width=2.2),
                             marker=dict(size=5, color=color)), row=row, col=1)
    limit = meta.get("threshold")
    if limit is not None:
        over = s[s > limit]
        fig.add_trace(go.Scatter(x=t[over.index], y=over, name="超标点", mode="markers",
                                 marker=dict(size=11, color="#dc2626", symbol="x",
                                             line=dict(width=2, color="#7f1d1d"))), row=row, col=1)


def risk_gauge(score: int, level: str):
    """风险分值仪表盘（0-100，三色分区）。"""
    if not HAS_PLOTLY:
        return None
    color = C.SEVERITY.get(level, C.SEVERITY["GREEN"])["hex"]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "分", "font": {"size": 30, "color": color}},
        title={"text": f"综合风险 · {C.SEVERITY.get(level, {}).get('name', '')}", "font": {"size": 15}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": color, "thickness": 0.55},
            "steps": [
                {"range": [0, 30], "color": "#dcfce7"},
                {"range": [30, 60], "color": "#fef9c3"},
                {"range": [60, 80], "color": "#ffedd5"},
                {"range": [80, 100], "color": "#fee2e2"}],
            "threshold": {"line": {"color": color, "width": 4}, "thickness": 1, "value": score}},
    ))
    fig.update_layout(height=230, margin=dict(l=20, r=20, t=45, b=10))
    return fig
