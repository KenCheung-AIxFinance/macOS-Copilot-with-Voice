#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
知识库高级特性示例
此示例演示了知识库的高级使用方法，包括：
1. 使用自定义嵌入模型
2. 使用FAISS向量存储
3. 自定义文档分割
4. 多知识库集成
"""

import os
import sys
import tempfile
from pathlib import Path

# 将上一级目录添加到模块搜索路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownTextSplitter, CharacterTextSplitter

# 导入知识库模块
from knowledge_base import (
    KnowledgeBaseFactory,
    ChromaKnowledgeBase,
    FAISSKnowledgeBase,
    load_document,
    split_documents,
    load_documents_from_dir
)


def create_custom_embedding_model():
    """创建自定义嵌入模型"""
    print("=== 创建自定义嵌入模型 ===")
    
    # 使用HuggingFace的多语言嵌入模型
    try:
        embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        print("使用多语言嵌入模型: paraphrase-multilingual-MiniLM-L12-v2")
    except Exception as e:
        print(f"加载模型失败: {e}")
        # 退回到标准模型
        embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        print("退回到标准嵌入模型: all-MiniLM-L6-v2")
    
    return embedding_model


def test_with_faiss():
    """测试使用FAISS向量存储"""
    print("\n=== 测试FAISS向量存储 ===")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"向量存储目录: {temp_dir}")
    
    # 创建自定义嵌入模型
    embedding_model = create_custom_embedding_model()
    
    # 创建测试文档
    documents = [
        Document(
            page_content="区块链是一种分布式账本技术，能够安全透明地记录交易和资产跟踪。",
            metadata={"source": "blockchain.txt", "topic": "技术", "language": "Chinese"}
        ),
        Document(
            page_content="人工智能是计算机科学的一个分支，致力于创建能够模拟人类智能的系统。",
            metadata={"source": "ai.txt", "topic": "技术", "language": "Chinese"}
        ),
        Document(
            page_content="量子计算利用量子力学原理进行信息处理，有望解决传统计算机难以处理的问题。",
            metadata={"source": "quantum.txt", "topic": "技术", "language": "Chinese"}
        ),
        Document(
            page_content="Blockchain is a distributed ledger technology that can securely and transparently record transactions and track assets.",
            metadata={"source": "blockchain_en.txt", "topic": "Technology", "language": "English"}
        ),
        Document(
            page_content="Artificial Intelligence is a branch of computer science dedicated to creating systems capable of simulating human intelligence.",
            metadata={"source": "ai_en.txt", "topic": "Technology", "language": "English"}
        )
    ]
    
    print(f"创建了 {len(documents)} 个测试文档")
    
    # 使用FAISS创建知识库
    kb = FAISSKnowledgeBase.from_documents(
        documents=documents,
        embedding_model=embedding_model,
        persist_directory=os.path.join(temp_dir, "faiss_index")
    )
    
    print("\n知识库创建成功，测试查询...")
    
    # 测试中文查询
    query_zh = "什么是区块链技术？"
    print(f"\n中文查询: '{query_zh}'")
    results = kb.query(query_zh)
    print(f"找到 {len(results)} 个相关文档:")
    for i, doc in enumerate(results):
        print(f"文档 {i+1} ({doc.metadata.get('language', 'Unknown')}):")
        print(f"内容: {doc.page_content}")
    
    # 测试英文查询
    query_en = "What is artificial intelligence?"
    print(f"\n英文查询: '{query_en}'")
    results = kb.query(query_en)
    print(f"找到 {len(results)} 个相关文档:")
    for i, doc in enumerate(results):
        print(f"文档 {i+1} ({doc.metadata.get('language', 'Unknown')}):")
        print(f"内容: {doc.page_content}")
    
    # 保存知识库
    print("\n保存知识库...")
    kb.save()
    
    # 加载知识库
    print("\n加载知识库...")
    loaded_kb = FAISSKnowledgeBase.load(
        embedding_model=embedding_model,
        persist_directory=os.path.join(temp_dir, "faiss_index"),
        allow_dangerous_deserialization=True  # 添加这个参数以允许反序列化
    )
    
    # 测试加载后的知识库
    print("\n测试加载后的知识库...")
    results = loaded_kb.query("量子计算的优势是什么？")
    print(f"找到 {len(results)} 个相关文档:")
    for i, doc in enumerate(results):
        print(f"文档 {i+1}:")
        print(f"内容: {doc.page_content}")
    
    print("\n=== FAISS向量存储测试完成 ===")
    
    return temp_dir


def test_custom_document_splitting():
    """测试自定义文档分割"""
    print("\n=== 测试自定义文档分割 ===")
    
    # 创建测试文件
    temp_dir = tempfile.mkdtemp()
    test_markdown = os.path.join(temp_dir, "test.md")
    
    with open(test_markdown, "w", encoding="utf-8") as f:
        f.write("""# 机器学习简介

## 监督学习

监督学习是一种机器学习任务，它使用标记数据来学习输入到输出的映射。

### 分类算法

分类算法用于预测离散类别标签。常见的分类算法包括：
- 决策树
- 随机森林
- 支持向量机
- 神经网络

### 回归算法

回归算法用于预测连续值。常见的回归算法包括：
- 线性回归
- 多项式回归
- 决策树回归

## 无监督学习

无监督学习处理未标记的数据，尝试发现其中的模式和结构。

### 聚类算法

聚类算法将相似的数据点分组。常见的聚类算法包括：
- K均值聚类
- 层次聚类
- DBSCAN

### 降维算法

降维算法减少数据的复杂性，同时保留重要特性。常见的降维算法包括：
- 主成分分析 (PCA)
- t-SNE
- 自编码器
""")
    
    print(f"创建了Markdown测试文件: {test_markdown}")
    
    # 加载文档
    docs = load_document(test_markdown)
    print(f"加载了 {len(docs)} 个文档")
    
    # 创建Markdown分割器
    md_splitter = MarkdownTextSplitter(
        chunk_size=150,
        chunk_overlap=30
    )
    
    # 分割文档
    md_docs = md_splitter.split_documents(docs)
    print(f"Markdown分割得到 {len(md_docs)} 个文档块")
    
    # 显示分割结果
    print("\nMarkdown分割结果预览:")
    for i, doc in enumerate(md_docs[:3]):  # 只显示前3个文档块
        print(f"\n文档块 {i+1}:")
        print(f"内容: {doc.page_content[:100]}...")
        if "headers" in doc.metadata:
            print(f"标题: {doc.metadata['headers']}")
    
    # 使用普通文本分割器
    char_splitter = CharacterTextSplitter(
        chunk_size=150,
        chunk_overlap=30,
        separator="\n"
    )
    
    # 分割文档
    char_docs = char_splitter.split_documents(docs)
    print(f"\n普通文本分割得到 {len(char_docs)} 个文档块")
    
    # 显示分割结果
    print("\n普通分割结果预览:")
    for i, doc in enumerate(char_docs[:3]):  # 只显示前3个文档块
        print(f"\n文档块 {i+1}:")
        print(f"内容: {doc.page_content[:100]}...")
    
    if len(char_docs) > 3:
        print(f"\n... 还有 {len(char_docs) - 3} 个文档块 ...")
    
    print("\n=== 自定义文档分割测试完成 ===")
    
    return md_docs


def test_multi_knowledge_base():
    """测试多知识库集成"""
    print("\n=== 测试多知识库集成 ===")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"存储目录: {temp_dir}")
    
    # 创建嵌入模型
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # 尝试创建语言模型
    try:
        llm = ChatOpenAI(temperature=0)
        has_llm = True
    except Exception:
        llm = None
        has_llm = False
        print("未配置语言模型，将只进行检索测试")
    
    # 创建技术文档
    tech_docs = [
        Document(
            page_content="Python是一种解释型高级编程语言，以简洁的语法和强大的库而闻名。",
            metadata={"source": "python.txt", "category": "技术"}
        ),
        Document(
            page_content="JavaScript是一种脚本编程语言，主要用于Web开发，可以为网页添加交互功能。",
            metadata={"source": "javascript.txt", "category": "技术"}
        )
    ]
    
    # 创建历史文档
    history_docs = [
        Document(
            page_content="第一次世界大战从1914年持续到1918年，是一场全球性冲突。",
            metadata={"source": "ww1.txt", "category": "历史"}
        ),
        Document(
            page_content="文艺复兴是14世纪至17世纪在欧洲开始的文化运动，标志着中世纪向现代过渡。",
            metadata={"source": "renaissance.txt", "category": "历史"}
        )
    ]
    
    # 创建两个知识库，使用英文集合名
    tech_kb = ChromaKnowledgeBase.from_documents(
        documents=tech_docs,
        embedding_model=embedding_model,
        collection_name="tech_knowledge",  # 使用英文集合名
        persist_directory=os.path.join(temp_dir, "tech_kb"),
        llm=llm
    )
    
    history_kb = ChromaKnowledgeBase.from_documents(
        documents=history_docs,
        embedding_model=embedding_model,
        collection_name="history_knowledge",  # 使用英文集合名
        persist_directory=os.path.join(temp_dir, "history_kb"),
        llm=llm
    )
    
    print("创建了两个知识库：技术知识库和历史知识库")
    
    # 测试查询每个知识库
    query = "编程语言有哪些？"
    print(f"\n查询技术知识库: '{query}'")
    tech_results = tech_kb.query(query)
    print(f"找到 {len(tech_results)} 个相关文档:")
    for i, doc in enumerate(tech_results):
        print(f"文档 {i+1}:")
        print(f"内容: {doc.page_content}")
    
    query = "什么是文艺复兴？"
    print(f"\n查询历史知识库: '{query}'")
    history_results = history_kb.query(query)
    print(f"找到 {len(history_results)} 个相关文档:")
    for i, doc in enumerate(history_results):
        print(f"文档 {i+1}:")
        print(f"内容: {doc.page_content}")
    
    # 如果有语言模型，测试回答生成
    if has_llm:
        print("\n测试生成回答:")
        query = "比较Python和JavaScript的主要用途"
        print(f"查询: '{query}'")
        answer = tech_kb.generate_answer(query)
        print(f"技术知识库回答: {answer}")
        
        query = "文艺复兴的历史意义是什么？"
        print(f"查询: '{query}'")
        answer = history_kb.generate_answer(query)
        print(f"历史知识库回答: {answer}")
    
    print("\n=== 多知识库集成测试完成 ===")


if __name__ == "__main__":
    # 测试FAISS向量存储
    faiss_dir = test_with_faiss()
    
    # 测试自定义文档分割
    md_docs = test_custom_document_splitting()
    
    # 测试多知识库集成
    test_multi_knowledge_base()
    
    print("\n所有高级特性测试完成!") 