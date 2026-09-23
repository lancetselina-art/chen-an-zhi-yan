from pathlib import Path

from core.demo import demo_vision_result
from core.knowledge import build_rule_digest
from core.llm import analyze_image
from .runtime import knowledge, llm_config

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_IMAGE = PROJECT_ROOT / 'data' / 'demo_site.jpg'
DEMO_OVERLAY = PROJECT_ROOT / 'data' / 'overlay_demo.jpg'


def demo_asset_path(kind: str) -> Path:
    assets = {'input': DEMO_IMAGE, 'overlay': DEMO_OVERLAY}
    try:
        path = assets[kind]
    except KeyError as exc:
        raise ValueError('未知的演示资源') from exc
    if not path.is_file():
        raise FileNotFoundError(f'演示资源不存在: {path.name}')
    return path


def analyze(image: bytes | None, mime: str, context: dict, demo: bool = True):
    if demo:
        demo_asset_path('input')
        demo_asset_path('overlay')
        result = demo_vision_result()
        result.update({
            'input_image_url': '/api/vision/demo/input',
            'overlay_image_url': '/api/vision/demo/overlay',
        })
        return result
    if not image:
        raise ValueError('请上传现场图片')
    if not llm_config().api_key:
        return demo_vision_result()
    return analyze_image(llm_config(), image, mime.split('/')[-1], context, build_rule_digest(knowledge()))
