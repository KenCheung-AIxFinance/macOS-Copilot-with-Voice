#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
知识库功能测试示例
此示例演示了如何创建知识库、添加文档、查询知识库并生成回答
"""

import os
import sys
import tempfile
from pathlib import Path

# 将上一级目录添加到模块搜索路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_deepseek import ChatDeepSeek
from langchain_community.embeddings import HuggingFaceEmbeddings

# 导入知识库模块
from knowledge_base import (
    KnowledgeBaseFactory,
    load_document,
    split_documents,
    load_documents_from_dir
)


def test_basic_functionality():
    """测试基本功能: 创建知识库、添加文档、查询、生成回答"""
    print("=== 测试基本功能 ===")
    
    # 创建临时目录用于存储向量数据库
    temp_dir = tempfile.mkdtemp()
    print(f"向量数据库存储目录: {temp_dir}")
    
    # 创建嵌入模型
    try:
        # 首先尝试使用OpenAI嵌入模型 (如果设置了环境变量)
        embedding_model = OpenAIEmbeddings()
        print("使用OpenAI嵌入模型")
    except Exception:
        # 退回到HuggingFace嵌入模型
        embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        print("使用HuggingFace嵌入模型: sentence-transformers/all-MiniLM-L6-v2")
    
    # 创建LLM (如果设置了环境变量)
    try:
        llm = ChatDeepSeek()
        has_llm = True
        print("使用DeepSeek语言模型")
    except Exception:
        llm = None
        has_llm = False
        print("未配置语言模型，只能进行检索，不能生成回答")
    
    # 创建简单的测试文档
    documents = [
        Document(
            page_content="苹果是一种红色或绿色的水果，口感甜脆，富含维生素C和纤维。",
            metadata={"source": "fruits.txt", "topic": "水果"}
        ),
        Document(
            page_content="香蕉是一种黄色的弯曲水果，富含钾和维生素B6。",
            metadata={"source": "fruits.txt", "topic": "水果"}
        ),
        Document(
            page_content="Python是一种高级编程语言，以简洁易读的语法著称，广泛用于数据分析和人工智能开发。",
            metadata={"source": "programming.txt", "topic": "编程"}
        ),
        Document(
            page_content="JavaScript是网页开发的核心语言，用于构建交互式网站和Web应用。",
            metadata={"source": "programming.txt", "topic": "编程"}
        ),
        Document(
            page_content="PyTorch是一个开源的深度学习框架，由Facebook的人工智能研究团队开发，提供GPU加速的张量计算和动态计算图。",
            metadata={"source": "ai.txt", "topic": "人工智能"}
        )
    ]
    
    print(f"创建了 {len(documents)} 个测试文档")
    
    # 使用工厂创建Chroma知识库
    print("\n创建Chroma知识库...")
    kb = KnowledgeBaseFactory.create_knowledge_base(
        embedding_model=embedding_model,
        store_type="chroma",
        documents=documents,
        persist_directory=os.path.join(temp_dir, "chroma_db"),
        llm=llm,
        collection_name="test_collection"
    )
    
    # 执行查询
    print("\n测试查询: '什么水果富含维生素？'")
    results = kb.query("什么水果富含维生素？")
    print(f"找到 {len(results)} 个相关文档:")
    for i, doc in enumerate(results):
        print(f"\n文档 {i+1}:")
        print(f"内容: {doc.page_content}")
        print(f"元数据: {doc.metadata}")
        
    # 如果有语言模型，测试生成回答
    if has_llm:
        print("\n测试生成回答: '什么水果富含维生素？'")
        answer = kb.generate_answer("什么水果富含维生素？")
        print(f"回答: {answer}")
        
        print("\n测试生成回答: '哪种编程语言适合机器学习？'")
        answer = kb.generate_answer("哪种编程语言适合机器学习？")
        print(f"回答: {answer}")
    
    # 保存知识库
    print("\n保存知识库...")
    kb.save()
    print("知识库保存成功!")
    
    # 加载知识库
    print("\n加载知识库...")
    loaded_kb = KnowledgeBaseFactory.load_knowledge_base(
        embedding_model=embedding_model,
        store_type="chroma",
        persist_directory=os.path.join(temp_dir, "chroma_db"),
        llm=llm
    )
    
    # 测试加载后的知识库
    print("\n测试加载后的知识库查询: '编程语言的特点是什么？'")
    results = loaded_kb.query("编程语言的特点是什么？")
    print(f"找到 {len(results)} 个相关文档:")
    for i, doc in enumerate(results):
        print(f"\n文档 {i+1}:")
        print(f"内容: {doc.page_content}")
        print(f"元数据: {doc.metadata}")
    
    print("\n=== 基本功能测试完成 ===")


def create_test_files():
    """创建测试文件"""
    temp_dir = tempfile.mkdtemp()
    
    # 创建测试文件
    test_files = {
        "python_intro.txt": """
Python是一种广泛使用的解释型、高级编程语言，由Guido van Rossum于1991年创建。
Python的设计强调代码的可读性，使用缩进而非括号来组织代码块。
它支持多种编程范式，包括面向对象、命令式、函数式和过程式编程。
Python通常被作为脚本语言使用，但也完全能够构建复杂的大型应用。
Python拥有丰富的标准库和第三方库，使得开发变得高效。
""",
        "machine_learning.txt": """
机器学习是人工智能的一个分支，专注于开发能够从数据中学习的算法和模型。
机器学习算法通过识别数据中的模式来构建数学模型，从而做出预测或决策。
常见的机器学习类型包括监督学习、无监督学习和强化学习。
监督学习使用带标签的数据集来训练模型，而无监督学习则寻找未标记数据中的隐藏结构。
深度学习是机器学习的一个子领域，它使用多层神经网络处理复杂问题。
"""
    }
    
    # 写入文件
    for filename, content in test_files.items():
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    return temp_dir


def test_file_loading():
    """测试文件加载功能"""
    print("\n=== 测试文件加载功能 ===")
    
    # 创建测试文件
    files_dir = create_test_files()
    print(f"创建测试文件目录: {files_dir}")
    
    # 列出测试文件
    test_files = os.listdir(files_dir)
    print(f"测试文件: {test_files}")
    
    # 加载文档
    print("\n加载文档...")
    documents = load_documents_from_dir(files_dir, extensions=[".txt"])
    print(f"加载了 {len(documents)} 个文档")
    
    # 分割文档
    print("\n分割文档...")
    split_docs = split_documents(documents, chunk_size=100, chunk_overlap=20)
    print(f"分割后得到 {len(split_docs)} 个文档块")
    
    # 显示分割后的文档
    print("\n分割后的文档预览:")
    for i, doc in enumerate(split_docs[:3]):
        print(f"\n文档块 {i+1}:")
        print(f"内容: {doc.page_content}")
        print(f"元数据: {doc.metadata}")
    
    if len(split_docs) > 3:
        print(f"\n... 还有 {len(split_docs) - 3} 个文档块 ...")
    
    print("\n=== 文件加载测试完成 ===")


if __name__ == "__main__":
    # 执行测试
    test_basic_functionality()
    test_file_loading()
    
    print("\n所有测试完成!") 