"""Cross-entrypoint contracts for the preserved demo workflow and API envelope."""

from pathlib import Path

import pandas as pd

from core import config
from core.analytics import compute_features
from core.demo import demo_sensor_result, demo_vision_result
from core.reporting import sensor_to_markdown, vision_to_markdown


def test_demo_results_keep_report_contracts():
    vision = demo_vision_result()
    frame = pd.read_csv(Path(__file__).parents[2] / "data" / "sample_sensor.csv")
    features = compute_features(frame, config.STAGES[0], next(iter(config.WORK_TYPES)), False, "")
    sensor = demo_sensor_result(features)
    context = {"stage": config.STAGES[0], "work_type": next(iter(config.WORK_TYPES)), "is_night": False, "city": ""}
    assert {"overall", "findings"} <= vision.keys()
    assert {"overall", "warnings", "metric_reports"} <= sensor.keys()
    assert "F01" in vision_to_markdown(vision, context)
    assert isinstance(sensor_to_markdown(sensor, features, context), str)


def test_api_health_envelope_contract():
    from fastapi.testclient import TestClient
    from backend.main import app

    body = TestClient(app).get("/api/health").json()
    assert {"ok", "data", "error", "request_id"} <= body.keys()
    assert body["ok"] is True
