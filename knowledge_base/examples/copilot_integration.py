#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
macOS_Copilot 知识库集成示例
此示例演示了如何将知识库与macOS_Copilot应用集成
"""

import os
import sys
from pathlib import Path

# 将上一级目录添加到模块搜索路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from macOS_Copilot.models.knowledge_base import KnowledgeBaseModel
from knowledge_base import load_document, split_documents


def setup_knowledge_base():
    """设置知识库并创建测试数据"""
    print("=== 设置macOS_Copilot知识库 ===")
    
    # 设置知识库目录
    kb_dir = os.path.join(os.path.expanduser("~"), ".macOS_Copilot_test", "knowledge_base")
    os.makedirs(kb_dir, exist_ok=True)
    print(f"知识库存储目录: {kb_dir}")
    
    # 初始化知识库模型
    kb_model = KnowledgeBaseModel(
        embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
        store_type="chroma",
        persist_directory=kb_dir
    )
    
    # 创建知识库（如果不存在）
    if not kb_model.knowledge_base:
        print("创建新知识库...")
        success = kb_model.create_knowledge_base()
        if success:
            print("知识库创建成功!")
        else:
            print("知识库创建失败!")
            return None
    else:
        print("使用现有知识库")
    
    return kb_model


def add_test_data(kb_model):
    """添加测试数据到知识库"""
    print("\n=== 添加测试数据 ===")
    
    # 创建测试文件目录
    temp_dir = os.path.join(os.path.expanduser("~"), ".macOS_Copilot_test", "temp_docs")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建测试文件
    test_files = {
        "apple_products.txt": """
苹果公司（Apple Inc.）是一家美国跨国科技公司，总部位于加利福尼亚州库比蒂诺。
苹果公司设计、开发和销售消费电子产品、计算机软件和在线服务。

主要产品包括：
1. iPhone - 智能手机产品线，运行iOS系统
2. iPad - 平板电脑产品线，运行iPadOS系统
3. Mac - 个人电脑产品线，运行macOS系统
4. Apple Watch - 智能手表产品线，运行watchOS系统
5. Apple TV - 数字媒体播放器，运行tvOS系统
6. AirPods - 无线耳机产品线

苹果公司的软件产品包括macOS、iOS、iPadOS、watchOS和tvOS操作系统，
以及iTunes、Safari网络浏览器、iLife和iWork创意与生产力套件等。
""",
        "macos_features.txt": """
macOS是苹果公司开发的桌面操作系统，专为Mac电脑设计。

macOS的主要特点：
1. 用户友好的图形界面，包括Dock、Finder和Spotlight等
2. 与其他苹果设备的无缝集成，如iPhone、iPad和Apple Watch
3. 强大的安全性能和隐私保护
4. 内置的应用程序如Safari、Mail、Photos和iMovie等
5. 支持虚拟助手Siri
6. 时间机器(Time Machine)自动备份功能

macOS的最新版本名为macOS Ventura（版本13），提供了更多功能如舞台管理器(Stage Manager)、
连续互通摄像头(Continuity Camera)和系统设置重新设计等。
""",
        "copilot_info.txt": """
macOS Copilot是一个智能助手应用，专为Mac用户设计，旨在提高工作效率和简化日常任务。

主要功能：
1. 智能命令执行 - 通过自然语言处理理解用户指令并执行相应操作
2. 知识库集成 - 允许用户构建和查询个人知识库
3. 文件管理助手 - 帮助组织和查找文件
4. 代码编写辅助 - 为开发者提供编码建议和辅助
5. 自动化工作流程 - 创建和执行自定义的自动化任务

macOS Copilot利用先进的人工智能技术，包括大型语言模型和机器学习算法，
为用户提供上下文相关的帮助和建议，从而提高工作效率和用户体验。
"""
    }
    
    # 写入测试文件
    file_paths = []
    for filename, content in test_files.items():
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        file_paths.append(file_path)
    
    print(f"创建了 {len(file_paths)} 个测试文件")
    
    # 添加文件到知识库
    result = kb_model.add_files(file_paths)
    print(f"添加文件结果: {result['message']}")
    
    return True


def test_search_and_query(kb_model):
    """测试搜索和问答功能"""
    print("\n=== 测试搜索和问答 ===")
    
    # 测试查询
    queries = [
        "苹果公司有哪些产品？",
        "macOS的主要特点是什么？",
        "什么是macOS Copilot？",
        "macOS和iOS有什么关系？"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        
        # 执行查询
        results = kb_model.query(query)
        print(f"找到 {len(results)} 个相关文档:")
        for i, doc in enumerate(results[:2]):  # 只显示前2个结果
            print(f"文档 {i+1}: {doc.page_content[:100]}...")
        
        # 生成回答
        if hasattr(kb_model, "llm") and kb_model.llm:
            print("\n生成回答:")
            answer = kb_model.generate_answer(query)
            print(f"回答: {answer}")
        
    print("\n=== 搜索和问答测试完成 ===")


def clean_test_data():
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")
    
    test_dir = os.path.join(os.path.expanduser("~"), ".macOS_Copilot_test")
    
    # 询问是否要删除测试数据
    response = input(f"是否删除测试目录 {test_dir}？(y/n): ")
    if response.lower() == 'y':
        import shutil
        try:
            shutil.rmtree(test_dir)
            print(f"已删除测试目录: {test_dir}")
        except Exception as e:
            print(f"删除目录失败: {e}")
    else:
        print(f"保留测试目录: {test_dir}")


if __name__ == "__main__":
    # 设置知识库
    kb_model = setup_knowledge_base()
    if kb_model:
        # 添加测试数据
        if add_test_data(kb_model):
            # 测试搜索和问答
            test_search_and_query(kb_model)
        
        # 清理测试数据
        clean_test_data()
    
    print("\n集成测试完成!") 