# -*- coding: utf-8 -*-
"""离线冒烟测试：不依赖 API Key，验证知识库/特征工程/Prompt/绘图/检测框/报告全链路。
运行：python tests/smoke_test.py
"""
import io
import os
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pandas as pd
from PIL import Image

from core import config as C
from core import knowledge as KB
from core import analytics as A
from core import charts as CH
from core import vision_overlay as VO
from core import reporting as R
from core import prompts as P
from core import demo as DEMO

ok = lambda name: print(f"[OK] {name}")

# 1. 知识库
kb = KB.load_local_kb()
assert len(kb) >= 11, len(kb)
digest = KB.build_rule_digest(kb)
assert len(digest) > 500 and len(digest) < len("".join(kb.values()))
print(f"知识库 {len(kb)} 份；原文 {sum(len(v) for v in kb.values())} 字 → 精要 {len(digest)} 字")
ok("知识库加载与精要压缩")

# 2. 映射
files = KB.files_for_categories(["DUST_BARE", "EXHAUST", "FIRE"])
assert "01-扬尘-红线.md" in files and "08-尾气排放.md" in files
bundle = KB.get_clause_bundle(kb, files + ["99-不存在.md"])
ok("隐患→知识库映射（含缺失占位）")

# 3. Prompt 构建
sp1 = P.build_vision_system_prompt(digest, C.STAGES[0], "土方开挖/拆除", False)
sp2 = P.build_sensor_system_prompt(digest, C.STAGES[0], "土方开挖/拆除", False)
assert "schema_version" in sp1 and "schema_version" in sp2 and "JSON" in sp1
ok("两套黄金 Prompt 构建")

# 4. 特征工程
df = pd.read_csv(os.path.join(ROOT, "data", "sample_sensor.csv"))
f = A.compute_features(df, C.STAGES[0], "土方开挖/拆除", False, "西安")
assert f["metrics"]["TSP"]["status"] == "EXCEED", f["metrics"]["TSP"]
assert f["metrics"]["NOISE"]["status"] == "EXCEED"
assert f["breathing_zone"]["status"] == "EXCEED"
assert f["wbgt"]["value"] is not None
print("TSP:", f["metrics"]["TSP"]["latest"], "趋势", f["metrics"]["TSP"]["trend"],
      "| WBGT:", f["wbgt"]["value"], "| 呼吸带中值:", f["breathing_zone"]["estimated_mid"],
      "| 预警数:", len(f["deterministic_alerts"]), "| 风险分:", f["risk_score"])
ok("时序特征工程与确定性预警")

# 5. 演示研判结果
sr = DEMO.demo_sensor_result(f)
json.dumps(sr, ensure_ascii=False)  # 可序列化
assert len(sr["metric_reports"]) >= 4 and sr["overall"]["risk_level"] == "RED"
ok("传感器演示研判结果")

# 6. 视觉演示结果 + 检测框
vr = DEMO.demo_vision_result()
json.dumps(vr, ensure_ascii=False)
img = Image.open(DEMO.DEMO_IMAGE)
out = VO.draw_findings(img, vr)
out_path = os.path.join(ROOT, "data", "overlay_demo.jpg")
out.save(out_path, quality=90)
assert os.path.getsize(out_path) > 50000
ok(f"检测框叠加 → {out_path}")

# 7. 图表（plotly）
fig1 = CH.sensor_figure(A.canonicalize(df), f)
fig2 = CH.risk_gauge(92, "RED")
assert fig1 is not None and fig2 is not None
ok("Plotly 时序图与风险仪表盘")

# 8. 报告
ctx = {"stage": C.STAGES[0], "work_type": "土方开挖/拆除", "is_night": False, "city": "西安"}
md1 = R.vision_to_markdown(vr, ctx)
md2 = R.sensor_to_markdown(sr, f, ctx)
assert "F01" in md1 and "研判报告" in md2
ok("Markdown 报告生成")

print("\n全部冒烟测试通过 ✅")
