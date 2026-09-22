import pandas as pd
from core.analytics import compute_features
from core.demo import demo_sensor_result
from core.llm import analyze_sensors
from core.knowledge import build_rule_digest
from .runtime import knowledge, llm_config
def features(rows, context):
    if not rows: raise ValueError("数据行不能为空")
    return compute_features(pd.DataFrame(rows), context.get("stage", ""), context.get("work_type", ""), context.get("is_night", False), context.get("city", ""))
def analyze(data, context=None, demo=True):
    context = context or {}
    cfg = llm_config()
    if demo or not cfg.api_key:
        return demo_sensor_result(data)
    return analyze_sensors(cfg, data, context, build_rule_digest(knowledge()))
