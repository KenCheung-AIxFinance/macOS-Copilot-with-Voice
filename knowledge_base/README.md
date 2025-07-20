# macOS_Copilot 知识库底层库

这是一个基于LangChain的RAG（检索增强生成）知识库实现，为macOS_Copilot提供智能知识库功能。

## 功能特点

- **灵活的向量存储支持**：支持Chroma和FAISS两种向量数据库
- **多种嵌入模型**：支持HuggingFace和OpenAI的嵌入模型
- **文档加载**：支持多种文档格式，包括TXT、PDF、Markdown等
- **智能文档分割**：提供多种文本分割策略，优化检索效果
- **RAG问答**：结合检索和生成模型，基于知识库内容回答问题
- **易于扩展**：模块化设计，便于添加新的向量存储或嵌入模型

## 安装要求

- Python 3.8+
- 依赖库:
  - langchain 和相关组件(langchain-core, langchain-community等)
  - chromadb (用于Chroma向量存储)
  - faiss-cpu 或 faiss-gpu (用于FAISS向量存储)
  - sentence-transformers (用于本地嵌入模型)
  - openai (可选，用于OpenAI嵌入模型和语言模型)
  - 文档处理相关库: pypdf, docx2txt, unstructured等

## 快速开始

### 基本用法

```python
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from knowledge_base import KnowledgeBaseFactory

# 创建嵌入模型
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# 创建测试文档
documents = [
    Document(
        page_content="苹果是一种红色或绿色的水果，口感甜脆，富含维生素C和纤维。",
        metadata={"source": "fruits.txt"}
    ),
    Document(
        page_content="香蕉是一种黄色的弯曲水果，富含钾和维生素B6。",
        metadata={"source": "fruits.txt"}
    )
]

# 创建知识库
kb = KnowledgeBaseFactory.create_knowledge_base(
    embedding_model=embedding_model,
    store_type="chroma",  # 或 "faiss"
    documents=documents,
    persist_directory="./knowledge_data"
)

# 查询知识库
results = kb.query("什么水果富含维生素？")
for doc in results:
    print(doc.page_content)
```

### 从目录加载文档

```python
from knowledge_base import KnowledgeBaseFactory, load_documents_from_dir, split_documents
from langchain_community.embeddings import HuggingFaceEmbeddings

# 加载文档
documents = load_documents_from_dir("./my_documents", extensions=[".txt", ".pdf", ".md"])

# 分割文档
split_docs = split_documents(documents, chunk_size=1000, chunk_overlap=200)

# 创建嵌入模型
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# 创建知识库
kb = KnowledgeBaseFactory.create_knowledge_base(
    embedding_model=embedding_model,
    store_type="chroma",
    documents=split_docs,
    persist_directory="./knowledge_data"
)

# 保存知识库
kb.save()
```

### 生成回答

```python
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from knowledge_base import KnowledgeBaseFactory

# 创建嵌入模型
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# 创建语言模型
llm = ChatOpenAI(temperature=0.2)

# 加载知识库
kb = KnowledgeBaseFactory.load_knowledge_base(
    embedding_model=embedding_model,
    store_type="chroma",
    persist_directory="./knowledge_data",
    llm=llm
)

# 生成回答
answer = kb.generate_answer("什么水果富含维生素？")
print(answer)
```

## 与macOS_Copilot集成

知识库底层库已与macOS_Copilot集成，通过`macOS_Copilot.models.knowledge_base`模块进行调用。示例：

```python
from macOS_Copilot.models.knowledge_base import KnowledgeBaseModel

# 初始化知识库模型
kb_model = KnowledgeBaseModel(
    embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
    store_type="chroma",
    persist_directory="~/.macOS_Copilot/knowledge_base"
)

# 添加文件
kb_model.add_files(["document1.txt", "document2.pdf"])

# 查询
results = kb_model.query("我的问题")

# 生成回答
answer = kb_model.generate_answer("我的问题")
```

## 示例

查看`examples`目录中的示例脚本，了解更多使用方法：

- `simple_test.py` - 基本功能测试
- `copilot_integration.py` - 与macOS_Copilot集成示例
- `advanced_features.py` - 高级特性示例

## 支持的向量存储

- **Chroma**：适合大多数场景，支持元数据过滤，性能良好
- **FAISS**：Facebook AI研究所开发的高性能向量搜索库，适合大规模向量检索

## 支持的嵌入模型

- **HuggingFace模型**：本地运行，无需API密钥
  - all-MiniLM-L6-v2（默认）
  - paraphrase-multilingual-MiniLM-L12-v2（多语言支持）
  - 以及其他HuggingFace支持的嵌入模型
- **OpenAI模型**：需要API密钥
  - text-embedding-ada-002
  - text-embedding-3-small
  - text-embedding-3-large

## 支持的语言模型（用于生成回答）

- **OpenAI模型**：需要API密钥
  - gpt-3.5-turbo
  - gpt-4-turbo
  - 其他OpenAI兼容模型
- **其他LangChain支持的模型**：可以在代码中集成

## 文件格式支持

- 文本文件 (.txt)
- PDF文件 (.pdf)
- Markdown文件 (.md)
- Word文档 (.docx)
- Excel文件 (.xlsx, .xls)
- CSV文件 (.csv)
- JSON文件 (.json)

## 可能的扩展方向

- 添加更多向量存储支持（如Pinecone、Weaviate等）
- 实现本地语言模型集成（如LLaMa、ChatGLM等）
- 添加网页和API文档爬取功能
- 实现主动学习和知识库自动更新 