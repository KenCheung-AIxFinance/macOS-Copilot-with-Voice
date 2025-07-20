from typing import Optional, List, Dict, Any, Union, Literal
import os
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel

from .base import KnowledgeBase
from .chroma_kb import ChromaKnowledgeBase
from .faiss_kb import FAISSKnowledgeBase
from .utils import load_documents_from_dir, split_documents, split_markdown_documents


class KnowledgeBaseFactory:
    """知识库工厂类，用于简化知识库的创建和管理"""
    
    @staticmethod
    def create_knowledge_base(
        embedding_model: Embeddings,
        store_type: Literal["chroma", "faiss"] = "chroma",
        documents: Optional[List[Document]] = None,
        persist_directory: Optional[str] = None,
        llm: Optional[BaseLanguageModel] = None,
        collection_name: str = "default",
        **kwargs
    ) -> KnowledgeBase:
        """
        创建知识库
        
        参数:
            embedding_model: 嵌入模型
            store_type: 向量存储类型，"chroma" 或 "faiss"
            documents: 要添加的文档列表
            persist_directory: 持久化目录
            llm: 语言模型
            collection_name: 集合名称（仅对Chroma有效）
            **kwargs: 额外参数
            
        返回:
            KnowledgeBase实例
        """
        if store_type == "chroma":
            if documents:
                return ChromaKnowledgeBase.from_documents(
                    documents=documents,
                    embedding_model=embedding_model,
                    collection_name=collection_name,
                    persist_directory=persist_directory,
                    llm=llm,
                    **kwargs
                )
            else:
                return ChromaKnowledgeBase(
                    embedding_model=embedding_model,
                    collection_name=collection_name,
                    persist_directory=persist_directory,
                    llm=llm,
                    **kwargs
                )
        elif store_type == "faiss":
            if documents:
                return FAISSKnowledgeBase.from_documents(
                    documents=documents,
                    embedding_model=embedding_model,
                    persist_directory=persist_directory,
                    llm=llm,
                    **kwargs
                )
            else:
                return FAISSKnowledgeBase(
                    embedding_model=embedding_model,
                    persist_directory=persist_directory,
                    llm=llm,
                    **kwargs
                )
        else:
            raise ValueError(f"不支持的向量存储类型: {store_type}")
            
    @staticmethod
    def load_knowledge_base(
        embedding_model: Embeddings,
        store_type: Literal["chroma", "faiss"] = "chroma",
        persist_directory: str = None,
        llm: Optional[BaseLanguageModel] = None,
        collection_name: str = "default",
        **kwargs
    ) -> KnowledgeBase:
        """
        加载现有知识库
        
        参数:
            embedding_model: 嵌入模型
            store_type: 向量存储类型，"chroma" 或 "faiss"
            persist_directory: 持久化目录
            llm: 语言模型
            collection_name: 集合名称（仅对Chroma有效）
            **kwargs: 额外参数
            
        返回:
            KnowledgeBase实例
        """
        if not persist_directory:
            raise ValueError("必须提供persist_directory来加载知识库")
            
        if store_type == "chroma":
            return ChromaKnowledgeBase.load(
                embedding_model=embedding_model,
                collection_name=collection_name,
                persist_directory=persist_directory,
                llm=llm,
                **kwargs
            )
        elif store_type == "faiss":
            return FAISSKnowledgeBase.load(
                embedding_model=embedding_model,
                persist_directory=persist_directory,
                llm=llm,
                **kwargs
            )
        else:
            raise ValueError(f"不支持的向量存储类型: {store_type}")
    
    @staticmethod
    def create_from_directory(
        directory_path: str,
        embedding_model: Embeddings,
        store_type: Literal["chroma", "faiss"] = "chroma",
        extensions: Optional[List[str]] = None,
        persist_directory: Optional[str] = None,
        llm: Optional[BaseLanguageModel] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        collection_name: str = "default",
        **kwargs
    ) -> KnowledgeBase:
        """
        从目录创建知识库
        
        参数:
            directory_path: 文档目录路径
            embedding_model: 嵌入模型
            store_type: 向量存储类型
            extensions: 文件扩展名列表，如 [".pdf", ".txt"]
            persist_directory: 持久化目录
            llm: 语言模型
            chunk_size: 文本分块大小
            chunk_overlap: 文本分块重叠大小
            collection_name: 集合名称（仅对Chroma有效）
            **kwargs: 额外参数
            
        返回:
            KnowledgeBase实例
        """
        # 加载目录中的文档
        documents = load_documents_from_dir(directory_path, extensions)
        
        if not documents:
            raise ValueError(f"在目录 {directory_path} 中未找到文档")
        
        # 分割文档
        split_docs = split_documents(documents, chunk_size, chunk_overlap)
        
        # 创建知识库
        return KnowledgeBaseFactory.create_knowledge_base(
            embedding_model=embedding_model,
            store_type=store_type,
            documents=split_docs,
            persist_directory=persist_directory,
            llm=llm,
            collection_name=collection_name,
            **kwargs
        ) 