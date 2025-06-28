import os
import time
import speech_recognition as sr
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter)
from PyQt6.QtCore import Qt, QTimer

# 导入自定义组件
from macOS_Copilot.ui.chat.area import ChatArea
from macOS_Copilot.ui.chat.input import InputArea
from macOS_Copilot.ui.sidebar import Sidebar
from macOS_Copilot.ui.knowledge.page import KnowledgeBasePage

# 导入工作线程
from macOS_Copilot.ui.workers.audio import AudioWorker
from macOS_Copilot.ui.workers.tts import TTSWorker
from macOS_Copilot.ui.workers.assistant import StreamingAssistantWorker

# 导入数据模型
from macOS_Copilot.models.knowledge import KnowledgeBase, KnowledgeItem

# 导入代理
from macOS_Copilot.agent.types import ArchitectureType, TaskComplexity
from macOS_Copilot.agent.assistant import IntelligentMacOSAssistant

class MacOSAssistantUI(QMainWindow):
    """macOS系统助手UI主窗口"""
    
    WELCOME_MESSAGE = (
        "# 🤖 macOS系统助手\n\n"
        "欢迎使用macOS系统助手！我可以帮助您管理macOS系统。\n\n"
        "## 🚀 主要功能\n\n"
        "### 🔧 系统管理\n"
        "- **系统信息查询** - 获取macOS版本、CPU、内存、磁盘使用情况\n"
        "- **进程管理** - 查看正在运行的进程，按CPU使用率排序\n"
        "- **网络监控** - 查看网络接口和连接状态\n"
        "- **电池状态** - 获取电池电量和剩余时间\n"
        "- **音量控制** - 设置系统音量\n\n"
        "### 📱 应用程序管理\n"
        "- **应用启动** - 打开系统内置和第三方应用程序\n"
        "- **应用列表** - 查看已安装的应用程序\n"
        "- **智能搜索** - 自动查找和启动应用程序\n\n"
        "### 📁 文件操作\n"
        "- **文件搜索** - 在指定目录中搜索文件\n"
        "- **笔记创建** - 快速创建文本笔记文件\n"
        "- **文件管理** - 基本的文件操作功能\n\n"
        "### 💻 终端集成\n"
        "- **命令执行** - 安全执行终端命令\n"
        "- **系统控制** - 通过命令行控制macOS系统\n\n"
        "## 💡 使用提示\n\n"
        "- 试试点击左侧的**预设命令**\n"
        "- 或者直接输入您的问题\n"
        "- 支持语音输入和文字输入\n"
        "- 助手回复支持Markdown格式\n\n"
        "**开始您的macOS管理之旅吧！** 🎉"
    )
    
    def __init__(self):
        super().__init__()
        
        # 初始化设置
        self.setWindowTitle('macOS系统助手')
        self.setGeometry(100, 100, 1600, 900)  # 进一步增加窗口宽度
        self.setMinimumSize(1300, 700)  # 增加最小窗口大小
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                color: #000000;
            }
            QTextEdit:focus {
                border: 1px solid #007AFF;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                color: #000000;
            }
            QLineEdit:focus {
                border: 1px solid #007AFF;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                color: #2c3e50;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            /* 新的滚动条样式 */
            QScrollBar:vertical {
                background: transparent;
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::handle:vertical:pressed {
                background: #808080;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            /* 水平滚动条样式 */
            QScrollBar:horizontal {
                background: transparent;
                height: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #c0c0c0;
                min-width: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #a0a0a0;
            }
            QScrollBar::handle:horizontal:pressed {
                background: #808080;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        
        # 初始化组件
        self.current_page = "chat"  # 页面状态：chat或kb
        
        # 初始化语音识别
        self.init_speech_recognition()
        
        # 初始化智能助手
        self.init_assistant()
        
        # 初始化知识库
        self.init_knowledge_base()
        
        # 创建UI组件
        self.create_ui()
        
        # 添加欢迎消息
        self.chat_area.add_message("助手", self.WELCOME_MESSAGE)
        
        # 启动工作线程
        self.start_workers()
        
        # 当前正在使用的架构和复杂度
        self.current_architecture = ArchitectureType.DIRECT
        self.current_complexity = TaskComplexity.SIMPLE
        
        # TTS状态
        self.is_speaking = False
        self.last_tts_time = 0
        
        # 定时更新指示器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_intelligence_indicators)
        self.update_timer.start(2000)  # 每2秒更新一次
    
    def init_speech_recognition(self):
        """初始化语音识别"""
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 1.0
        self.recognizer.phrase_threshold = 0.5
        self.recognizer.non_speaking_duration = 0.8
    
    def init_assistant(self):
        """初始化AI助手"""
        api_key = "sk-1b53c98a3b8c4abcaa1f68540ab3252d"  # 这里应该使用真实有效的API密钥
        # 使用直接导入，避免循环导入问题
        self.assistant = IntelligentMacOSAssistant(api_key)
    
    def init_knowledge_base(self):
        """初始化知识库"""
        # 定义知识库文件路径
        kb_file = os.path.join(os.path.expanduser("~"), "macOS_Copilot_knowledge.json")
        
        # 从文件加载知识库，如果文件不存在则创建新的知识库
        self.knowledge_base = KnowledgeBase.load_from_file(kb_file)
        
        # 如果知识库为空，添加默认知识条目
        if len(self.knowledge_base.get_all_items()) == 0:
            default_items = [
                {
                    "title": "如何使用macOS助手？", 
                    "content": "您可以在左侧输入问题或点击预设命令，助手会自动为您解答。支持自然语言交互，可以询问系统信息、打开应用、搜索文件等。"
                },
                {
                    "title": "常见系统命令速查", 
                    "content": "## 系统信息\n- 查看系统信息\n- 查看电池状态\n- 查看网络信息\n\n## 应用操作\n- 打开Safari\n- 打开终端\n- 列出正在运行的应用\n\n## 文件操作\n- 搜索文件\n- 创建笔记"
                },
                {
                    "title": "macOS快捷键大全", 
                    "content": "## 常用快捷键\n- **⌘ + C**: 复制\n- **⌘ + V**: 粘贴\n- **⌘ + X**: 剪切\n- **⌘ + Z**: 撤销\n- **⌘ + A**: 全选\n- **⌘ + F**: 查找\n- **⌘ + S**: 保存\n- **⌘ + P**: 打印\n- **⌘ + W**: 关闭窗口\n- **⌘ + Q**: 退出应用\n- **⌘ + Tab**: 切换应用\n- **⌘ + Space**: 打开Spotlight搜索\n\n## 截图快捷键\n- **⌘ + Shift + 3**: 全屏截图\n- **⌘ + Shift + 4**: 选择区域截图\n- **⌘ + Shift + 5**: 打开截图工具"
                },
                {
                    "title": "文件搜索技巧", 
                    "content": "在macOS助手中，您可以使用以下命令搜索文件：\n\n```\n搜索文件 [文件名]\n```\n\n例如：\n- 搜索文件 report.pdf\n- 搜索文件 *.jpg\n- 在桌面搜索 *.docx\n\n助手支持通配符和指定目录搜索。"
                },
            ]
            
            for item in default_items:
                self.knowledge_base.add_item_from_values(item["title"], item["content"])
    
    def create_ui(self):
        """创建UI界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建左侧边栏
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self.on_page_changed)
        self.sidebar.preset_command_clicked.connect(self.on_preset_command_clicked)
        
        # 创建右侧内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # 创建聊天区域
        self.chat_area = ChatArea()
        
        # 创建输入区域
        self.input_area = InputArea()
        self.input_area.message_sent.connect(self.on_message_sent)
        self.input_area.tts_toggled.connect(self.on_tts_toggled)
        self.input_area.voice_input_toggled.connect(self.on_voice_input_toggled)
        self.input_area.clear_chat_requested.connect(self.on_clear_chat_requested)
        
        # 创建知识库页面
        self.kb_page = KnowledgeBasePage(self.knowledge_base)
        # 连接知识库页面的查询信号到助手
        self.kb_page.query_to_assistant.connect(self.on_kb_query_to_assistant)
        
        # 默认显示聊天页面
        self.refresh_content_area()
        
        # 添加组件到主布局
        main_layout.addWidget(self.sidebar, 0)
        main_layout.addWidget(self.content_widget, 1)
    
    def refresh_content_area(self):
        """刷新内容区域"""
        # 清空内容区域
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        
        if self.current_page == "chat":
            self.content_layout.addWidget(self.chat_area, 1)
            self.content_layout.addWidget(self.input_area, 0)
        elif self.current_page == "kb":
            self.content_layout.addWidget(self.kb_page)
    
    def on_page_changed(self, page):
        """页面切换处理"""
        self.current_page = page
        self.refresh_content_area()
    
    def on_preset_command_clicked(self, command):
        """预设命令点击处理"""
        self.input_area.input_text.setPlainText(command)
        self.input_area.send_message()
    
    def on_message_sent(self, message):
        """消息发送处理"""
        # 添加用户消息
        self.chat_area.add_message("你", message)
        
        # 处理消息
        self.process_message(message)
    
    def process_message(self, text):
        """处理消息"""
        # 在发送前评估任务复杂度
        if hasattr(self.assistant, '_evaluate_task_complexity'):
            try:
                self.current_complexity = self.assistant._evaluate_task_complexity(text)
                print("当前复杂度：", self.current_complexity)
                # 根据复杂度选择架构
                self.current_architecture = self.assistant._select_architecture(self.current_complexity)
                print("当前架构：", self.current_architecture)
                # 更新显示
                self.update_intelligence_indicators()
            except Exception as e:
                print(f"复杂度评估错误: {str(e)}")
        
        # 创建空的助手消息气泡（用于流式更新）
        self.chat_area.current_assistant_bubble = self.chat_area.add_message("助手", "", create_empty=True)
        
        # 启动打字指示器
        self.chat_area.current_assistant_bubble.start_typing_indicator()
        
        # 如果存在上一个流式工作线程，停止它
        if hasattr(self, 'assistant_worker') and self.assistant_worker is not None:
            self.assistant_worker.stop()
            self.assistant_worker.wait(500)  # 等待最多500ms
        
        # 启动流式助手工作线程
        self.assistant_worker = StreamingAssistantWorker(self.assistant, text)
        self.assistant_worker.signals.stream_start.connect(self.on_stream_start)
        self.assistant_worker.signals.stream_chunk.connect(self.on_stream_chunk)
        self.assistant_worker.signals.stream_end.connect(self.on_stream_end)
        self.assistant_worker.signals.result.connect(self.on_assistant_response)
        self.assistant_worker.signals.error.connect(self.on_assistant_error)
        self.assistant_worker.signals.status.connect(self.on_worker_status)
        self.assistant_worker.signals.stream_thinking.connect(self.on_stream_thinking)
        self.assistant_worker.start()
    
    def on_stream_start(self):
        """流式输出开始处理"""
        self.sidebar.update_status("AI正在回答...")
    
    def on_stream_chunk(self, chunk):
        """流式文本块处理"""
        if hasattr(self.chat_area, 'current_assistant_bubble') and self.chat_area.current_assistant_bubble:
            self.chat_area.current_assistant_bubble.append_text(chunk)
            
            # 仅当用户当前在底部时才自动滚动
            QTimer.singleShot(10, self.chat_area.scroll_to_bottom)
    
    def on_stream_end(self):
        """流式输出结束处理"""
        self.sidebar.update_status("回答已完成")
        
        # 确保打字指示器被关闭
        if hasattr(self.chat_area, 'current_assistant_bubble') and self.chat_area.current_assistant_bubble:
            self.chat_area.current_assistant_bubble.stop_typing_indicator()
        
        # 恢复发送按钮状态
        self.input_area.reset_sending_state()
    
    def on_assistant_response(self, response):
        """助手响应处理"""
        # 流式显示已经完成，这里主要用于TTS等后续处理
        self.sidebar.update_status("回答已完成")
        
        # 确保打字指示器被关闭
        if hasattr(self.chat_area, 'current_assistant_bubble') and self.chat_area.current_assistant_bubble:
            self.chat_area.current_assistant_bubble.stop_typing_indicator()
        
        # 如果启用了TTS，播放响应
        if hasattr(self, 'is_tts_enabled') and self.is_tts_enabled:
            self.speak_response(response)
        
        # 清除当前助手气泡引用
        self.chat_area.current_assistant_bubble = None
    
    def on_assistant_error(self, error_msg):
        """助手错误处理"""
        self.sidebar.update_status(f"错误: {error_msg}")
        
        # 恢复发送按钮状态
        self.input_area.reset_sending_state()
        
        # 关闭任何活动的指示器
        if hasattr(self.chat_area, 'current_assistant_bubble') and self.chat_area.current_assistant_bubble:
            self.chat_area.current_assistant_bubble.stop_typing_indicator()
    
    def on_tts_toggled(self, enabled):
        """TTS开关切换处理"""
        self.is_tts_enabled = enabled
        self.sidebar.update_status("AI朗读已" + ("启用" if enabled else "禁用"))
    
    def on_voice_input_toggled(self, enabled):
        """语音输入开关切换处理"""
        if hasattr(self, 'audio_worker'):
            self.audio_worker.set_paused(not enabled)
            self.sidebar.update_status("语音输入已" + ("启用" if enabled else "禁用"))
    
    def on_clear_chat_requested(self):
        """清空聊天记录处理"""
        self.chat_area.clear_chat()
        self.chat_area.add_message("助手", self.WELCOME_MESSAGE)
    
    def start_workers(self):
        """启动工作线程"""
        # 启动音频识别线程
        self.audio_worker = AudioWorker(self.recognizer)
        self.audio_worker.signals.result.connect(self.on_recognized_text)
        self.audio_worker.signals.error.connect(self.on_audio_worker_error)
        self.audio_worker.signals.status.connect(self.on_audio_worker_status)
        self.audio_worker.start()
        
        # 启动后立即禁用语音输入
        self.audio_worker.set_paused(True)
        
        # 初始化TTS工作线程
        self.tts_worker = TTSWorker()
        self.tts_worker.signals.finished.connect(self.on_tts_finished)
        self.tts_worker.signals.error.connect(self.on_tts_error)
    
    def on_recognized_text(self, text):
        """处理语音识别文本"""
        self.input_area.input_text.setPlainText(text)
        self.input_area.send_message()
    
    def on_audio_worker_error(self, error_msg):
        """处理音频工作线程错误"""
        self.sidebar.update_status(f"语音识别错误: {error_msg}")
    
    def on_audio_worker_status(self, status_msg):
        """处理音频工作线程状态"""
        self.sidebar.update_status(status_msg)
    
    def on_tts_error(self, error_msg):
        """处理TTS错误"""
        self.sidebar.update_status(f"TTS错误: {error_msg}")
        
        # 重置TTS状态
        self.is_speaking = False
        self.audio_worker.set_speaking(False)
    
    def speak_response(self, text):
        """语音播放响应"""
        if not hasattr(self, 'is_tts_enabled') or not self.is_tts_enabled:
            return  # 如果TTS未启用，不播放语音
        
        # 检查上次TTS的时间，确保至少间隔1秒
        current_time = time.time()
        if (current_time - self.last_tts_time) < 1:
            time.sleep(1)  # 确保至少等待1秒，防止系统资源冲突
        
        # 确保任何之前的语音合成已经结束
        if hasattr(self, 'tts_worker') and self.tts_worker.isRunning():
            self.tts_worker.wait(1000)  # 最多等待1秒
        
        # 记录本次TTS开始时间    
        self.last_tts_time = time.time()
            
        # 优先关闭语音识别，先暂停录音，设置状态
        self.is_speaking = True
        if hasattr(self, 'audio_worker'):
            self.audio_worker.set_speaking(True)  # 防止AI说话时录音
        
        # 强制暂停一小段时间，让麦克风完全释放
        time.sleep(0.5)
        
        # 更新状态
        self.sidebar.update_status("AI朗读中，语音输入已禁用...")
            
        # 开始语音合成并播放
        self.tts_worker.set_text(text)
        self.tts_worker.start()
    
    def on_tts_finished(self):
        """TTS完成回调"""
        # 等待音频播放器彻底关闭
        time.sleep(0.5)
        
        # 重置状态
        self.is_speaking = False
        
        # 适当延迟后再恢复语音输入，确保系统处理完扬声器输出
        QTimer.singleShot(1000, self._update_after_tts)
    
    def _update_after_tts(self):
        """TTS完成后更新状态（带延迟）"""
        # 最后才重置语音识别的speaking状态，确保麦克风完全重置
        if hasattr(self, 'audio_worker'):
            self.audio_worker.set_speaking(False)
        
        # 更新状态
        input_enabled = hasattr(self, 'input_area') and hasattr(self.input_area, 'is_voice_input_enabled') and self.input_area.is_voice_input_enabled
        self.sidebar.update_status("语音输入已" + ("启用" if input_enabled else "禁用"))
    
    def update_intelligence_indicators(self):
        """更新智能指标显示"""
        if not hasattr(self, 'input_area'):
            return
            
        try:
            # 架构名称映射
            arch_name_map = {
                ArchitectureType.DIRECT: "直接响应",
                ArchitectureType.BASIC_COT: "基础思考链",
                ArchitectureType.FULL_COT: "完整思考链", 
                ArchitectureType.REACT: "ReAct模式",
                ArchitectureType.PLANNER: "规划架构"
            }
            
            # 复杂度名称映射
            complexity_name_map = {
                TaskComplexity.SIMPLE: "简单",
                TaskComplexity.MEDIUM: "中等",
                TaskComplexity.COMPLEX: "复杂",
                TaskComplexity.ADVANCED: "高级"
            }
            
            # 颜色映射
            arch_colors = {
                ArchitectureType.DIRECT: "#007AFF",      # 蓝色
                ArchitectureType.BASIC_COT: "#5cb85c",   # 绿色
                ArchitectureType.FULL_COT: "#f0ad4e",    # 橙色
                ArchitectureType.REACT: "#d9534f",       # 红色
                ArchitectureType.PLANNER: "#9c27b0"      # 紫色
            }
            
            complexity_colors = {
                TaskComplexity.SIMPLE: "#28a745",      # 绿色
                TaskComplexity.MEDIUM: "#17a2b8",      # 青色
                TaskComplexity.COMPLEX: "#fd7e14",     # 橙色
                TaskComplexity.ADVANCED: "#dc3545"     # 红色
            }
            
            # 获取当前使用的架构和复杂度
            arch_name = arch_name_map.get(self.current_architecture, "直接响应")
            complexity_name = complexity_name_map.get(self.current_complexity, "简单")
            
            # 获取对应的颜色
            arch_color = arch_colors.get(self.current_architecture, "#007AFF")
            complexity_color = complexity_colors.get(self.current_complexity, "#28a745")
            
            # 更新UI显示
            self.input_area.update_intelligence_indicators(
                arch_name, complexity_name, arch_color, complexity_color)
            
        except Exception as e:
            print(f"更新智能指标错误: {str(e)}")
    
    def on_worker_status(self, status):
        """处理工作线程状态更新"""
        self.sidebar.update_status(status)
        
    def on_stream_thinking(self, is_thinking):
        """处理思考状态变化"""
        if is_thinking:
            self.sidebar.update_status("AI正在思考...")
            # 可以在这里添加思考指示器的显示
        else:
            self.sidebar.update_status("AI正在回答...")
            # 可以在这里隐藏思考指示器
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 关闭录音工作线程
        if hasattr(self, 'audio_worker'):
            # 确保麦克风已释放
            if hasattr(self.audio_worker, 'microphone') and self.audio_worker.microphone:
                try:
                    self.audio_worker.microphone.__exit__(None, None, None)
                except:
                    pass
            self.audio_worker.stop()
            self.audio_worker.wait()
            
        # 关闭TTS工作线程
        if hasattr(self, 'tts_worker'):
            self.tts_worker.quit()
            self.tts_worker.wait()
            
        # 删除所有遗留的临时音频文件
        try:
            for file in os.listdir():
                if file.startswith("temp_") and file.endswith(".mp3"):
                    try:
                        os.remove(file)
                    except:
                        pass
        except:
            pass
            
        event.accept()

    def on_kb_query_to_assistant(self, query):
        """处理从知识库发送到助手的查询"""
        # 切换到聊天页面
        self.current_page = "chat"
        self.sidebar.chat_nav_btn.setChecked(True)
        self.sidebar.kb_nav_btn.setChecked(False)
        self.refresh_content_area()
        
        # 设置输入框文本
        self.input_area.input_text.setPlainText(query)
        
        # 发送消息
        self.input_area.send_message() 