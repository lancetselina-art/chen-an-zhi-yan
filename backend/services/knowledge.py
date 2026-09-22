from core.knowledge import search_kb
from .runtime import KNOWLEDGE_DIR, knowledge

def source_directory() -> str:
    """Return the single local knowledge source used by every API search."""
    return str(KNOWLEDGE_DIR)

def search(query):
    return [{"file": f, "score": s, "snippet": sn} for f,s,sn in search_kb(knowledge(), query)]
def get_file(name):
    if name not in knowledge(): raise FileNotFoundError(name)
    return knowledge()[name]
