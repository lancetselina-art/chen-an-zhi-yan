from core.demo import demo_vision_result
from core.knowledge import build_rule_digest
from core.llm import analyze_image
from .runtime import knowledge, llm_config
def analyze(image: bytes, mime: str, context: dict, demo: bool = True):
    if demo or not llm_config().api_key:
        return demo_vision_result()
    return analyze_image(llm_config(), image, mime.split('/')[-1], context, build_rule_digest(knowledge()))
