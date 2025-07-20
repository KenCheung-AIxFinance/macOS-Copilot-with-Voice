# knowledge_base 工具函数文件

from typing import List, Optional, Union, Dict, Any
import os
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    CSVLoader,
    JSONLoader,
)

def example_util_func():
    """示例工具函数。"""
    pass

def get_document_loader(file_path: str):
    """
    根据文件类型获取适当的文档加载器
    
    参数:
        file_path: 文件路径
        
    返回:
        文档加载器实例
    """
    file_extension = Path(file_path).suffix.lower()
    
    if file_extension == ".pdf":
        return PyPDFLoader(file_path)
    elif file_extension == ".md":
        return TextLoader(file_path)
    elif file_extension == ".txt":
        return TextLoader(file_path)
    elif file_extension == ".docx":
        return Docx2txtLoader(file_path)
    elif file_extension == ".xlsx" or file_extension == ".xls":
        return UnstructuredExcelLoader(file_path)
    elif file_extension == ".csv":
        return CSVLoader(file_path)
    elif file_extension == ".json":
        return JSONLoader(
            file_path=file_path,
            jq_schema=".",
            text_content=False,
        )
    else:
        # 对于未知文件类型，尝试使用文本加载器
        return TextLoader(file_path)

def load_document(file_path: str) -> List[Document]:
    """
    加载指定路径的文档
    
    参数:
        file_path: 文件路径
        
    返回:
        Document对象列表
    """
    loader = get_document_loader(file_path)
    return loader.load()

def load_documents_from_dir(directory_path: str, extensions: Optional[List[str]] = None) -> List[Document]:
    """
    从目录加载文档
    
    参数:
        directory_path: 目录路径
        extensions: 文件扩展名列表，如 [".pdf", ".txt"]
        
    返回:
        Document对象列表
    """
    documents = []
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file)[1].lower()
            
            if extensions and file_extension not in extensions:
                continue
                
            try:
                docs = load_document(file_path)
                documents.extend(docs)
            except Exception as e:
                print(f"加载文件 {file_path} 时出错: {str(e)}")
                
    return documents

def split_documents(documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
    """
    将文档分割成更小的块
    
    参数:
        documents: 文档列表
        chunk_size: 块大小
        chunk_overlap: 块重叠大小
        
    返回:
        分割后的Document对象列表
    """
    # 创建文本分割器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    
    # 分割文档
    return text_splitter.split_documents(documents)

def split_markdown_documents(documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
    """
    将Markdown文档分割成更小的块
    
    参数:
        documents: Markdown文档列表
        chunk_size: 块大小
        chunk_overlap: 块重叠大小
        
    返回:
        分割后的Document对象列表
    """
    # 创建Markdown文本分割器
    md_splitter = MarkdownTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    
    # 分割文档
    return md_splitter.split_documents(documents) 