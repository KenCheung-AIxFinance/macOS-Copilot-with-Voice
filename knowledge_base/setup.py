from setuptools import setup, find_packages

setup(
    name="macOS_Copilot_KnowledgeBase",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langchain-core",
        "langchain-community",
        "langchain-chroma",
        "langchain-text-splitters",
        "chromadb",
        "faiss-cpu",  # 或 faiss-gpu 用于GPU支持
        "sentence-transformers",
        "torch",
        "numpy",
        "pypdf",
        "docx2txt",
        "python-magic",
        "opencv-python",  # 用于解析PDF中的图像
        "pandas",  # 用于处理CSV文件
        "unstructured",  # 可选，用于更高级的文档处理
        "openai",  # 可选，用于OpenAI模型集成
    ],
    author="macOS Copilot Team",
    author_email="example@example.com",
    description="基于LangChain的RAG知识库底层库",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/macOS_Copilot_KnowledgeBase",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 