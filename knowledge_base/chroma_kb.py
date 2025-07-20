import os
from typing import List, Optional, Dict, Any
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel

from .base import KnowledgeBase


class ChromaKnowledgeBase(KnowledgeBase):
    """基于Chroma的知识库实现"""
    
    def __init__(
        self,
        embedding_model: Embeddings,
        collection_name: str = "default",
        persist_directory: Optional[str] = None,
        llm: Optional[BaseLanguageModel] = None,
        client_settings: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化Chroma知识库
        
        参数:
            embedding_model: 用于文本嵌入的模型
            collection_name: Chroma集合名称
            persist_directory: 持久化目录
            llm: 语言模型，用于生成回答
            client_settings: Chroma客户端设置
        """
        # 创建或加载向量存储
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_model,
            persist_directory=persist_directory,
            client_settings=client_settings,
        )
        
        super().__init__(
            embedding_model=embedding_model,
            vector_store=vector_store,
            vector_store_path=persist_directory,
            llm=llm
        )
        
        self.collection_name = collection_name
    
    def add_documents(self, documents: List[Document], **kwargs) -> None:
        """
        添加文档到Chroma知识库
        
        参数:
            documents: 文档列表
            **kwargs: 传递给Chroma.add_documents的额外参数
        """
        self.vector_store.add_documents(documents, **kwargs)
        
    def save(self) -> None:
        """保存Chroma向量存储"""
        if self.vector_store_path:
            # 检查方法是否存在，因为较新版本的Chroma可能使用不同的方法
            if hasattr(self.vector_store, "_persist"):
                self.vector_store._persist()
            elif hasattr(self.vector_store, "persist"):
                self.vector_store.persist()
            else:
                print("警告: 无法找到Chroma的持久化方法")
            
    @classmethod
    def from_documents(
        cls,
        documents: List[Document],
        embedding_model: Embeddings,
        collection_name: str = "default",
        persist_directory: Optional[str] = None,
        llm: Optional[BaseLanguageModel] = None,
        client_settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> "ChromaKnowledgeBase":
        """
        从文档创建新的Chroma知识库
        
        参数:
            documents: 文档列表
            embedding_model: 嵌入模型
            collection_name: 集合名称
            persist_directory: 持久化目录
            llm: 语言模型
            client_settings: Chroma客户端设置
            **kwargs: 传递给Chroma.from_documents的额外参数
            
        返回:
            ChromaKnowledgeBase实例
        """
        # 创建向量存储
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=embedding_model,
            collection_name=collection_name,
            persist_directory=persist_directory,
            client_settings=client_settings,
            **kwargs
        )
        
        # 创建知识库实例
        knowledge_base = cls(
            embedding_model=embedding_model,
            collection_name=collection_name,
            persist_directory=persist_directory,
            llm=llm,
            client_settings=client_settings,
        )
        
        # 更新向量存储
        knowledge_base.vector_store = vector_store
        
        return knowledge_base
    
    @classmethod
    def load(
        cls,
        embedding_model: Embeddings,
        collection_name: str = "default",
        persist_directory: Optional[str] = None,
        llm: Optional[BaseLanguageModel] = None,
        client_settings: Optional[Dict[str, Any]] = None,
    ) -> "ChromaKnowledgeBase":
        """
        加载现有的Chroma知识库
        
        参数:
            embedding_model: 嵌入模型
            collection_name: 集合名称
            persist_directory: 持久化目录
            llm: 语言模型
            client_settings: Chroma客户端设置
            
        返回:
            ChromaKnowledgeBase实例
        """
        return cls(
            embedding_model=embedding_model,
            collection_name=collection_name,
            persist_directory=persist_directory,
            llm=llm,
            client_settings=client_settings,
        ) 