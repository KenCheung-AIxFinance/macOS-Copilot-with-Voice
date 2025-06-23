import sys
import threading
import queue
import time
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QPushButton, QLabel, QFrame,
                            QScrollArea, QSplitter, QListWidget, QListWidgetItem,
                            QTextBrowser, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject, QSize, QPropertyAnimation, QEasingCurve, QPoint, QRectF, pyqtProperty
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QTextCursor, QTextOption, QBrush, QPen, QPainter, QPainterPath
import speech_recognition as sr
import edge_tts
import asyncio
from openai import OpenAI
import os
import tempfile
from langdetect import detect, DetectorFactory
import re
import markdown

# 导入我们的macOS助手
from agent import IntelligentMacOSAssistant, ArchitectureType, TaskComplexity, EnhancedStreamingHandler

class WorkerSignals(QObject):
    """定义工作线程的信号"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(str)
    status = pyqtSignal(str)
    stream_chunk = pyqtSignal(str)  # 流式文本块信号
    stream_start = pyqtSignal()     # 流式输出开始信号
    stream_end = pyqtSignal()       # 流式输出结束信号
    stream_thinking = pyqtSignal(bool)  # 流式思考状态信号（用于显示思考指示器）

class AudioWorker(QThread):
    """处理音频识别的工作线程"""
    def __init__(self, recognizer):
        super().__init__()
        self.recognizer = recognizer
        self.signals = WorkerSignals()
        self.is_running = True
        self.is_speaking = False
        self.is_paused = False
        self.microphone = None
        self.should_reset = False

    def set_speaking(self, speaking):
        """设置说话状态"""
        self.is_speaking = speaking
        if speaking:
            # 当AI开始说话时，标记需要重置麦克风
            self.should_reset = True
            
    def set_paused(self, paused):
        """设置暂停状态"""
        self.is_paused = paused
        if paused or not paused:
            # 无论是暂停还是取消暂停，都标记需要重置麦克风
            self.should_reset = True

    def run(self):
        while self.is_running:
            # 处理正常语音识别
            if not self.is_speaking and not self.is_paused:
                try:
                    # 如果需要重置麦克风，则关闭当前麦克风并重新创建
                    if self.should_reset:
                        if self.microphone:
                            try:
                                self.microphone.__exit__(None, None, None)
                            except:
                                pass
                            self.microphone = None
                        time.sleep(0.5)  # 短暂等待，确保资源释放
                        self.should_reset = False
                    
                    # 创建新的麦克风连接
                    if not self.microphone:
                        self.microphone = sr.Microphone().__enter__()
                        # 调整噪声阈值
                        self.recognizer.adjust_for_ambient_noise(self.microphone, duration=0.5)
                        
                    self.signals.status.emit("正在聆听...")
                    audio = self.recognizer.listen(
                        self.microphone, 
                        timeout=5, 
                        phrase_time_limit=10
                    )
                    self.signals.status.emit("正在处理...")
                    text = self.recognizer.recognize_google(audio, language='zh-CN')
                    self.signals.result.emit(text)
                    
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    self.signals.error.emit(f"语音识别错误: {str(e)}")
                    # 发生错误时标记需要重置麦克风
                    self.should_reset = True
                    time.sleep(0.5)
                    
            elif self.is_speaking:
                # AI说话时，关闭麦克风连接，完全停止录音
                if self.microphone:
                    try:
                        self.microphone.__exit__(None, None, None)
                    except:
                        pass
                    self.microphone = None
                
                self.signals.status.emit("AI朗读中，语音识别已禁用...")
                time.sleep(0.5)  # 减少CPU使用
                
            elif self.is_paused:
                # 暂停状态，不进行任何录音
                if self.microphone:
                    try:
                        self.microphone.__exit__(None, None, None)
                    except:
                        pass
                    self.microphone = None
                
                # self.signals.status.emit("语音输入已暂停")
                time.sleep(0.5)
                
            time.sleep(0.1)

    def stop(self):
        self.is_running = False

class TTSWorker(QThread):
    """处理语音合成的工作线程"""
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self.text = ""
        self.voice = 'zh-CN-XiaoxiaoNeural'

    def set_text(self, text):
        self.text = text

    def run(self):
        try:
            # 生成唯一的临时文件名，避免多次调用冲突
            temp_file = f"temp_{int(time.time())}.mp3"
            
            # 语音合成与播放
            communicate = edge_tts.Communicate(self.text, self.voice)
            asyncio.run(communicate.save(temp_file))
            os.system(f"afplay {temp_file}")
            
            # 合成完成后删除临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            self.signals.error.emit(f"TTS错误: {str(e)}")
        finally:
            self.signals.finished.emit()

class StreamingAssistantWorker(QThread):
    """处理助手流式响应的工作线程"""
    def __init__(self, assistant, user_input):
        super().__init__()
        self.assistant = assistant
        self.user_input = user_input
        self.signals = WorkerSignals()
        self.active = True  # 控制线程是否继续处理
        
        # 流式处理器配置
        self.streaming_handler = None

    def stop(self):
        """停止流式输出处理"""
        self.active = False

    def run(self):
        try:
            # 发送流式输出开始信号
            self.signals.stream_start.emit()
            
            # 创建增强的流式处理器
            self.streaming_handler = EnhancedStreamingHandler(
                streaming_callback=lambda token: self.handle_token(token),
                thinking_callback=lambda is_thinking: self.signals.stream_thinking.emit(is_thinking),
                start_callback=lambda: self.signals.stream_start.emit(),
                end_callback=lambda: self.signals.stream_end.emit()
            )
            
            # 使用流式响应
            full_response = ""
            
            # 如果assistant有自定义的stream_with_handler方法，使用它
            if hasattr(self.assistant, 'stream_with_handler'):
                # 这是一个假设的方法，实际上需要在agent.py中实现
                for chunk in self.assistant.stream_with_handler(self.user_input, self.streaming_handler):
                    if not self.active:
                        break  # 如果被停止则中断处理
                    
                    full_response += chunk
            else:
                # 使用标准stream方式
                for chunk in self.assistant.chat_stream(self.user_input):
                    if not self.active:
                        break  # 如果被停止则中断处理
                    
                    full_response += chunk
                    # 发送单个文本块
                    self.signals.stream_chunk.emit(chunk)
                    
                    # 短暂延时以优化UI响应
                    QThread.msleep(10)
            
            # 发送完整响应用于其他处理（如TTS）
            if self.active:  # 只在正常完成时发送结果
                self.signals.result.emit(full_response)
                
            # 发送流式输出结束信号
            self.signals.stream_end.emit()
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()
            
    def handle_token(self, token):
        """处理从增强流式处理器收到的单个令牌"""
        if not self.active:
            return
        
        # 发送文本块
        self.signals.stream_chunk.emit(token)

class StatusLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #2c3e50;
                padding: 12px 20px;
                background-color: #ecf0f1;
                border-radius: 8px;
                border: 2px solid #bdc3c7;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(50)

class ChatBubble(QFrame):
    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.current_text = text  # 保存当前文本内容
        self.typing_indicator = None
        self.breathing_dots = None
        
        if not is_user:
            # 只为助手消息添加动画指示器
            self.breathing_dots = BreathingDotIndicator(self, 
                                                     dot_color="#007AFF", 
                                                     dot_count=3, 
                                                     dot_size=8)
            self.breathing_dots.hide()
        
        # 设置样式 - 全宽设计
        if is_user:
            self.setStyleSheet("""
                QFrame {
                    background-color: #f0f8ff; /* 浅蓝色背景 */
                    border-top: 1px solid #e5e5e5;
                    border-bottom: 1px solid #e5e5e5;
                    padding: 16px 24px;
                    color: #2c3e50;
                    font-size: 14px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-top: 1px solid #e5e5e5;
                    border-bottom: 1px solid #e5e5e5;
                    padding: 16px 24px;
                    color: #2c3e50;
                    font-size: 14px;
                }
            """)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 为全宽设计移除最大宽度限制
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # 创建文本浏览器来支持Markdown
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        
        # 完全禁用滚动条
        self.text_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 设置优化的自动换行
        self.text_browser.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        
        # 设置大小策略为完全自适应
        self.text_browser.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        # 文本不可编辑，但可选择
        self.text_browser.setReadOnly(True)
        self.text_browser.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        
        # 设置文本浏览器样式
        if is_user:
            self.text_browser.setStyleSheet("""
                QTextBrowser {
                    background-color: transparent;
                    border: none;
                    color: #2c3e50;
                    font-size: 14px;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    line-height: 1.5;
                    padding: 0 36px;
                }
                QTextBrowser a {
                    color: #007AFF;
                    text-decoration: underline;
                }
            """)
        else:
            self.text_browser.setStyleSheet("""
                QTextBrowser {
                    background-color: transparent;
                    border: none;
                    color: #2c3e50;
                    font-size: 14px;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    line-height: 1.6;
                    padding: 0 36px;
                }
                QTextBrowser a {
                    color: #007AFF;
                    text-decoration: underline;
                }
                QTextBrowser code {
                    background-color: #f1f2f6;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace;
                    font-size: 13px;
                }
                QTextBrowser pre {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    padding: 12px;
                    margin: 12px 0;
                    font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace;
                    font-size: 13px;
                    overflow: auto;
                    width: 95%;
                }
                QTextBrowser h1, QTextBrowser h2, QTextBrowser h3, QTextBrowser h4, QTextBrowser h5, QTextBrowser h6 {
                    margin: 20px 0 10px 0;
                    font-weight: 600;
                }
                QTextBrowser h1 { font-size: 22px; }
                QTextBrowser h2 { font-size: 20px; }
                QTextBrowser h3 { font-size: 18px; }
                QTextBrowser ul, QTextBrowser ol {
                    margin: 10px 0;
                    padding-left: 24px;
                }
                QTextBrowser li {
                    margin: 6px 0;
                }
                QTextBrowser blockquote {
                    border-left: 4px solid #007AFF;
                    padding: 0 12px;
                    margin: 12px 0;
                    color: #6c757d;
                }
                QTextBrowser table {
                    border-collapse: collapse;
                    width: 95%;
                    margin: 16px 0;
                }
                QTextBrowser th, QTextBrowser td {
                    border: 1px solid #dee2e6;
                    padding: 8px 12px;
                    text-align: left;
                }
                QTextBrowser th {
                    background-color: #f8f9fa;
                    font-weight: bold;
                }
                /* 自定义文本浏览器滚动条 */
                QScrollBar:vertical {
                    background: transparent;
                    width: 10px;
                    margin: 1px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(160, 160, 160, 0.3);
                    min-height: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover {
                    background: rgba(160, 160, 160, 0.6);
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
                QScrollBar:horizontal {
                    background: transparent;
                    height: 10px;
                    margin: 1px;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal {
                    background: rgba(160, 160, 160, 0.3);
                    min-width: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: rgba(160, 160, 160, 0.6);
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                    background: none;
                }
            """)
        
        # 处理Markdown内容
        if is_user:
            # 用户消息不进行Markdown处理，直接显示
            self.text_browser.setPlainText(text)
        else:
            # 助手消息进行Markdown处理
            self.update_text(text)
        
        # 添加文本浏览器到布局
        layout.addWidget(self.text_browser)
        
        # 设置自适应大小
        self.adjustSize()
        
        # 修正气泡宽度
        self.adjustWidth()
        
        # 如果是助手气泡，确保呼吸动画在适当的位置
        if not is_user and self.breathing_dots:
            # 放在文本区域顶部中央
            self.breathing_dots.move(
                self.width() // 2 - self.breathing_dots.width() // 2, 
                self.text_browser.pos().y() + 10
            )
    
    def update_text(self, text):
        """更新文本内容（支持流式更新）"""
        self.current_text = text
        
        if self.is_user:
            # 用户消息直接显示纯文本
            self.text_browser.setPlainText(text)
        else:
            # 助手消息进行Markdown处理
            try:
                # 转换Markdown为HTML
                html_content = markdown.markdown(
                    text,
                    extensions=['fenced_code', 'codehilite', 'tables', 'nl2br']
                )
                self.text_browser.setHtml(html_content)
            except Exception as e:
                # 如果Markdown处理失败，显示原始文本
                self.text_browser.setPlainText(text)
        
        # 更新布局
        self.adjustWidth()
    
    def start_typing_indicator(self):
        """开始显示输入指示器"""
        if self.breathing_dots and self.current_text == "":
            # 更新位置确保居中
            self.breathing_dots.move(
                self.width() // 2 - self.breathing_dots.width() // 2, 
                self.text_browser.pos().y() + 10
            )
            self.breathing_dots.start_animation()
    
    def stop_typing_indicator(self):
        """停止显示输入指示器"""
        if self.breathing_dots:
            self.breathing_dots.stop_animation()
    
    def resizeEvent(self, event):
        """重绘事件，更新呼吸动画位置"""
        super().resizeEvent(event)
        # 更新呼吸动画位置
        if self.breathing_dots:
            self.breathing_dots.move(
                self.width() // 2 - self.breathing_dots.width() // 2, 
                self.text_browser.pos().y() + 10
            )
    
    def append_text(self, text_chunk):
        """追加文本内容（用于流式显示）"""
        # 如果有文本开始出现，停止打字指示器
        if self.current_text == "" and text_chunk != "":
            self.stop_typing_indicator()
            
        self.current_text += text_chunk
        
        # 对于小块文本更新，使用更高效的处理方式
        if len(text_chunk) < 100 and not ("\n" in text_chunk or "```" in text_chunk):
            # 纯文本小块更新，不需要完全重新渲染Markdown
            if self.is_user:
                cursor = self.text_browser.textCursor()
                cursor.movePosition(QTextCursor.End)
                cursor.insertText(text_chunk)
            else:
                # 助手消息，需要重新渲染Markdown以支持格式化
                self.update_text(self.current_text)
        else:
            # 大块文本或包含特殊格式，完全重新渲染
            self.update_text(self.current_text)
            
        # 调整宽度和滚动位置
        QTimer.singleShot(10, self.adjustWidth)
        
    def adjustWidth(self):
        """完全自适应文本高度，无滚动条"""
        # 获取文档内容的大小
        doc = self.text_browser.document()
        doc.adjustSize()  # 先调整文档大小
        doc_size = doc.size().toSize()
        
        # 获取内容高度和宽度
        content_height = doc_size.height()
        
        # 清除所有高度和宽度限制
        self.text_browser.setMinimumHeight(0)
        self.text_browser.setMaximumHeight(99999) # 实际无限制
        
        # 设置自适应高度
        self.text_browser.setFixedHeight(content_height + 30) # 额外空间用于边距
        
        # 关闭所有滚动条
        self.text_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 更新布局
        self.text_browser.updateGeometry()
        self.updateGeometry()
        self.adjustSize()

class BreathingDotIndicator(QWidget):
    """渐变呼吸动画的圆点加载指示器"""
    def __init__(self, parent=None, dot_color="#007AFF", dot_count=3, dot_size=10):
        super().__init__(parent)
        
        # 基本配置
        self.dot_color = dot_color      # 圆点颜色
        self.dot_count = dot_count      # 圆点数量
        self.dot_size = dot_size        # 圆点大小
        self.dot_spacing = dot_size*2   # 圆点间距
        self.opacity_values = [0.3] * dot_count  # 每个圆点的不透明度
        
        # 设置组件大小
        width = dot_count * dot_size * 3
        height = dot_size * 3
        self.setFixedSize(width, height)
        
        # 设置动画
        self.animations = []
        self.setup_animations()
        
        # 初始隐藏
        self.hide()
    
    def setup_animations(self):
        """设置动画效果"""
        delay = 200  # 动画延迟时间(毫秒)
        
        for i in range(self.dot_count):
            # 为每个点创建不透明度变化动画
            anim = QPropertyAnimation(self, b"opacity" + str(i).encode())
            anim.setDuration(1200)  # 动画持续时间
            anim.setStartValue(0.2)
            anim.setEndValue(1.0)
            anim.setLoopCount(-1)    # 无限循环
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)  # 动画曲线
            
            # 设置自动反向，产生呼吸效果
            anim.setDirection(QPropertyAnimation.Direction.Forward)
            
            # 添加延迟，使每个点的动画错开
            # 不使用setStartTime，而是在启动动画时使用QTimer实现延迟
            self.animations.append((anim, i * delay))
    
    def start_animation(self):
        """开始动画，带有错开延迟效果"""
        self.show()
        
        # 启动每个动画，使用QTimer实现延迟
        for anim, delay in self.animations:
            # 为每个动画创建单独的延时启动
            QTimer.singleShot(delay, lambda a=anim: a.start())
    
    def stop_animation(self):
        """停止动画"""
        for anim, _ in self.animations:
            anim.stop()
        self.hide()
    
    # 动态属性访问器
    def get_opacity(self, index):
        return self.opacity_values[index]
    
    def set_opacity(self, index, value):
        if 0 <= index < len(self.opacity_values):
            self.opacity_values[index] = value
            self.update()  # 触发重绘
    
    # 动态创建属性
    for i in range(10):  # 足够多的点
        locals()[f'opacity{i}'] = pyqtProperty(float, 
                                      lambda self, i=i: self.get_opacity(i), 
                                      lambda self, val, i=i: self.set_opacity(i, val))
    
    def paintEvent(self, event):
        """绘制事件，渲染圆点"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 抗锯齿
        
        # 圆点基本参数
        x_center = self.width() // 2
        y_center = self.height() // 2
        radius = self.dot_size // 2
        spacing = self.dot_spacing
        
        # 计算第一个点的位置
        x_start = x_center - ((self.dot_count - 1) * spacing) // 2
        
        for i in range(self.dot_count):
            x = x_start + i * spacing
            
            # 设置颜色和不透明度
            color = QColor(self.dot_color)
            color.setAlphaF(self.opacity_values[i])
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)  # 无边框
            
            # 绘制圆点
            painter.drawEllipse(QPoint(x, y_center), radius, radius)

class MacOSAssistantUI(QMainWindow):
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
        self.setWindowTitle('macOS系统助手')
        self.setGeometry(100, 100, 1600, 900)  # 进一步增加窗口宽度
        self.setMinimumSize(1300, 700)  # 增加最小窗口大小
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                color: #2c3e50;
            }
            QTextEdit:focus {
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
        
        # 初始化语音识别
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 1.0
        self.recognizer.phrase_threshold = 0.5
        self.recognizer.non_speaking_duration = 0.8
        
        # 初始化macOS智能助手
        api_key = "sk-1b53c98a3b8c4abcaa1f68540ab3252d"
        self.assistant = IntelligentMacOSAssistant(api_key)
        
        self.current_page = "chat"  # "chat" or "kb"
        self.knowledge_base_container = None
        self.init_ui()
        
        # 对话状态
        self.is_speaking = False
        
        # 启动工作线程
        self.start_workers()
        
        # 默认关闭语音功能
        self.audio_worker.set_paused(True)  # 默认暂停语音输入
        
        # 添加安全延迟防止麦克风冲突
        self.last_tts_time = 0
        
        # 预设命令列表
        self.preset_commands = [
            "查看系统信息",
            "打开Safari",
            "打开终端",
            "查看电池状态",
            "查看网络信息",
            "查看运行进程",
            "搜索文件",
            "设置音量为50%",
            "创建笔记",
            "获取当前时间"
        ]
        
        self.update_preset_commands()
        
        # 当前正在使用的架构
        self.current_architecture = ArchitectureType.DIRECT
        self.current_complexity = TaskComplexity.SIMPLE
        
        # 定时更新指示器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_intelligence_indicators)
        self.update_timer.start(2000)  # 每2秒更新一次
        
    def init_ui(self):
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧边栏
        self.create_sidebar()
        main_layout.addWidget(self.sidebar, 0)
        
        # 右侧主内容区域
        self.create_main_content()
        main_layout.addWidget(self.main_content, 1)
        
        # 添加欢迎消息
        self.add_message("助手", self.WELCOME_MESSAGE)
    
    def create_sidebar(self):
        """
        创建左侧边栏，顶部加入导航栏
        """
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(300)
        self.sidebar.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-right: 1px solid #e5e5e5;
            }
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(16)

        # ======= 新增导航栏 =======
        nav_bar = QWidget()
        nav_bar_layout = QHBoxLayout(nav_bar)
        nav_bar_layout.setContentsMargins(0, 0, 0, 0)
        nav_bar_layout.setSpacing(8)
        self.chat_nav_btn = QPushButton("💬 对话")
        self.kb_nav_btn = QPushButton("📚 知识库")
        for btn in [self.chat_nav_btn, self.kb_nav_btn]:
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e3f2fd;
                    color: #1976d2;
                    border: none;
                    border-radius: 8px;
                    font-size: 15px;
                    font-weight: 600;
                    padding: 8px 18px;
                }
                QPushButton:checked {
                    background-color: #1976d2;
                    color: white;
                }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chat_nav_btn.setChecked(True)
        self.chat_nav_btn.clicked.connect(self.switch_to_chat_page)
        self.kb_nav_btn.clicked.connect(self.switch_to_kb_page)
        nav_bar_layout.addWidget(self.chat_nav_btn)
        nav_bar_layout.addWidget(self.kb_nav_btn)
        nav_bar_layout.addStretch(1)
        sidebar_layout.addWidget(nav_bar)
        # ======= 导航栏结束 =======

        # 标题
        title_label = QLabel("macOS助手")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px 0;
            }
        """)
        sidebar_layout.addWidget(title_label)
        
        # 预设命令标题
        preset_label = QLabel("快速命令")
        preset_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #6c757d;
                padding: 8px 0;
            }
        """)
        sidebar_layout.addWidget(preset_label)
        
        # 预设命令列表
        self.preset_list = QListWidget()
        self.preset_list.itemClicked.connect(self.on_preset_clicked)
        self.preset_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                padding: 4px;
                font-size: 13px;
                color: #2c3e50;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            /* 自定义侧边栏列表滚动条 */
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 2px 2px 2px 2px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(180, 180, 180, 0.3);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(180, 180, 180, 0.7);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        sidebar_layout.addWidget(self.preset_list)
        
        # 状态指示器
        self.status_indicator = QLabel("🟢 系统正常")
        self.status_indicator.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #6c757d;
                padding: 8px 0;
            }
        """)
        sidebar_layout.addWidget(self.status_indicator)
        
        sidebar_layout.addStretch()
    
    def create_main_content(self):
        """
        创建主内容区，支持页面切换
        """
        self.main_content = QWidget()
        self.main_content.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        self.main_layout = QVBoxLayout(self.main_content)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.refresh_main_content()

    def refresh_main_content(self):
        # 清空主内容区
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        if self.current_page == "chat":
            self.create_chat_area()
            self.main_layout.addWidget(self.chat_container, 1)
            self.create_input_area()
            self.main_layout.addWidget(self.input_container, 0)
            # ====== 保证欢迎信息存在 ======
            if hasattr(self, 'chat_layout') and self.chat_layout.count() == 1:
                self.add_message("助手", self.WELCOME_MESSAGE)
        elif self.current_page == "kb":
            if not self.knowledge_base_container:
                self.knowledge_base_container = self.create_knowledge_base_page()
            self.main_layout.addWidget(self.knowledge_base_container, 1)

    def switch_to_chat_page(self):
        self.current_page = "chat"
        self.chat_nav_btn.setChecked(True)
        self.kb_nav_btn.setChecked(False)
        self.refresh_main_content()

    def switch_to_kb_page(self):
        self.current_page = "kb"
        self.chat_nav_btn.setChecked(False)
        self.kb_nav_btn.setChecked(True)
        self.refresh_main_content()

    def create_knowledge_base_page(self):
        kb_widget = QWidget()
        kb_layout = QVBoxLayout(kb_widget)
        kb_layout.setContentsMargins(32, 32, 32, 32)
        kb_layout.setSpacing(18)
        title = QLabel("📚 知识库")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1976d2; margin-bottom: 12px;")
        kb_layout.addWidget(title)
        desc = QLabel("这里可以展示您的知识库内容、FAQ、文档、快捷指令等。")
        desc.setStyleSheet("font-size: 15px; color: #444; margin-bottom: 8px;")
        kb_layout.addWidget(desc)
        # 示例知识点列表
        kb_list = QListWidget()
        kb_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                font-size: 14px;
                color: #2c3e50;
            }
            QListWidget::item {
                padding: 10px 16px;
                border-radius: 4px;
                margin: 3px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
        kb_list.addItem("如何使用macOS助手？")
        kb_list.addItem("常见系统命令速查")
        kb_list.addItem("快捷键大全")
        kb_list.addItem("文件搜索技巧")
        kb_list.addItem("更多内容即将上线...")
        kb_layout.addWidget(kb_list, 1)
        return kb_widget
    
    def create_chat_area(self):
        """创建聊天区域"""
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        
        chat_layout = QVBoxLayout(self.chat_container)
        chat_layout.setContentsMargins(24, 24, 24, 24)
        chat_layout.setSpacing(0)
        
        # 聊天显示区域
        self.chat_area = QScrollArea()
        self.chat_area.setStyleSheet("""
            QScrollArea {
                background-color: #ffffff;
                border: none;
            }
            /* 自定义聊天区域滚动条 */
            QScrollBar:vertical {
                background: transparent;
                width: 14px;
                margin: 2px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background: rgba(160, 160, 160, 0.5);
                min-height: 30px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(160, 160, 160, 0.8);
            }
            QScrollBar::handle:vertical:pressed {
                background: rgba(128, 128, 128, 0.9);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # 创建聊天内容容器
        self.chat_widget = QWidget()
        self.chat_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.MinimumExpanding
        )
        
        # 创建聊天布局
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setSpacing(0)  # 移除消息间距以实现全屏连续布局
        self.chat_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.addStretch()
        
        # 设置滚动区域属性
        self.chat_area.setWidget(self.chat_widget)
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 添加滚动区域到聊天容器
        chat_layout.addWidget(self.chat_area)
    
    def create_input_area(self):
        """创建输入区域"""
        self.input_container = QWidget()
        self.input_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-top: 1px solid #e5e5e5;
            }
        """)
        
        input_layout = QVBoxLayout(self.input_container)
        input_layout.setContentsMargins(32, 16, 32, 24)
        input_layout.setSpacing(16)
        
        # 创建控制面板 - 更简约设计
        control_panel = QWidget()
        control_panel.setStyleSheet("""
            QWidget {
                background-color: #fafbfc;
                border: none;
                border-radius: 8px;
            }
        """)
        
        control_panel_layout = QHBoxLayout(control_panel)
        control_panel_layout.setContentsMargins(12, 10, 12, 10)
        control_panel_layout.setSpacing(12)
        
        # 创建状态显示容器
        status_container = self.create_status_display_container()
        control_panel_layout.addWidget(status_container, 3)
        
        # 添加垂直分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                width: 1px;
                margin-top: 5px;
                margin-bottom: 5px;
            }
        """)
        control_panel_layout.addWidget(separator)
        
        # 创建按钮容器
        button_container = QWidget()
        button_container.setStyleSheet("background-color: transparent; border: none;")
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(12)
        
        # AI朗读切换按钮
        self.tts_button = QPushButton(" 🔊 AI朗读 ")
        self.tts_button.clicked.connect(self.toggle_tts)
        self.tts_button.setCheckable(True)
        self.tts_button.setToolTip("切换AI朗读功能")
        self.tts_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #424242;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 16px;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #bababa;
            }
            QPushButton:checked {
                background-color: #007AFF;
                color: white;
                border-color: #0062cc;
            }
        """)
        button_layout.addWidget(self.tts_button)
        
        # 用户语音输入切换按钮
        self.voice_input_button = QPushButton(" 🎤 语音输入 ")
        self.voice_input_button.clicked.connect(self.toggle_voice_input)
        self.voice_input_button.setCheckable(True)
        self.voice_input_button.setToolTip("切换语音输入功能")
        self.voice_input_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #424242;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 16px;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #bababa;
            }
            QPushButton:checked {
                background-color: #28a745;
                color: white;
                border-color: #1f8838;
            }
        """)
        button_layout.addWidget(self.voice_input_button)
        
        # 清空聊天记录按钮
        self.clear_button = QPushButton(" 🗑️ 清空聊天 ")
        self.clear_button.clicked.connect(self.clear_chat)
        self.clear_button.setToolTip("清空聊天记录")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #424242;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 16px;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #bababa;
            }
            QPushButton:pressed {
                background-color: #dc3545;
                color: white;
                border-color: #bd2130;
            }
        """)
        button_layout.addWidget(self.clear_button)
        
        control_panel_layout.addWidget(button_container, 2)
        input_layout.addWidget(control_panel)
        
        # 输入框和发送按钮区域
        input_row = QHBoxLayout()
        input_row.setSpacing(16)
        input_row.setContentsMargins(0, 0, 0, 0)
        
        # 输入框
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(120)
        self.input_text.setMinimumHeight(60)
        self.input_text.setPlaceholderText("输入您的问题或命令...")
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #e5e5e5;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                color: #2c3e50;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border: 1px solid #007AFF;
            }
            /* 自定义输入框滚动条 */
            QScrollBar:vertical {
                background: transparent;
                width: 12px;
                margin: 2px 2px 2px 2px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(160, 160, 160, 0.4);
                min-height: 25px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(160, 160, 160, 0.7);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        input_row.addWidget(self.input_text, 1)
        
        # 发送按钮
        send_btn_container = QWidget()
        send_btn_container.setFixedSize(120, 60)
        send_btn_container.setStyleSheet("background-color: transparent; border: none;")
        send_btn_layout = QVBoxLayout(send_btn_container)
        send_btn_layout.setContentsMargins(0, 0, 0, 0)
        
        self.send_button = QPushButton(" 发 送 ")
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        send_btn_layout.addWidget(self.send_button)
        
        input_row.addWidget(send_btn_container, 0)
        
        input_layout.addLayout(input_row)
    
    def create_status_display_container(self):
        """创建状态显示容器 - 极简设计"""
        status_container = QWidget()
        status_container.setStyleSheet("background-color: transparent; border: none;")
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(16)
        
        # AI朗读状态指示器 - 极简设计
        tts_status_widget = QWidget()
        tts_status_widget.setStyleSheet("background-color: transparent;")
        tts_status_layout = QHBoxLayout(tts_status_widget)
        tts_status_layout.setContentsMargins(8, 0, 8, 0)
        tts_status_layout.setSpacing(6)
        
        tts_icon = QLabel("🔊")
        tts_icon.setStyleSheet("font-size: 16px;")
        tts_status_layout.addWidget(tts_icon)
        
        tts_label = QLabel("AI朗读")
        tts_label.setStyleSheet("font-size: 13px; color: #424242; font-weight: 500;")
        tts_status_layout.addWidget(tts_label)
        
        self.tts_status = QLabel("已关闭")
        self.tts_status.setStyleSheet("font-size: 13px; color: #dc3545; font-weight: 500;")
        tts_status_layout.addWidget(self.tts_status)
        
        status_layout.addWidget(tts_status_widget)
        
        # 语音输入状态指示器 - 极简设计
        voice_status_widget = QWidget()
        voice_status_widget.setStyleSheet("background-color: transparent;")
        voice_status_layout = QHBoxLayout(voice_status_widget)
        voice_status_layout.setContentsMargins(8, 0, 8, 0)
        voice_status_layout.setSpacing(6)
        
        voice_icon = QLabel("🎤")
        voice_icon.setStyleSheet("font-size: 16px;")
        voice_status_layout.addWidget(voice_icon)
        
        voice_label = QLabel("语音输入")
        voice_label.setStyleSheet("font-size: 13px; color: #424242; font-weight: 500;")
        voice_status_layout.addWidget(voice_label)
        
        self.voice_input_status = QLabel("已关闭")
        self.voice_input_status.setStyleSheet("font-size: 13px; color: #dc3545; font-weight: 500;")
        voice_status_layout.addWidget(self.voice_input_status)
        
        status_layout.addWidget(voice_status_widget)
        
        # 智能架构状态指示器 - 新增
        arch_status_widget = QWidget()
        arch_status_widget.setStyleSheet("background-color: transparent;")
        arch_status_layout = QHBoxLayout(arch_status_widget)
        arch_status_layout.setContentsMargins(8, 0, 8, 0)
        arch_status_layout.setSpacing(6)
        
        arch_icon = QLabel("🧠")
        arch_icon.setStyleSheet("font-size: 16px;")
        arch_status_layout.addWidget(arch_icon)
        
        arch_label = QLabel("思考模式")
        arch_label.setStyleSheet("font-size: 13px; color: #424242; font-weight: 500;")
        arch_status_layout.addWidget(arch_label)
        
        self.arch_status = QLabel("直接响应")
        self.arch_status.setStyleSheet("font-size: 13px; color: #007AFF; font-weight: 500;")
        arch_status_layout.addWidget(self.arch_status)
        
        status_layout.addWidget(arch_status_widget)
        
        # 任务复杂度指示器 - 新增
        complexity_status_widget = QWidget()
        complexity_status_widget.setStyleSheet("background-color: transparent;")
        complexity_status_layout = QHBoxLayout(complexity_status_widget)
        complexity_status_layout.setContentsMargins(8, 0, 8, 0)
        complexity_status_layout.setSpacing(6)
        
        complexity_icon = QLabel("📊")
        complexity_icon.setStyleSheet("font-size: 16px;")
        complexity_status_layout.addWidget(complexity_icon)
        
        complexity_label = QLabel("任务难度")
        complexity_label.setStyleSheet("font-size: 13px; color: #424242; font-weight: 500;")
        complexity_status_layout.addWidget(complexity_label)
        
        self.complexity_status = QLabel("简单")
        self.complexity_status.setStyleSheet("font-size: 13px; color: #28a745; font-weight: 500;")
        complexity_status_layout.addWidget(self.complexity_status)
        
        status_layout.addWidget(complexity_status_widget)
        
        status_layout.addStretch(1)
        
        return status_container
    
    def update_preset_commands(self):
        """更新预设命令列表"""
        self.preset_list.clear()
        for command in self.preset_commands:
            item = QListWidgetItem(command)
            self.preset_list.addItem(item)
    
    def on_preset_clicked(self, item):
        """处理预设命令点击"""
        command = item.text()
        self.input_text.setPlainText(command)
        self.send_message()
    
    def start_workers(self):
        """启动工作线程"""
        # 启动音频识别线程
        self.audio_worker = AudioWorker(self.recognizer)
        self.audio_worker.signals.result.connect(self.handle_recognized_text)
        self.audio_worker.signals.error.connect(self.handle_error)
        self.audio_worker.signals.status.connect(self.update_status)
        self.audio_worker.start()
        # 启动后立即禁用语音输入
        self.audio_worker.set_paused(True)
        if hasattr(self, 'voice_input_button'):
            self.voice_input_button.setChecked(False)
        if hasattr(self, 'voice_input_status'):
            self.voice_input_status.setText("已关闭")
            self.voice_input_status.setStyleSheet("font-size: 13px; color: #dc3545; font-weight: 500;")
        # 不主动更改主状态栏
        # self.update_status("语音输入已禁用")
        # 启动TTS线程
        self.tts_worker = TTSWorker()
        self.tts_worker.signals.finished.connect(self.on_tts_finished)
        self.tts_worker.signals.error.connect(self.handle_error)
    
    def handle_recognized_text(self, text):
        """处理语音识别的文本"""
        self.input_text.setPlainText(text)
        self.send_message()
    
    def handle_error(self, error_msg):
        """处理错误"""
        self.update_status(f"错误: {error_msg}")
        
        # 恢复发送按钮状态
        self.send_button.setText(" 发 送 ")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        
        # 关闭任何活动的指示器
        if hasattr(self, 'current_assistant_bubble') and self.current_assistant_bubble:
            self.current_assistant_bubble.stop_typing_indicator()
    
    def update_status(self, status):
        """更新状态"""
        self.status_indicator.setText(status)
    
    def send_message(self):
        """发送消息"""
        text = self.input_text.toPlainText().strip()
        if not text:
            return
        
        # 添加用户消息到聊天
        self.add_message("你", text)
        self.input_text.clear()
        
        # 设置发送按钮状态，而不是禁用它
        self.send_button.setText(" 发送中... ")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #a0a0a0;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #a0a0a0;
            }
        """)
        
        # 延迟100ms后启动流式处理，让UI能够更新
        QTimer.singleShot(100, lambda: self._process_message(text))
        
    def _process_message(self, text):
        """异步处理消息，避免阻塞UI"""
        # 更新状态
        self.update_status("正在处理...")
        
        # 在发送前评估任务复杂度
        if hasattr(self.assistant, '_evaluate_task_complexity'):
            try:
                self.current_complexity = self.assistant._evaluate_task_complexity(text)
                # 根据复杂度选择架构
                self.current_architecture = self.assistant._select_architecture(self.current_complexity)
                # 更新显示
                self.update_intelligence_indicators()
            except Exception as e:
                print(f"复杂度评估错误: {str(e)}")
        
        # 创建空的助手消息气泡（用于流式更新）
        self.current_assistant_bubble = self.add_message("助手", "", create_empty=True)
        
        # 启动打字指示器
        self.current_assistant_bubble.start_typing_indicator()
        
        # 如果存在上一个流式工作线程，停止它
        if hasattr(self, 'assistant_worker') and self.assistant_worker is not None:
            self.assistant_worker.stop()
            self.assistant_worker.wait(500)  # 等待最多500ms
        
        # 启动流式助手工作线程
        self.assistant_worker = StreamingAssistantWorker(self.assistant, text)
        self.assistant_worker.signals.stream_start.connect(self.on_stream_start)
        self.assistant_worker.signals.stream_chunk.connect(self.handle_stream_chunk)
        self.assistant_worker.signals.stream_end.connect(self.on_stream_end)
        self.assistant_worker.signals.result.connect(self.handle_assistant_response)
        self.assistant_worker.signals.error.connect(self.handle_error)
        self.assistant_worker.start()
    
    def on_stream_start(self):
        """流式输出开始时的处理"""
        # 可以在这里添加开始反馈，如显示思考指示器等
        self.update_status("AI正在回答...")
    
    def on_stream_end(self):
        """流式输出结束时的处理"""
        # 流式输出完成后的UI更新
        self.update_status("回答已完成")
        
        # 确保打字指示器被关闭
        if hasattr(self, 'current_assistant_bubble') and self.current_assistant_bubble:
            self.current_assistant_bubble.stop_typing_indicator()
        
        # 恢复发送按钮状态
        self.send_button.setText(" 发 送 ")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
    
    def handle_stream_chunk(self, chunk):
        """处理流式文本块"""
        if hasattr(self, 'current_assistant_bubble') and self.current_assistant_bubble:
            self.current_assistant_bubble.append_text(chunk)
            # 仅当用户当前在底部时才自动滚动
            scroll_bar = self.chat_area.verticalScrollBar()
            at_bottom = (scroll_bar.value() >= scroll_bar.maximum() - 20)
            if at_bottom:
                QTimer.singleShot(10, self.scroll_to_bottom)
    
    def handle_assistant_response(self, response):
        """处理助手响应"""
        # 流式显示已经完成，这里主要用于TTS等后续处理
        self.update_status("回答已完成")
        
        # 确保打字指示器被关闭
        if hasattr(self, 'current_assistant_bubble') and self.current_assistant_bubble:
            self.current_assistant_bubble.stop_typing_indicator()
        
        # 如果启用了TTS，播放响应
        if self.tts_button.isChecked():
            self.speak_response(response)
        
        # 清除当前助手气泡引用
        if hasattr(self, 'current_assistant_bubble'):
            self.current_assistant_bubble = None
    
    def add_message(self, sender, message, create_empty=False):
        """添加消息到聊天区域"""
        is_user = (sender == "你")
        current_time = datetime.now().strftime("%H:%M")
        
        # 创建聊天消息框
        bubble = ChatBubble(message, is_user)
        
        # 创建消息容器，全屏宽度
        container = QWidget()
        container.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        
        # 消息容器布局
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 创建标题栏
        header = QWidget()
        header.setFixedHeight(40)  # 固定标题栏高度
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 8, 24, 8)
        
        if is_user:
            # 用户消息标题
            header.setStyleSheet("background-color: #f0f8ff;")
            
            # 用户标签
            user_label = QLabel(sender)
            user_label.setStyleSheet("color: #2c3e50; font-size: 13px; font-weight: bold;")
            
            # 时间标签
            time_label = QLabel(current_time)
            time_label.setStyleSheet("color: #8e8e8e; font-size: 12px; margin-left: 8px;")
            
            # 添加到标题布局
            header_layout.addWidget(user_label)
            header_layout.addWidget(time_label)
            header_layout.addStretch()
        else:
            # 助手消息标题
            header.setStyleSheet("background-color: #f8fafc;")
            
            # 助手标签
            assistant_label = QLabel("AI助手")
            assistant_label.setStyleSheet("color: #28a745; font-size: 13px; font-weight: bold;")
            
            # 时间标签
            time_label = QLabel(current_time)
            time_label.setStyleSheet("color: #8e8e8e; font-size: 12px; margin-left: 8px;")
            
            # 添加到标题布局
            header_layout.addWidget(assistant_label)
            header_layout.addWidget(time_label)
            header_layout.addStretch()
        
        # 将标题栏和消息添加到容器
        container_layout.addWidget(header, 0)  # 0表示固定大小
        container_layout.addWidget(bubble, 1)  # 1表示可拉伸
        
        # 插入到布局中（在stretch之前）
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)
        
        # 允许布局更新并刷新显示
        QTimer.singleShot(10, bubble.adjustWidth)
        
        # 延时滚动到底部，确保消息完全渲染
        QTimer.singleShot(100, self.scroll_to_bottom)
        
        # 强制更新，确保实时显示
        QApplication.processEvents()
        
        # 如果是创建空的助手消息，返回气泡引用
        if create_empty:
            return bubble
        
        return None
    
    def scroll_to_bottom(self):
        """滚动到聊天区域底部"""
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )
    
    def toggle_tts(self):
        """切换TTS模式（AI朗读）"""
        if self.tts_button.isChecked():
            self.tts_status.setText("已启用")
            self.tts_status.setStyleSheet("font-size: 13px; color: #28a745; font-weight: 500;")
            self.update_status("AI朗读已启用")
        else:
            self.tts_status.setText("已关闭")
            self.tts_status.setStyleSheet("font-size: 13px; color: #dc3545; font-weight: 500;")
            self.update_status("AI朗读已禁用")
    
    def toggle_voice_input(self):
        """切换语音输入模式"""
        if self.voice_input_button.isChecked():
            self.voice_input_status.setText("已启用")
            self.voice_input_status.setStyleSheet("font-size: 13px; color: #28a745; font-weight: 500;")
            self.audio_worker.set_paused(False)  # 启用语音输入
            self.update_status("语音输入已启用")
        else:
            self.voice_input_status.setText("已关闭")
            self.voice_input_status.setStyleSheet("font-size: 13px; color: #dc3545; font-weight: 500;")
            self.audio_worker.set_paused(True)   # 禁用语音输入
            self.update_status("语音输入已禁用")
    
    def speak_response(self, text):
        """语音播放响应"""
        if not self.tts_button.isChecked():
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
        self.audio_worker.set_speaking(True)  # 防止AI说话时录音
        
        # 强制暂停一小段时间，让麦克风完全释放
        time.sleep(0.5)
        
        # 如果语音输入已启用，显示状态提醒
        if self.voice_input_button.isChecked():
            self.update_status("AI朗读中，语音输入已禁用...")
        else:
            self.update_status("AI朗读中...")
            
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
        self.audio_worker.set_speaking(False)
        
        # 根据当前状态更新显示
        if self.voice_input_button.isChecked():
            self.update_status("语音输入已启用")
        else:
            self.update_status("语音输入已禁用")
    
    def clear_chat(self):
        """清空聊天记录"""
        # 清除当前助手气泡引用
        if hasattr(self, 'current_assistant_bubble'):
            self.current_assistant_bubble = None
        
        # 清除所有聊天消息，保留stretch
        while self.chat_layout.count() > 1:
            child = self.chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 添加欢迎消息
        self.add_message("助手", self.WELCOME_MESSAGE)
    
    def closeEvent(self, event):
        """关闭事件"""
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

    def update_intelligence_indicators(self):
        """更新智能指标显示"""
        try:
            # 获取当前架构信息
            if hasattr(self.assistant, 'user_context'):
                # 获取最后一次处理的任务架构和复杂度
                strategies = self.assistant.user_context.get("successful_strategies", {})
                if strategies:
                    # 更新架构状态
                    arch_name_map = {
                        ArchitectureType.DIRECT: "直接响应",
                        ArchitectureType.BASIC_COT: "基础思考链",
                        ArchitectureType.FULL_COT: "完整思考链", 
                        ArchitectureType.REACT: "ReAct模式",
                        ArchitectureType.PLANNER: "规划架构"
                    }
                    
                    complexity_name_map = {
                        TaskComplexity.SIMPLE: "简单",
                        TaskComplexity.MEDIUM: "中等",
                        TaskComplexity.COMPLEX: "复杂",
                        TaskComplexity.ADVANCED: "高级"
                    }
                    
                    # 设置架构名称和颜色
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
                    
                    # 更新架构状态显示
                    if hasattr(self, 'current_architecture'):
                        arch_name = arch_name_map.get(self.current_architecture, "直接响应")
                        arch_color = arch_colors.get(self.current_architecture, "#007AFF")
                        self.arch_status.setText(arch_name)
                        self.arch_status.setStyleSheet(f"font-size: 13px; color: {arch_color}; font-weight: 500;")
                    
                    # 更新复杂度状态显示
                    if hasattr(self, 'current_complexity'):
                        complexity_name = complexity_name_map.get(self.current_complexity, "简单")
                        complexity_color = complexity_colors.get(self.current_complexity, "#28a745")
                        self.complexity_status.setText(complexity_name)
                        self.complexity_status.setStyleSheet(f"font-size: 13px; color: {complexity_color}; font-weight: 500;")
        except Exception as e:
            print(f"更新智能指标错误: {str(e)}")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MacOSAssistantUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 