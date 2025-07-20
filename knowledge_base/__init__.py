# knowledge_base 库初始化文件

from .base import KnowledgeBase
from .chroma_kb import ChromaKnowledgeBase
from .faiss_kb import FAISSKnowledgeBase
from .factory import KnowledgeBaseFactory
from .utils import (
    example_util_func,
    get_document_loader,
    load_document,
    load_documents_from_dir,
    split_documents,
    split_markdown_documents,
)

__all__ = [
    "KnowledgeBase",
    "ChromaKnowledgeBase",
    "FAISSKnowledgeBase",
    "KnowledgeBaseFactory",
    "example_util_func",
    "get_document_loader",
    "load_document",
    "load_documents_from_dir",
    "split_documents",
    "split_markdown_documents",
] 