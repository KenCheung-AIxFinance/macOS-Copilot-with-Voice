# 🚀 macOS Copilot - 您的智能系统助手

<div align="center">

![macOS Copilot](https://img.shields.io/badge/macOS-Copilot-007AFF?style=for-the-badge&logo=apple&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Enabled-green?style=for-the-badge&logo=langchain&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**🎯 让您的macOS更智能，让操作更简单**

[✨ 功能特性](#-功能特性) • [🚀 快速开始](#-快速开始) • [💡 使用示例](#-使用示例) • [🔧 技术架构](#-技术架构)

</div>

---

## 🌟 产品亮点

> **macOS Copilot** 是专为macOS用户打造的智能系统助手，集成了语音交互、系统管理、应用控制等强大功能。就像Windows Copilot一样，让您的macOS操作更加智能和便捷！

### 🎯 核心价值
- **🤖 AI驱动** - 基于大语言模型的智能对话
- **🎤 语音交互** - 支持中文语音输入和AI语音回复
- **⚡ 系统集成** - 深度集成macOS系统功能
- **🎨 现代UI** - 美观的图形界面，操作直观
- **🔒 安全可靠** - 本地化处理，保护隐私

---

## ✨ 功能特性

### 🎤 智能语音交互
- **中文语音识别** - 支持自然语言输入
- **AI语音合成** - 使用Edge TTS进行语音回复
- **实时对话** - 语音与文字混合交互模式
- **智能降噪** - 自动环境噪音适应

### 🔧 系统管理工具
- **📊 系统监控** - 实时CPU、内存、磁盘使用率
- **🔋 电池管理** - 电池状态和剩余时间监控
- **🌐 网络诊断** - 网络接口和连接状态查看
- **🔊 音量控制** - 系统音量智能调节
- **⏰ 时间服务** - 精确时间获取和显示

### 📱 应用程序管理
- **🚀 智能启动** - 模糊匹配应用名称，一键启动
- **📋 应用列表** - 查看所有已安装应用程序
- **🔍 快速搜索** - 智能应用搜索和推荐
- **⚙️ 系统应用** - 深度集成系统内置应用

### 📁 文件操作助手
- **🔍 智能搜索** - 全盘文件快速搜索
- **📝 笔记创建** - 一键创建文本笔记
- **📂 文件管理** - 基础文件操作功能
- **🗂️ 目录浏览** - 智能目录结构分析

### 💻 终端集成
- **🛡️ 安全执行** - 受控的终端命令执行
- **🔧 系统控制** - 通过命令行控制macOS
- **🤖 自动化** - 支持批量操作和脚本执行
- **📊 进程管理** - 实时进程监控和管理

---

## 🚀 快速开始

### 📋 系统要求
- ✅ macOS 10.15 (Catalina) 或更高版本
- ✅ Python 3.8+ 
- ✅ 麦克风权限
- ✅ 网络连接（AI API调用）

### ⚡ 一键安装

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/macOS-Copilot.git
cd macOS-Copilot

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API密钥
export OPENAI_API_KEY="your-api-key-here"

# 4. 启动应用
python macos_assistant_ui.py
```

### 🎯 两种使用模式

**图形界面模式（推荐）**
```bash
python macos_assistant_ui.py
```

**命令行模式**
```bash
python agent.py
```

---

## 💡 使用示例

### 🎤 语音交互示例
```
👤 用户: "帮我查看系统信息"
🤖 助手: [语音回复] "您的系统信息如下：macOS 14.0，16GB内存，CPU使用率45%..."

👤 用户: "打开Safari浏览器"
🤖 助手: [语音回复] "已为您打开Safari浏览器"
```

### 🔧 系统管理示例
```
👤 用户: 查看系统信息
🤖 助手: 
系统信息:
ProductName:    macOS
ProductVersion: 14.0
BuildVersion:   23A344
CPU: Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz
内存: 16GB 总内存, 45.2% 使用率
磁盘: 512GB 总空间, 67.8% 使用率
```

### 📱 应用管理示例
```
👤 用户: 打开Safari
🤖 助手: 已打开 Safari

👤 用户: 查看已安装的应用程序
🤖 助手: 已安装的应用程序:
Safari.app, Google Chrome.app, Terminal.app, Calculator.app...
```

### 📁 文件操作示例
```
👤 用户: 搜索文件 test.txt
🤖 助手: 找到以下文件:
/Users/username/Documents/test.txt
/Users/username/Desktop/test.txt

👤 用户: 创建笔记 今天的工作计划
🤖 助手: 笔记已创建: /Users/username/Desktop/note_20241201_143022.txt
```

---

## 🎨 界面预览

<div align="center">

![主界面](https://via.placeholder.com/800x500/007AFF/FFFFFF?text=macOS+Copilot+主界面)
*现代化的图形用户界面，支持语音交互和系统管理*

</div>

---

## 🔧 技术架构

### 🏗️ 核心组件
- **🤖 LangChain** - AI代理框架，提供强大的推理能力
- **🧠 DeepSeek API** - 大语言模型服务，支持中文对话
- **🎨 PyQt6** - 现代化图形用户界面框架
- **🎤 SpeechRecognition** - 高精度语音识别引擎
- **🔊 Edge TTS** - 微软Edge TTS语音合成服务
- **📊 psutil** - 系统监控和进程管理

### 🔧 工具集成
- **🛠️ MacOSTools** - macOS系统工具集合
- **⚡ AgentExecutor** - LangChain代理执行器
- **💬 ChatOpenAI** - OpenAI兼容的聊天模型

### 🎯 架构特点
- **🔄 响应式设计** - 实时响应用户输入
- **🎤 语音优先** - 语音交互为核心功能
- **🔒 安全可靠** - 本地化处理，保护用户隐私
- **⚡ 高性能** - 优化的多线程架构

---

## 🎯 预设命令

图形界面提供丰富的预设命令，一键执行常用操作：

| 功能类别 | 预设命令 |
|---------|---------|
| 🔧 系统管理 | 查看系统信息、查看电池状态、查看网络信息 |
| 📱 应用控制 | 打开Safari、打开终端、打开计算器 |
| 📊 系统监控 | 查看运行进程、查看内存使用 |
| 📁 文件操作 | 搜索文件、创建笔记 |
| 🔊 系统控制 | 设置音量为50%、获取当前时间 |

---

## 🛡️ 安全与隐私

### 🔒 安全特性
- **🛡️ 权限管理** - 精确控制应用权限
- **🔐 本地处理** - 敏感数据本地化处理
- **⚡ 安全执行** - 受控的命令执行环境
- **🔍 透明操作** - 所有操作可追溯

### ⚠️ 安全提醒
1. **权限管理** - 首次运行需要授予麦克风权限
2. **命令执行** - 终端命令执行需要用户确认
3. **文件访问** - 文件操作仅访问用户目录
4. **系统控制** - 系统操作需要用户授权

---

## 🚧 故障排除

### 🔍 常见问题

| 问题 | 解决方案 |
|------|---------|
| 🎤 语音识别失败 | 检查麦克风权限和网络连接 |
| 📱 应用无法打开 | 确认应用已安装且路径正确 |
| ⚡ 命令执行失败 | 检查命令语法和用户权限 |
| 🌐 API调用失败 | 验证API密钥和网络连接 |

### 🐛 调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🚀 开发计划

### 🎯 即将推出
- [ ] 📊 系统性能监控面板
- [ ] 🤖 自动化脚本支持
- [ ] 🔌 插件系统
- [ ] 📱 更多应用集成
- [ ] 🔄 系统备份功能
- [ ] 🌐 网络诊断工具

### 🔄 持续改进
- [ ] 🎨 用户界面优化
- [ ] ⚡ 性能提升
- [ ] 🌍 多语言支持
- [ ] 🔧 错误处理改进
- [ ] 📚 文档完善

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 🛠️ 开发环境设置
```bash
# 1. Fork项目
# 2. 克隆到本地
git clone https://github.com/yourusername/macOS-Copilot.git

# 3. 创建功能分支
git checkout -b feature/amazing-feature

# 4. 提交更改
git commit -m 'Add amazing feature'

# 5. 推送分支
git push origin feature/amazing-feature

# 6. 创建Pull Request
```

### 📝 贡献类型
- 🐛 Bug报告
- 💡 功能建议
- 📚 文档改进
- 🎨 UI/UX优化
- ⚡ 性能优化

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

---

## 📞 联系我们

- 🐛 **问题反馈**: [GitHub Issues](https://github.com/yourusername/macOS-Copilot/issues)
- 💬 **讨论交流**: [GitHub Discussions](https://github.com/yourusername/macOS-Copilot/discussions)
- 📧 **邮件联系**: your-email@example.com

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**

[![GitHub stars](https://img.shields.io/github/stars/yourusername/macOS-Copilot?style=social)](https://github.com/yourusername/macOS-Copilot)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/macOS-Copilot?style=social)](https://github.com/yourusername/macOS-Copilot)

**🎯 让macOS更智能，让生活更简单**

</div> 