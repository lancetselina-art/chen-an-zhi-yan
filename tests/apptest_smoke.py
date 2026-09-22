# -*- coding: utf-8 -*-
"""Streamlit AppTest：无头跑通完整脚本，并模拟点击演示模式下的视觉/数据两条链路。
运行：python tests/apptest_smoke.py
"""
import os
import sys

from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app.py")


def click(at, label):
    for b in at.button:
        if label in b.label:
            b.click().run()
            return True
    return False


at = AppTest.from_file(APP, default_timeout=60)
at.run()
assert not at.exception, [(e.exception_type, e.message) for e in at.exception]
print("[OK] 应用首次加载无异常；tabs =", [t.label for t in at.tabs])

# 演示模式默认开启（无 API Key）
# 1) 视觉巡检
assert click(at, "开始 AI 视觉巡检"), "未找到视觉巡检按钮"
assert not at.exception, [(e.exception_type, e.message) for e in at.exception]
metrics = [m.label for m in at.metric]
assert any("红线" in x for x in metrics), metrics
print("[OK] 视觉巡检链路：检测框/指标/工单渲染，metric =", metrics[:4])

# 2) 传感器研判（默认 CSV 演示数据）
assert click(at, "生成 AI 专业研判报告"), "未找到数据研判按钮"
assert not at.exception, [(e.exception_type, e.message) for e in at.exception]
print("[OK] 传感器研判链路：图表/预警/工艺窗口渲染，展开器数量 =", len(at.expander))

# 3) 两次分析均应写入会话台账（success 提示出现）
joined = " ".join(s.value for s in at.success)
assert "检查台账" in joined, joined
print("[OK] 报告已写入检查台账")
print("\nAppTest 全链路通过 ✅")
