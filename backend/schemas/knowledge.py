from pydantic import BaseModel
class SearchResult(BaseModel):
    file: str
    score: int | float
    snippet: str
