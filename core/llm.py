# -*- coding: utf-8 -*-
"""
尘安智眼 v4 —— 大模型调用封装（OpenAI 兼容协议，默认智谱 GLM）
健壮性要点：
  · 统一超时、指数退避重试（连接失败/限流/服务端错误）；
  · 鉴权、超时、限流、模型名错误等异常翻译为中文友好提示；
  · JSON 容错：去代码围栏 → 括号截取 → 一次修复重试；
  · 视觉模型与文本模型分离；无 Key / 演示模式走 core.demo 固定样例。
"""
from __future__ import annotations

import json
import re
import base64
import time
from dataclasses import dataclass

from openai import OpenAI
from openai import (APIConnectionError, APITimeoutError, AuthenticationError,
                    BadRequestError, InternalServerError, RateLimitError)

from . import prompts


class LLMError(RuntimeError):
    """面向用户的友好异常。"""


@dataclass
class AppConfig:
    api_key: str = ""
    base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    vision_model: str = "glm-5.3-flash"
    text_model: str = "glm-5.3-flash"
    temperature: float = 0.1
    timeout: int = 45
    demo_mode: bool = False


# ============================ 底层调用 ============================
def _client(cfg: AppConfig) -> OpenAI:
    return OpenAI(api_key=cfg.api_key or "demo", base_url=cfg.base_url, timeout=cfg.timeout)


def _request(cfg: AppConfig, model: str, messages: list, max_tokens: int,
             json_mode: bool = False) -> str:
    if not cfg.api_key:
        raise LLMError("未配置 API Key：请在左侧侧边栏填写，或开启“演示模式”体验完整界面。")
    last_err = None
    for attempt in range(3):
        try:
            kwargs = dict(model=model, messages=messages,
                          temperature=cfg.temperature, max_tokens=max_tokens)
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            try:
                resp = _client(cfg).chat.completions.create(**kwargs)
            except BadRequestError as e:
                # 个别模型不支持 response_format 参数，去掉后重试一次
                if json_mode and "response_format" in str(e):
                    kwargs.pop("response_format", None)
                    resp = _client(cfg).chat.completions.create(**kwargs)
                else:
                    raise
            return resp.choices[0].message.content or ""
        except (APITimeoutError, APIConnectionError, RateLimitError, InternalServerError) as e:
            last_err = e
            if attempt < 2:
                time.sleep(1.5 ** attempt)
                continue
            kind = {APITimeoutError: "模型响应超时，可在侧边栏调大超时时间后重试",
                    APIConnectionError: "无法连接模型服务，请检查网络与 Base URL",
                    RateLimitError: "触发限流或额度不足，请稍后重试或更换模型",
                    InternalServerError: "模型服务暂时异常，请稍后重试"}.get(type(e), "服务异常")
            raise LLMError(kind)
        except AuthenticationError:
            raise LLMError("API Key 无效、过期或欠费，请检查后重试")
        except BadRequestError as e:
            raise LLMError(f"请求被模型拒绝（常见原因：模型名错误、图片过大或不支持该格式）：{str(e)[:160]}")
        except Exception as e:  # noqa: BLE001 - 兜底，避免页面崩溃
            raise LLMError(f"未知调用异常：{str(e)[:160]}")
    raise LLMError(f"调用失败：{last_err}")


def _extract_json_object(text: str) -> str | None:
    """从模型回复中抠出 JSON 对象本体：去代码围栏 → 取最外层花括号。"""
    fence = re.search(r"```(?:json|JSON)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return text[start:end + 1]
    return None


def _parse_json(raw: str, cfg: AppConfig, model: str, messages: list) -> dict:
    # 第一次：直接解析 → 去围栏/截取最外层花括号
    for cand in (raw.strip(), _extract_json_object(raw)):
        if cand:
            try:
                return json.loads(cand)
            except json.JSONDecodeError:
                continue
    # 第二次：让模型自我修复一次（给足输出长度，禁止思考过程与围栏）
    try:
        fixed = _request(cfg, model, messages + [
            {"role": "assistant", "content": raw[:6000]},
            {"role": "user", "content": "你上一条回复不是合法 JSON（可能被截断或夹带了思考过程）。"
                                        "请严格按约定 Schema 重新【完整】输出，只输出一个 JSON 对象，"
                                        "不要输出思考过程、解释文字或代码围栏。"}], 8192, json_mode=True)
        body = _extract_json_object(fixed) or fixed
        return json.loads(body)
    except (LLMError, json.JSONDecodeError):
        snippet = re.sub(r"\s+", " ", raw)[:150]
        raise LLMError("模型返回内容无法解析为结构化 JSON（多为输出被截断或未按约定格式返回）。"
                       f"返回片段：{snippet}…… 建议：在 ?admin=1 中换用 glm-5.3 旗舰模型后重试。")


# ============================ 业务调用 ============================
def analyze_image(cfg: AppConfig, image_bytes: bytes, mime: str,
                  context: dict, rule_digest: str) -> dict:
    system = prompts.build_vision_system_prompt(
        rule_digest, context["stage"], context["work_type"], context["is_night"])
    b64 = base64.b64encode(image_bytes).decode()
    user_content = [
        {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
        {"type": "text", "text": "请按系统约定执行现场巡检并只输出 JSON。检查上下文："
                                  + json.dumps(context, ensure_ascii=False)},
    ]
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": user_content}]
    raw = _request(cfg, cfg.vision_model, messages, max_tokens=8192, json_mode=True)
    data = _parse_json(raw, cfg, cfg.vision_model, messages)
    _require(data, ("overall", "findings"))
    return data


def analyze_sensors(cfg: AppConfig, features: dict, context: dict, rule_digest: str) -> dict:
    system = prompts.build_sensor_system_prompt(
        rule_digest, context["stage"], context["work_type"], context["is_night"])
    payload = {"检查上下文": context, "探头时序特征features": features}
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": "以下是程序计算好的特征 JSON，请据此研判并只输出约定 JSON：\n"
                                             + json.dumps(payload, ensure_ascii=False, default=str)}]
    raw = _request(cfg, cfg.text_model, messages, max_tokens=8192, json_mode=True)
    data = _parse_json(raw, cfg, cfg.text_model, messages)
    _require(data, ("overall", "metric_reports"))
    return data


def _require(data: dict, keys):
    if not isinstance(data, dict) or not all(k in data for k in keys):
        raise LLMError("模型返回 JSON 缺少必需字段，请重试或更换模型")
