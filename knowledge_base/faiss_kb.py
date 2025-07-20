import os
import pickle
from typing import List, Optional, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel

from .base import KnowledgeBase


class FAISSKnowledgeBase(KnowledgeBase):
    """基于FAISS的知识库实现"""
    
    def __init__(
        self,
        embedding_model: Embeddings,
        vector_store: Optional[FAISS] = None,
        persist_directory: Optional[str] = None,
        llm: Optional[BaseLanguageModel] = None,
    ):
        """
        初始化FAISS知识库
        
        参数:
            embedding_model: 用于文本嵌入的模型
            vector_store: 已有的FAISS向量存储
            persist_directory: 持久化目录
            llm: 语言模型，用于生成回答
        """
        super().__init__(
            embedding_model=embedding_model,
            vector_store=vector_store,
            vector_store_path=persist_directory,
            llm=llm
        )
    
    def add_documents(self, documents: List[Document], **kwargs) -> None:
        """
        添加文档到FAISS知识库
        
        参数:
            documents: 文档列表
            **kwargs: 额外参数
        """
        if self.vector_store is None:
            # 如果没有初始化向量存储，则创建一个
            self.vector_store = FAISS.from_documents(
                documents, self.embedding_model, **kwargs
            )
        else:
            # 否则添加到现有存储
            self.vector_store.add_documents(documents)
        
    def save(self) -> None:
        """保存FAISS向量存储到磁盘"""
        if self.vector_store_path and self.vector_store:
            # 确保目录存在
            os.makedirs(self.vector_store_path, exist_ok=True)
            
            # 保存FAISS索引
            self.vector_store.save_local(self.vector_store_path)
    
    @classmethod
    def from_documents(
        cls,
        documents: List[Document],
        embedding_model: Embeddings,
        persist_directory: Optional[str] = None,
        llm: Optional[BaseLanguageModel] = None,
        **kwargs
    ) -> "FAISSKnowledgeBase":
        """
        从文档创建新的FAISS知识库
        
        参数:
            documents: 文档列表
            embedding_model: 嵌入模型
            persist_directory: 持久化目录
            llm: 语言模型
            **kwargs: 传递给FAISS.from_documents的额外参数
            
        返回:
            FAISSKnowledgeBase实例
        """
        # 创建向量存储
        vector_store = FAISS.from_documents(
            documents=documents,
            embedding=embedding_model,
            **kwargs
        )
        
        # 创建知识库实例
        knowledge_base = cls(
            embedding_model=embedding_model,
            vector_store=vector_store,
            persist_directory=persist_directory,
            llm=llm
        )
        
        # 如果指定了持久化目录，则保存
        if persist_directory:
            knowledge_base.save()
        
        return knowledge_base
    
    @classmethod
    def load(
        cls,
        embedding_model: Embeddings,
        persist_directory: str,
        llm: Optional[BaseLanguageModel] = None,
        **kwargs
    ) -> "FAISSKnowledgeBase":
        """
        从磁盘加载FAISS知识库
        
        参数:
            embedding_model: 嵌入模型
            persist_directory: 持久化目录
            llm: 语言模型
            **kwargs: 额外参数，包括allow_dangerous_deserialization
            
        返回:
            FAISSKnowledgeBase实例
        """
        if not os.path.exists(persist_directory):
            raise ValueError(f"目录 {persist_directory} 不存在")
            
        # 加载FAISS索引
        vector_store = FAISS.load_local(
            persist_directory,
            embedding_model,
            # 传递所有额外参数，包括allow_dangerous_deserialization
            **kwargs
        )
        
        return cls(
            embedding_model=embedding_model,
            vector_store=vector_store,
            persist_directory=persist_directory,
            llm=llm
        ) 