# -*- coding: utf-8 -*-
"""
尘安智眼 v4 —— 传感器时序分析（确定性计算层）
原则：所有阈值判定、统计量、趋势斜率、WBGT/呼吸带折算都由代码算准，
     大模型只负责机理研判与措施建议，从根本上杜绝 LLM 算术幻觉。
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from . import config as C


# ============================ 一、数据载入与标准化 ============================
def canonicalize(df: pd.DataFrame) -> pd.DataFrame:
    """把中文/英文别名表头统一为 TIME/TSP/NOISE/TEMP/HUM/PM10，并按时间排序。"""
    rename = {}
    lowered = {str(c).strip(): c for c in df.columns}
    for canon, aliases in C.COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lowered:
                rename[lowered[alias]] = canon
                break
    df = df.rename(columns=rename).copy()
    for col in ["TSP", "NOISE", "TEMP", "HUM", "PM10"]:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "TIME" in df.columns:
        df["TIME"] = pd.to_datetime(df["TIME"], errors="coerce")
        df = df.sort_values(by="TIME", na_position="last").reset_index(drop=True)
    else:
        df = df.reset_index(drop=True)
    return df[["TIME"] + [c for c in ["TSP", "NOISE", "TEMP", "HUM", "PM10"]]]


def _hours_axis(df: pd.DataFrame) -> np.ndarray:
    """把时间轴换算为相对小时；无法解析时间时退化为等间隔序号。"""
    if "TIME" in df and df["TIME"].notna().sum() >= 2:
        t0 = df["TIME"].dropna().iloc[0]
        return (df["TIME"] - t0).dt.total_seconds().to_numpy(dtype=float) / 3600.0
    return np.arange(len(df), dtype=float)


# ============================ 二、WBGT 简化估算（双线性插值）============================
def estimate_wbgt(temp: float | None, humidity: float | None):
    if temp is None or humidity is None or math.isnan(temp) or math.isnan(humidity):
        return None
    temps = sorted(C.WBGT_TABLE.keys())
    hums = [50, 70, 90]
    grid = np.array([[C.WBGT_TABLE[t][h] for h in hums] for t in temps], dtype=float)
    ti = np.clip(np.interp(temp, temps, np.arange(len(temps))), 0, len(temps) - 1)
    hi = np.clip(np.interp(humidity, hums, np.arange(len(hums))), 0, len(hums) - 1)
    i0, j0 = int(np.floor(ti)), int(np.floor(hi))
    i1, j1 = min(i0 + 1, len(temps) - 1), min(j0 + 1, len(hums) - 1)
    dt, dh = ti - i0, hi - j0
    val = (grid[i0, j0] * (1 - dt) * (1 - dh) + grid[i0, j1] * (1 - dt) * dh
           + grid[i1, j0] * dt * (1 - dh) + grid[i1, j1] * dt * dh)
    return round(float(val), 1)


# ============================ 三、单指标统计 ============================
def _series_stats(values: np.ndarray, hours: np.ndarray, limit: float | None,
                  unit: str, higher_is_bad: bool = True) -> dict[str, Any]:
    v = values[~np.isnan(values)]
    out: dict[str, Any] = {"n_total": int(len(values)), "n_valid": int(len(v)),
                           "latest": None, "mean": None, "max": None, "min": None,
                           "slope_per_hour": None, "pct_change": None, "trend": "NO_DATA",
                           "exceed_points": 0, "exceed_ratio": 0.0, "max_consecutive_exceed": 0,
                           "threshold": limit, "unit": unit, "status": "NO_DATA"}
    if len(v) == 0:
        return out
    latest, mean, mx, mn = float(v[-1]), float(np.mean(v)), float(np.max(v)), float(np.min(v))
    out.update(latest=round(latest, 3), mean=round(mean, 3), max=round(mx, 3), min=round(mn, 3))

    # 线性斜率（最小二乘，单位/小时）
    if len(v) >= 2:
        h = hours[~np.isnan(values)]
        if np.ptp(h) > 0:
            slope = float(np.polyfit(h, v, 1)[0])
            out["slope_per_hour"] = round(slope, 4)
        base = v[0] if abs(v[0]) > 1e-9 else max(abs(mx) * 0.05, 1e-6)
        out["pct_change"] = round(float((v[-1] - v[0]) / base), 3)

    # 超标统计与最长连续超标段
    if limit is not None:
        over = v > limit if higher_is_bad else v < limit
        out["exceed_points"] = int(over.sum())
        out["exceed_ratio"] = round(float(over.mean()), 2)
        run = best = 0
        for flag in over:
            run = run + 1 if flag else 0
            best = max(best, run)
        out["max_consecutive_exceed"] = int(best)
        if latest > limit if higher_is_bad else latest < limit:
            out["status"] = "EXCEED"
        elif latest >= 0.9 * limit if higher_is_bad else latest <= 1.1 * limit:
            out["status"] = "NEAR"
        else:
            out["status"] = "NORMAL"

    # 趋势分类（变化幅度 + 斜率，带死区避免噪声误判）
    out["trend"] = _classify_trend(v, out.get("slope_per_hour"), limit)
    return out


def _classify_trend(v: np.ndarray, slope: float | None, limit: float | None) -> str:
    if len(v) < 2:
        return "NO_DATA"
    pct = (v[-1] - v[0]) / (abs(v[0]) if abs(v[0]) > 1e-9 else 1.0)
    band = 0.08  # 8% 死区
    # 方向性优先：净变化显著的上行/下行（允许中途小幅回落）直接定趋势
    if pct >= band and (slope is None or slope > 0):
        return "RISING"
    if pct <= -band and (slope is None or slope < 0):
        return "FALLING"
    # 无明确净趋势但起伏明显才判波动，避免把“上升后小幅回落”误判为波动
    if np.std(v) > max(0.12 * abs(np.mean(v)), 1e-6) and (np.max(v) - np.min(v)) > (limit or 1) * 0.2:
        return "VOLATILE"
    return "STABLE"


# ============================ 四、主入口：特征工程 ============================
def compute_features(df: pd.DataFrame, stage: str, work_type: str, is_night: bool,
                     city: str = "西安") -> dict[str, Any]:
    df = canonicalize(df)
    hours = _hours_axis(df)
    tsp_limit = C.STAGE_TSP_LIMIT.get(stage, 0.8)
    noise_limit = C.NOISE_LIMIT["night"] if is_night else C.NOISE_LIMIT["day"]

    metrics = {
        "TSP":   _series_stats(df["TSP"].to_numpy(float), hours, tsp_limit, "mg/m³"),
        "NOISE": _series_stats(df["NOISE"].to_numpy(float), hours, noise_limit, "dB(A)"),
        "TEMP":  _series_stats(df["TEMP"].to_numpy(float), hours, C.HEAT_RED_LINE, "℃"),
        "HUM":   _series_stats(df["HUM"].to_numpy(float), hours, None, "%"),
        "PM10":  _series_stats(df["PM10"].to_numpy(float), hours, None, "mg/m³"),
    }

    latest = {k: metrics[k]["latest"] for k in metrics}
    wbgt = estimate_wbgt(latest["TEMP"], latest["HUM"])

    # 场界 TSP → 工人呼吸带折算（取作业系数中值）
    breathing = None
    if latest["TSP"] is not None:
        lo, hi, dust_name, dust_limit, mask = C.WORK_TYPES.get(work_type, (1.5, 2.0, "混合尘", 4.0, "KN90"))
        mid = (lo + hi) / 2
        breathing = {
            "factor_low": lo, "factor_high": hi, "factor_mid": mid,
            "dust_type": dust_name, "yellow_limit_respirable": dust_limit,
            "estimated_low": round(latest["TSP"] * lo, 3),
            "estimated_mid": round(latest["TSP"] * mid, 3),
            "estimated_high": round(latest["TSP"] * hi, 3),
            "mask_advice": mask,
            "status": "EXCEED" if latest["TSP"] * mid > dust_limit else "NORMAL",
        }

    # 作业面噪声折算
    worker_noise = None
    if latest["NOISE"] is not None:
        wn = latest["NOISE"] + C.WORKER_NOISE_ADD
        worker_noise = {"estimated": round(wn, 1), "limit": C.WORKER_NOISE_LIMIT,
                        "status": "EXCEED" if wn >= C.WORKER_NOISE_LIMIT else "NEAR" if wn >= 82 else "NORMAL"}

    # PM10 背景修正三档（DB61/1078）
    background = None
    if latest["TSP"] is not None and latest["PM10"] is not None and latest["PM10"] > 0:
        ratio = latest["TSP"] / latest["PM10"]
        if ratio >= 2:
            case = "TSP≥2×PM10：施工影响显著，立即报警，不修正直接对标限值"
        elif ratio >= 1.3:
            corrected = round(latest["TSP"] - 1.3 * latest["PM10"], 3)
            case = f"1.3×PM10≤TSP<2×PM10：有一定影响，修正值={corrected} mg/m³ 后对标"
        else:
            case = "TSP≤1.3×PM10：施工对环境基本无影响，直接对标"
        background = {"ratio": round(ratio, 2), "conclusion": case}

    # 高温法定档位
    heat = None
    if latest["TEMP"] is not None:
        t = latest["TEMP"]
        if t >= 40:
            heat = {"level": "RED", "rule": C.HEAT_RULES[0][1]}
        elif t >= 37:
            heat = {"level": "RED", "rule": C.HEAT_RULES[1][1]}
        elif t >= 35:
            heat = {"level": "ORANGE", "rule": C.HEAT_RULES[2][1]}
        else:
            heat = {"level": "GREEN", "rule": "未达高温作业阈值"}

    # 数据质控：掉点、卡死（标准差为 0）、突变
    faults = []
    for k, m in metrics.items():
        if 0 < m["n_valid"] < m["n_total"]:
            faults.append(f"{k} 存在 {m['n_total'] - m['n_valid']} 个缺失/异常点")
        col = df[k].dropna().to_numpy(float)
        if len(col) >= 4 and np.std(col) < 1e-6:
            faults.append(f"{k} 全程数值恒定，疑似探头卡死")
    if len(df) == 0:
        faults.append("未读取到任何数据行")

    deterministic_alerts = _build_alerts(metrics, breathing, worker_noise, heat, background, is_night)
    risk = _risk_score(deterministic_alerts)

    return {
        "schema_version": "features/v2",
        "context": {"city": city, "stage": stage, "work_type": work_type,
                    "is_night": is_night, "period": "夜间" if is_night else "昼间",
                    "tsp_limit": tsp_limit, "noise_limit": noise_limit,
                    "gb16297_tsp_limit": C.GB16297_TSP_LIMIT},
        "n_rows": int(len(df)),
        "time_range": _time_range(df),
        "latest": latest,
        "metrics": metrics,
        "wbgt": {"value": wbgt, "note": "重体力劳动 WBGT≥25 即属高温作业，≥28 为第三级以上"} if wbgt else None,
        "breathing_zone": breathing,
        "worker_noise": worker_noise,
        "background_correction": background,
        "heat_rule": heat,
        "data_quality": {"completeness_pct": round(
            100 * np.mean([m["n_valid"] / max(m["n_total"], 1) for m in metrics.values()]), 1),
            "faults": faults},
        "deterministic_alerts": deterministic_alerts,
        "risk_score": risk,
    }


def _build_alerts(metrics, breathing, worker_noise, heat, background, is_night) -> list[dict]:
    alerts = []
    tsp, noise, temp = metrics["TSP"], metrics["NOISE"], metrics["TEMP"]

    if tsp["status"] == "EXCEED":
        sev = "RED" if tsp["latest"] >= C.GB16297_TSP_LIMIT or tsp["trend"] == "RISING" else "ORANGE"
        alerts.append({"level": sev, "metric": "TSP",
                       "title": f"场界 TSP {tsp['latest']} mg/m³ 超标（限值 {tsp['threshold']}）",
                       "detail": f"趋势：{tsp['trend']}，连续超标 {tsp['max_consecutive_exceed']} 点；"
                                 f"{background['conclusion'] if background else '无背景 PM10 数据，未做修正'}",
                       "kb_file": "01-扬尘-红线.md"})
    elif tsp["status"] == "NEAR":
        alerts.append({"level": "YELLOW", "metric": "TSP",
                       "title": f"TSP {tsp['latest']} 已达限值 90%，且趋势 {tsp['trend']}",
                       "detail": "建议提前开启喷淋、检查防尘网", "kb_file": "01-扬尘-红线.md"})

    if breathing and breathing["status"] == "EXCEED":
        alerts.append({"level": "ORANGE", "metric": "BREATHING_DUST",
                       "title": f"呼吸带{breathing['dust_type']}折算约 {breathing['estimated_mid']} mg/m³，"
                                f"超职业接触限值 {breathing['yellow_limit_respirable']}",
                       "detail": f"存在尘肺病累积剂量风险，须佩戴{breathing['mask_advice']}、缩短连续作业时间",
                       "kb_file": "02-扬尘-黄线.md"})

    if noise["status"] == "EXCEED":
        alerts.append({"level": "RED", "metric": "NOISE",
                       "title": f"场界噪声 {noise['latest']} dB(A) 超{'夜间' if is_night else '昼间'}限值 {noise['threshold']}",
                       "detail": "夜间施工须有县级以上主管部门证明并公告居民" if is_night else "排查高噪设备、设置隔声屏障",
                       "kb_file": "03-噪声-红线.md"})
    if worker_noise and worker_noise["status"] == "EXCEED":
        alerts.append({"level": "ORANGE", "metric": "WORKER_NOISE",
                       "title": f"作业面噪声估算 {worker_noise['estimated']} dB(A)，超 85 dB 职业限值",
                       "detail": "噪声性耳聋风险，须佩戴耳塞耳罩，+3dB 接触时间减半",
                       "kb_file": "04-噪声-黄线.md"})

    if heat and heat["level"] in ("RED", "ORANGE"):
        alerts.append({"level": heat["level"], "metric": "TEMP",
                       "title": f"气温 {temp['latest']}℃ 触发高温作业{'红线' if heat['level'] == 'RED' else '黄线'}",
                       "detail": heat["rule"] + "；落实防暑饮品、休息场所与高温津贴",
                       "kb_file": "05-高温.md"})
    return alerts


def _risk_score(alerts) -> int:
    score = 0
    for a in alerts:
        score += {"RED": 30, "ORANGE": 12, "YELLOW": 3}.get(a["level"], 0)
    return min(score, 100)


def _time_range(df: pd.DataFrame) -> str:
    if "TIME" not in df or df["TIME"].dropna().empty:
        return f"{len(df)} 个等间隔测点"
    t = df["TIME"].dropna()
    return f"{t.iloc[0]:%Y-%m-%d %H:%M} ~ {t.iloc[-1]:%H:%M}（{len(df)} 点）"


def level_from_alerts(alerts) -> str:
    if any(a["level"] == "RED" for a in alerts):
        return "RED"
    if any(a["level"] == "ORANGE" for a in alerts):
        return "ORANGE"
    if any(a["level"] == "YELLOW" for a in alerts):
        return "YELLOW"
    return "GREEN"
