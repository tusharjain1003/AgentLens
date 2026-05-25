import os
import sys
import types
from dataclasses import dataclass


os.environ.setdefault("DATABASE_URL", "postgresql://weblens:weblens@localhost:5432/weblens")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key")
os.environ.setdefault("DEEPSEEK_API_KEY", "")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("LLM_PROVIDER", "openai")


@dataclass
class ExtractedPage:
    url: str
    title: str
    markdown: str
    char_count: int
    from_cache: bool = False

    def summary(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "char_count": self.char_count,
            "from_cache": self.from_cache,
        }


extract_stub = types.ModuleType("pipeline.extract")
extract_stub.ExtractedPage = ExtractedPage
sys.modules.setdefault("pipeline.extract", extract_stub)

llm_stub = types.ModuleType("llm.openai_client")
llm_stub.get_llm = lambda: None
sys.modules.setdefault("llm.openai_client", llm_stub)

langsmith_stub = types.ModuleType("langsmith")
langsmith_stub.traceable = lambda *args, **kwargs: (lambda fn: fn)
sys.modules.setdefault("langsmith", langsmith_stub)

numpy_stub = types.ModuleType("numpy")
numpy_stub.ndarray = object
numpy_stub.zeros = lambda shape: []
sys.modules.setdefault("numpy", numpy_stub)

embed_stub = types.ModuleType("pipeline.embed")
embed_stub.bm25_search = lambda *args, **kwargs: []
embed_stub.build_bm25 = lambda chunks: (None, None)
embed_stub.embed_texts = lambda texts: []
embed_stub.get_rerank_model = lambda: None
sys.modules.setdefault("pipeline.embed", embed_stub)
