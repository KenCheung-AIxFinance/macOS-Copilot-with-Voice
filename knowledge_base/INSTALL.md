# macOS_Copilot知识库安装指南

本文档提供了macOS_Copilot知识库底层库的安装和使用说明。

## 安装要求

- Python 3.8或更高版本
- pip包管理器
- 对于macOS：可能需要安装Homebrew和XCode命令行工具

## 安装步骤

### 1. 克隆仓库（如果尚未克隆）

```bash
git clone https://github.com/yourusername/macOS_Copilot.git
cd macOS_Copilot
```

### 2. 使用pip安装

#### 方法一：从本地安装

```bash
# 创建并激活虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # 在Windows上使用：.venv\Scripts\activate

# 安装知识库底层库及其依赖
cd knowledge_base
pip install -e .
```

#### 方法二：安装必要的依赖

如果你不想安装整个包，可以只安装必要的依赖：

```bash
pip install langchain langchain-core langchain-community langchain-chroma langchain-text-splitters
pip install chromadb faiss-cpu sentence-transformers torch numpy
pip install pypdf docx2txt pandas
```

### 3. 安装可选依赖

根据需要安装以下可选依赖：

```bash
# 用于OpenAI集成
pip install openai

# 用于高级文档处理
pip install unstructured python-magic opencv-python
```

## 测试安装

安装完成后，可以运行示例脚本测试功能：

```bash
# 运行基本功能测试
python knowledge_base/examples/simple_test.py

# 运行macOS_Copilot集成测试
python knowledge_base/examples/copilot_integration.py

# 运行高级特性测试
python knowledge_base/examples/advanced_features.py
```

## 常见问题

### 安装unstructured时遇到问题

在某些环境中，安装unstructured包可能会遇到问题。如果不需要高级文档处理功能，可以跳过安装这个包。如果确实需要，尝试以下步骤：

```bash
# 在macOS上安装依赖
brew install libmagic poppler tesseract

# 然后安装unstructured
pip install "unstructured[all]"
```

### FAISS安装问题

如果在安装或使用FAISS时遇到问题，可以尝试：

```bash
# 卸载现有的FAISS
pip uninstall -y faiss-cpu

# 重新安装
pip install faiss-cpu
```

对于GPU支持，可以安装`faiss-gpu`代替`faiss-cpu`。

## 进一步配置

知识库默认使用本地嵌入模型，但也支持OpenAI API。要使用OpenAI的服务，需要设置环境变量：

```bash
# 在macOS/Linux上
export OPENAI_API_KEY=your-api-key-here

# 在Windows上
set OPENAI_API_KEY=your-api-key-here
```

可以将此行添加到shell配置文件（如`.bashrc`、`.zshrc`等）中，使其在每次启动终端时自动设置。 