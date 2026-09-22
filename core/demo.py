# -*- coding: utf-8 -*-
"""
尘安智眼 v4 —— 离线演示样例
无 API Key / 断网 / 路演现场网络不稳时，保证完整交互链路可演示：
  · 视觉：data/demo_site.jpg + 与画面标定好的结构化结果（检测框可直接叠加）；
  · 数据：基于 features 实时数值拼装研判结果，保证数字与图表一致。
"""
from __future__ import annotations

import os

DEMO_IMAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "data", "demo_site.jpg")


def demo_vision_result() -> dict:
    """与 data/demo_site.jpg 画面逐一标定的演示结果（归一化 0~999 坐标）。"""
    return {
        "schema_version": "vision/v2",
        "image_quality": {"usable": True, "note": "白天广角、光照良好，远处构件细节略模糊"},
        "scene": {"stage_guess": "土方/地基处理阶段", "key_areas": ["土方作业区", "材料加工区", "基坑临边"]},
        "overall": {
            "risk_level": "RED", "risk_score": 92,
            "disposition": "立即整改，涉事挖掘机停止作业",
            "headline": "发现4项红线隐患：机械冒黑烟、裸土未覆盖、未湿法作业、道路未硬化，扬尘与尾气叠加暴露"},
        "findings": [
            {"id": "F01", "category_code": "EXHAUST", "item": "挖掘机持续冒浓黑烟",
             "severity": "RED", "danger_level": 4, "confidence": 0.95, "immediate_danger": False,
             "bbox": [590, 220, 845, 540], "location_desc": "画面右侧土方作业的黄色挖掘机及烟羽",
             "visual_evidence": "挖掘机排气口持续排出浓黑烟雾并向画面右上方扩散，持续时间明显超过3秒",
             "accident_chain": "柴油燃烧不充分→颗粒物与NOx无组织排放→区域空气质量恶化+高排放机械违法使用→行政处罚",
             "standard_refs": [{"code": "GB20891-2014", "clause": "", "kb_file": "08-尾气排放.md"},
                               {"code": "HJ1014-2020", "clause": "", "kb_file": "08-尾气排放.md"}],
             "rectification": {"action": "立即停机，检查喷油嘴/空滤/柴油品质，维修达标并核验环保编码标识后方可复工",
                               "deadline_hours": 2, "responsible": "机械管理员", "voice_prompt": None},
             "affected_workers": 3},
            {"id": "F02", "category_code": "DUST_BARE", "item": "大面积裸土堆未覆盖防尘网",
             "severity": "RED", "danger_level": 3, "confidence": 0.96, "immediate_danger": False,
             "bbox": [210, 355, 700, 625], "location_desc": "画面中部两至三处数米高黄土堆",
             "visual_evidence": "黄土堆表面完全裸露，未见任何密目防尘网覆盖，堆顶可见风蚀扬尘纹理",
             "accident_chain": "大风/机械扰动起尘→场界TSP超标→PM10背景抬升与工人矽尘暴露→罚款并责令整改",
             "standard_refs": [{"code": "大气污染防治法第69/115条", "clause": "", "kb_file": "01-扬尘-红线.md"},
                               {"code": "DB61/1078-2017", "clause": "", "kb_file": "01-扬尘-红线.md"}],
             "rectification": {"action": "立即用密目防尘网100%覆盖并压边固定，堆体四周开启喷淋，落实六个100%",
                               "deadline_hours": 2, "responsible": "扬尘管理员", "voice_prompt": None},
             "affected_workers": 0},
            {"id": "F03", "category_code": "DUST_WET", "item": "土方作业未采取湿法降尘、扬尘烟羽明显",
             "severity": "RED", "danger_level": 3, "confidence": 0.88, "immediate_danger": False,
             "bbox": [470, 420, 760, 545], "location_desc": "挖掘机铲斗作业面及周边弥漫的尘带",
             "visual_evidence": "铲斗挖土处扬起明显尘雾并横向扩散，现场未见雾炮、喷淋或洒水痕迹",
             "accident_chain": "土方开挖无湿法→呼吸带矽尘浓度成倍升高→矽肺不可逆损害+场界TSP超标",
             "standard_refs": [{"code": "DB61/1078-2017", "clause": "", "kb_file": "01-扬尘-红线.md"}],
             "rectification": {"action": "作业面同步洒水/雾炮喷淋，保持土方表面湿润，配备专人负责湿法作业",
                               "deadline_hours": 1, "responsible": "班组长",
                               "voice_prompt": "工友您好，当前扬尘较大，请立即启动喷淋降尘。"},
             "affected_workers": 4},
            {"id": "F04", "category_code": "DUST_ROAD", "item": "场内主要道路未硬化、干燥起尘",
             "severity": "RED", "danger_level": 3, "confidence": 0.9, "immediate_danger": False,
             "bbox": [250, 560, 720, 870], "location_desc": "画面前景中部的施工便道与轮胎印迹",
             "visual_evidence": "道路为裸露土路，表面浮土厚重、车辙清晰，无硬化或洒水痕迹",
             "accident_chain": "车辆碾压带尘+带泥上路→道路扬尘与市政道路污染→六个100%不达标",
             "standard_refs": [{"code": "大气污染防治法第69条", "clause": "", "kb_file": "01-扬尘-红线.md"}],
             "rectification": {"action": "主要通道铺设硬化路面或钢板，定时洒水清扫，出入口设置洗车槽",
                               "deadline_hours": 24, "responsible": "文明施工员", "voice_prompt": None},
             "affected_workers": 0},
            {"id": "F05", "category_code": "SEWAGE", "item": "现场泥浆积水、未见三级沉淀池",
             "severity": "ORANGE", "danger_level": 2, "confidence": 0.62, "immediate_danger": False,
             "bbox": [490, 760, 999, 999], "location_desc": "画面右下角黄褐色积水坑",
             "visual_evidence": "基坑边存在大片黄褐色泥浆积水，画面内未见沉淀池或导流沟，存在漫流/直排风险",
             "accident_chain": "泥浆漫流或直排管网/河道→水体污染→违反水污染防治法",
             "standard_refs": [{"code": "水污染防治法", "clause": "", "kb_file": "10-污水泥浆.md"}],
             "rectification": {"action": "设置围挡与三级沉淀池，泥浆经沉淀达标后回用/排放，定期清淤",
                               "deadline_hours": 24, "responsible": "环保员", "voice_prompt": None},
             "affected_workers": 0},
            {"id": "F06", "category_code": "SCAFFOLD", "item": "左侧脚手架未见剪刀撑，整体性存疑",
             "severity": "ORANGE", "danger_level": 3, "confidence": 0.58, "immediate_danger": True,
             "bbox": [0, 60, 120, 660], "location_desc": "画面最左侧高耸的钢管脚手架/支模架",
             "visual_evidence": "可见立杆与水平杆，但画面范围内未见连续剪刀撑与明显连墙件，距离较远需近景复检",
             "accident_chain": "整体稳定性不足→架体失稳坍塌→群伤",
             "standard_refs": [{"code": "JGJ130-2011", "clause": "", "kb_file": None}],
             "rectification": {"action": "立即停止该架体上作业，由架子工近景核验剪刀撑、连墙件与脚手板，验收合格后复工",
                               "deadline_hours": 2, "responsible": "专职安全员",
                               "voice_prompt": "工友您好，上方架体正在检查，请先撤离到安全区域。"},
             "affected_workers": 2},
        ],
        "stats": {"red": 4, "orange": 2, "yellow": 0, "total": 6},
        "uncertainties": ["前景工人安全帽、反光背心佩戴规范，未计为隐患",
                          "脚手架距离较远，剪刀撑/连墙件需近景复核后再定级"]
    }


def demo_sensor_result(features: dict) -> dict:
    """根据真实计算出的 features 拼装演示研判，保证与图表数值一致。"""
    L = features["latest"]
    tsp = features["metrics"]["TSP"]
    noise = features["metrics"]["NOISE"]
    temp = features["metrics"]["TEMP"]
    bz = features.get("breathing_zone") or {}
    wn = features.get("worker_noise") or {}
    wbgt = (features.get("wbgt") or {}).get("value")
    return {
        "schema_version": "sensor/v2",
        "data_quality": features["data_quality"] | {"note": "各测点连续无掉点，数据可信，可用于执法级判定"},
        "overall": {"risk_level": "RED", "risk_score": features["risk_score"],
                    "disposition": "立即整改：停止涉尘土方作业面施工并启动应急降尘",
                    "headline": "TSP 持续上升并超标、作业面粉尘严重超标，叠加 37℃ 高温，职业健康与环保红线双触发"},
        "metric_reports": [
            {"metric": "TSP", "metric_name": "场界总悬浮颗粒物", "status": tsp["status"], "level": "RED",
             "current": L["TSP"], "unit": "mg/m³", "threshold": tsp["threshold"],
             "trend": tsp["trend"],
             "trend_evidence": f"监测时段内由 {tsp['min']} 升至最高 {tsp['max']}，斜率约 {tsp['slope_per_hour']} mg/(m³·h)，"
                               f"最长连续超标 {tsp['max_consecutive_exceed']} 点",
             "physical_mechanism": "TSP 单调上升通常对应湿法降尘失效与土方作业面扩大；颗粒物随东南风扩散将抬升周边 PM10，"
                                   "并在工人呼吸带富集，矽尘可致不可逆的矽肺病",
             "standard_refs": [{"code": "DB61/1078-2017", "kb_file": "01-扬尘-红线.md"},
                               {"code": "GB16297-1996", "kb_file": "01-扬尘-红线.md"}],
             "actions": ["立即开启全场喷淋与雾炮", "暂停扬尘最大的土方作业面", "检查并补盖防尘网", "加密监测频次至每15分钟一次"]},
            {"metric": "BREATHING_DUST", "metric_name": "呼吸带粉尘折算", "status": bz.get("status", "EXCEED"),
             "level": "RED", "current": bz.get("estimated_mid"), "unit": "mg/m³",
             "threshold": bz.get("yellow_limit_respirable"), "trend": tsp["trend"],
             "trend_evidence": f"按{features['context']['work_type']}系数 {bz.get('factor_low')}~{bz.get('factor_high')} 折算",
             "physical_mechanism": f"呼吸带{bz.get('dust_type')}估算 {bz.get('estimated_low')}~{bz.get('estimated_high')} mg/m³，"
                                   f"中值 {bz.get('estimated_mid')} 远超职业接触限值 {bz.get('yellow_limit_respirable')}，"
                                   "属慢性不可逆损害，剂量越高发病越早",
             "standard_refs": [{"code": "GBZ2.1-2019", "kb_file": "02-扬尘-黄线.md"}],
             "actions": ["佩戴 KN95 及以上防尘口罩并检查密合", "每作业2小时休息15分钟", "安排职业健康体检（胸片+肺功能）"]},
            {"metric": "NOISE", "metric_name": "场界噪声", "status": noise["status"],
             "level": "RED" if noise["status"] == "EXCEED" else "NORMAL",
             "current": L["NOISE"], "unit": "dB(A)", "threshold": noise["threshold"], "trend": noise["trend"],
             "trend_evidence": f"最新 {L['NOISE']} dB(A)，昼间限值 70；作业面估算约 {wn.get('estimated')} dB(A)",
             "physical_mechanism": "dB 为对数尺度，能量每+3dB 接触时间须减半；作业面持续高于85dB 将造成噪声性耳聋",
             "standard_refs": [{"code": "GB12523-2025", "kb_file": "03-噪声-红线.md"},
                               {"code": "GBZ2.2-2007", "kb_file": "04-噪声-黄线.md"}],
             "actions": ["高噪设备加装隔声/消声装置", "作业人员佩戴耳塞耳罩", "合理安排高噪工序时段"]},
            {"metric": "TEMP", "metric_name": "气温与高温作业", "status": temp["status"],
             "level": "RED" if (L["TEMP"] or 0) >= 37 else "ORANGE" if (L["TEMP"] or 0) >= 35 else "NORMAL",
             "current": L["TEMP"], "unit": "℃", "threshold": 35, "trend": temp["trend"],
             "trend_evidence": f"气温升至 {L['TEMP']}℃，湿度 {L['HUM']}%，估算 WBGT≈{wbgt}℃（重体力≥25 即属高温作业）",
             "physical_mechanism": "高气温叠加中等湿度使汗液蒸发受阻，热蓄积可致热射病；同时高温加速混凝土水分蒸发，"
                                   "坍落度损失快、初凝提前，易形成冷缝与塑性收缩裂缝",
             "standard_refs": [{"code": "安监总安健〔2012〕89号", "kb_file": "05-高温.md"}],
             "actions": ["室外作业累计不超过6小时、最高温3小时停止室外作业", "供应防暑饮品、设阴凉休息点",
                         "35℃以上足额发放高温津贴", "混凝土浇筑避开11:00-15:00并加强覆膜保湿养护"]},
        ],
        "coupled_synthesis": "高温、低湿与土方扬尘同向叠加：干燥大气加速尘粒扩散，TSP 与呼吸带粉尘同步走高；"
                             "作业人员同时承受粉尘、噪声与热辐射三重职业危害，午间事故率与中暑风险显著上升，"
                             "属必须立即干预的复合型高风险工况。",
        "process_window": {
            "concrete_pouring": {"suitable": False,
                                 "reason": f"气温 {L['TEMP']}℃、湿度仅 {L['HUM']}%，水分蒸发剧烈，浇筑质量风险高",
                                 "measures": ["避开11:00-15:00浇筑", "骨料遮阳洒水降温、掺缓凝型减水剂",
                                              "浇筑后立即喷雾并覆膜/土工布保湿养护", "加强入模温度与测温频次"]},
            "outdoor_work": {"suitable": False,
                             "reason": "处于37~40℃法定区间且扬尘超标",
                             "measures": ["室外露天作业累计≤6小时", "最高温3小时内停止室外作业",
                                          "涉尘岗位KN95+轮岗", "防暑饮品与应急药品到位"]}},
        "warnings": [
            {"level": "RED", "metric": "TSP", "title": "场界 TSP 持续超标且仍在上升",
             "detail": f"最新 {L['TSP']} mg/m³，超土方阶段限值 {tsp['threshold']}；呼吸带折算 {bz.get('estimated_mid')} mg/m³，"
                       f"远超矽尘呼尘限值 0.7", "deadline_hours": 1},
            {"level": "RED", "metric": "NOISE", "title": f"场界噪声 {L['NOISE']} dB(A) 昼间超标",
             "detail": f"作业面估算 {wn.get('estimated')} dB(A)，超 85dB 职业限值", "deadline_hours": 2},
            {"level": "ORANGE", "metric": "TEMP", "title": f"气温 {L['TEMP']}℃ 触发高温作业管控",
             "detail": f"估算 WBGT≈{wbgt}℃，须限时作业并落实防暑与津贴", "deadline_hours": 4}],
        "forecast": "若喷淋继续缺失，按当前斜率 TSP 约 1 小时内逼近 1.0 mg/m³ 国标红线；午后 14 时前后气温与臭氧/扬尘复合污染将达峰值。",
        "report_markdown": _demo_markdown(features)
    }


def _demo_markdown(f: dict) -> str:
    L = f["latest"]
    return f"""### 🌡️ 传感器数据专业研判报告（演示）
**监测时段**：{f['time_range']}　**城市/阶段**：{f['context']['city']} / {f['context']['stage']}

| 指标 | 最新值 | 限值 | 趋势 | 结论 |
|---|---|---|---|---|
| TSP | {L['TSP']} mg/m³ | {f['context']['tsp_limit']} | {f['metrics']['TSP']['trend']} | 🔴 超标 |
| 噪声 | {L['NOISE']} dB(A) | {f['context']['noise_limit']} | {f['metrics']['NOISE']['trend']} | 🔴 超标 |
| 气温 | {L['TEMP']} ℃ | 35 | {f['metrics']['TEMP']['trend']} | 🟠 高温管控 |
| 湿度 | {L['HUM']} % | — | — | 干燥 |
| 估算WBGT | {(f.get('wbgt') or {}).get('value')} ℃ | 25 | — | 高温作业 |

**核心研判**：TSP 持续上升并突破地标限值，呼吸带矽尘严重超标；噪声场界与作业面双超标；"
高温低湿加剧扬尘扩散与中暑风险，并对混凝土浇筑质量构成威胁。

**工艺窗口**：当前不适宜午间混凝土浇筑与连续室外重体力作业，须先降尘、再限时作业。
"""
