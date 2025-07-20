from typing import List, Dict, Any, Optional, Union, Literal
import os
import tempfile
import shutil
from pathlib import Path
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

import knowledge_base as kb
from knowledge_base import KnowledgeBase, KnowledgeBaseFactory


class KnowledgeBaseModel:
    """知识库模型接口，用于连接UI和底层知识库功能"""
    
    def __init__(
        self,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model_name: str = "gpt-3.5-turbo",
        store_type: Literal["chroma", "faiss"] = "chroma",
        persist_directory: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        初始化知识库模型
        
        参数:
            embedding_model_name: 嵌入模型名称或OpenAI模型名称
            llm_model_name: LLM模型名称
            store_type: 向量存储类型，"chroma" 或 "faiss"
            persist_directory: 持久化目录
            api_key: API密钥（如果使用OpenAI模型）
        """
        self.embedding_model_name = embedding_model_name
        self.llm_model_name = llm_model_name
        self.store_type = store_type
        self.persist_directory = persist_directory
        self.api_key = api_key
        
        # 初始化嵌入模型
        if "openai" in embedding_model_name.lower():
            self.embedding_model = OpenAIEmbeddings(
                model=embedding_model_name,
                openai_api_key=api_key
            )
        else:
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=embedding_model_name
            )
            
        # 初始化语言模型
        if api_key:
            self.llm = ChatOpenAI(
                model_name=llm_model_name,
                openai_api_key=api_key,
                temperature=0.2
            )
        else:
            self.llm = None
            
        self.knowledge_base = None
        
        # 如果提供了持久化目录，尝试加载现有知识库
        if persist_directory and os.path.exists(persist_directory):
            try:
                self.knowledge_base = KnowledgeBaseFactory.load_knowledge_base(
                    embedding_model=self.embedding_model,
                    store_type=store_type,
                    persist_directory=persist_directory,
                    llm=self.llm
                )
            except Exception as e:
                print(f"加载知识库失败: {str(e)}")
        
    def create_knowledge_base(self, collection_name: str = "default") -> bool:
        """
        创建空知识库
        
        参数:
            collection_name: 集合名称
            
        返回:
            是否成功
        """
        try:
            self.knowledge_base = KnowledgeBaseFactory.create_knowledge_base(
                embedding_model=self.embedding_model,
                store_type=self.store_type,
                persist_directory=self.persist_directory,
                llm=self.llm,
                collection_name=collection_name
            )
            return True
        except Exception as e:
            print(f"创建知识库失败: {str(e)}")
            return False
            
    def add_documents(self, documents: List[Document]) -> bool:
        """
        添加文档到知识库
        
        参数:
            documents: 文档列表
            
        返回:
            是否成功
        """
        if not self.knowledge_base:
            return False
            
        try:
            self.knowledge_base.add_documents(documents)
            if self.persist_directory:
                self.knowledge_base.save()
            return True
        except Exception as e:
            print(f"添加文档失败: {str(e)}")
            return False
    
    def add_files(
        self,
        file_paths: List[str],
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """
        添加文件到知识库
        
        参数:
            file_paths: 文件路径列表
            chunk_size: 文本分块大小
            chunk_overlap: 文本分块重叠大小
            
        返回:
            处理结果字典
        """
        if not self.knowledge_base:
            return {"success": False, "message": "知识库未初始化", "processed": 0, "failed": len(file_paths)}
            
        processed = 0
        failed = 0
        failed_files = []
        
        for file_path in file_paths:
            try:
                # 加载文档
                docs = kb.load_document(file_path)
                
                # 分割文档
                split_docs = kb.split_documents(docs, chunk_size, chunk_overlap)
                
                # 添加到知识库
                self.knowledge_base.add_documents(split_docs)
                processed += 1
            except Exception as e:
                print(f"处理文件 {file_path} 失败: {str(e)}")
                failed += 1
                failed_files.append({"path": file_path, "error": str(e)})
        
        # 保存知识库
        if self.persist_directory and processed > 0:
            try:
                self.knowledge_base.save()
            except Exception as e:
                print(f"保存知识库失败: {str(e)}")
                
        return {
            "success": processed > 0,
            "message": f"成功处理 {processed} 个文件，失败 {failed} 个",
            "processed": processed,
            "failed": failed,
            "failed_files": failed_files
        }
    
    def add_directory(
        self,
        directory_path: str,
        extensions: Optional[List[str]] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """
        添加目录中的文件到知识库
        
        参数:
            directory_path: 目录路径
            extensions: 文件扩展名列表
            chunk_size: 文本分块大小
            chunk_overlap: 文本分块重叠大小
            
        返回:
            处理结果字典
        """
        try:
            # 加载目录中的文档
            documents = kb.load_documents_from_dir(directory_path, extensions)
            
            if not documents:
                return {
                    "success": False, 
                    "message": f"在目录 {directory_path} 中未找到文档",
                    "processed": 0,
                    "failed": 0
                }
                
            # 分割文档
            split_docs = kb.split_documents(documents, chunk_size, chunk_overlap)
            
            # 如果还没有初始化知识库，创建一个
            if not self.knowledge_base:
                self.create_knowledge_base()
                
            # 添加到知识库
            self.knowledge_base.add_documents(split_docs)
            
            # 保存知识库
            if self.persist_directory:
                self.knowledge_base.save()
                
            return {
                "success": True,
                "message": f"成功添加 {len(documents)} 个文档",
                "processed": len(documents),
                "failed": 0
            }
        except Exception as e:
            print(f"添加目录失败: {str(e)}")
            return {
                "success": False,
                "message": f"添加目录失败: {str(e)}",
                "processed": 0,
                "failed": 1
            }
    
    def query(self, query: str, top_k: int = 5) -> List[Document]:
        """
        查询知识库
        
        参数:
            query: 查询文本
            top_k: 返回数量
            
        返回:
            相关文档列表
        """
        if not self.knowledge_base:
            return []
            
        try:
            return self.knowledge_base.query(query, top_k)
        except Exception as e:
            print(f"查询失败: {str(e)}")
            return []
    
    def generate_answer(self, query: str, top_k: int = 5) -> str:
        """
        生成回答
        
        参数:
            query: 查询文本
            top_k: 检索的文档数量
            
        返回:
            生成的回答
        """
        if not self.knowledge_base:
            return "知识库未初始化"
            
        if not self.llm:
            return "未配置语言模型，无法生成回答"
            
        try:
            return self.knowledge_base.generate_answer(query, top_k)
        except Exception as e:
            print(f"生成回答失败: {str(e)}")
            return f"生成回答时出错: {str(e)}" 