from typing import List, Dict, Any, Optional
import os
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel
from langchain_core.retrievers import BaseRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain


class KnowledgeBase:
    """知识库基类，提供RAG（检索增强生成）功能。"""
    
    def __init__(
        self,
        embedding_model: Embeddings,
        vector_store: Optional[VectorStore] = None,
        vector_store_path: Optional[str] = None,
        llm: Optional[BaseLanguageModel] = None,
    ):
        """
        初始化知识库
        
        参数:
            embedding_model: 用于文本嵌入的模型
            vector_store: 向量存储对象，如果已存在
            vector_store_path: 向量存储的路径，用于持久化
            llm: 语言模型，用于生成回答
        """
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.vector_store_path = vector_store_path
        self.llm = llm
        self.retriever = None
        
    def add_documents(self, documents: List[Document]) -> None:
        """
        添加文档到知识库
        
        参数:
            documents: 文档列表
        """
        if self.vector_store is None:
            raise ValueError("向量存储未初始化")
        
        self.vector_store.add_documents(documents)
        
    def query(self, query: str, top_k: int = 5) -> List[Document]:
        """
        查询知识库，返回相关文档
        
        参数:
            query: 查询文本
            top_k: 返回的文档数量
            
        返回:
            相关文档列表
        """
        if self.retriever is None:
            if self.vector_store is None:
                raise ValueError("向量存储未初始化")
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": top_k})
            
        return self.retriever.get_relevant_documents(query)
    
    def generate_answer(self, query: str, top_k: int = 5) -> str:
        """
        根据查询生成回答
        
        参数:
            query: 查询文本
            top_k: 检索的文档数量
            
        返回:
            生成的回答
        """
        if self.llm is None:
            raise ValueError("语言模型未初始化")
        
        if self.retriever is None:
            if self.vector_store is None:
                raise ValueError("向量存储未初始化")
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": top_k})
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_template("""
        根据以下上下文回答用户问题。如果上下文中没有相关信息，请说明你不知道，不要编造信息。

        上下文：
        {context}
        
        问题：{input}
        """)
        
        # 创建文档链
        document_chain = create_stuff_documents_chain(
            self.llm,
            prompt
        )
        
        # 创建检索链
        retrieval_chain = create_retrieval_chain(
            self.retriever,
            document_chain
        )
        
        # 执行链并返回结果
        response = retrieval_chain.invoke({"input": query})
        return response["answer"]
    
    def save(self) -> None:
        """保存向量存储"""
        if hasattr(self.vector_store, "persist") and self.vector_store_path:
            self.vector_store.persist()
            
    def load(self) -> None:
        """加载向量存储"""
        pass  # 由子类实现具体加载逻辑 