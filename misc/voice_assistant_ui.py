import sys
import threading
import queue
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QPushButton, QLabel, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QPalette, QColor
import speech_recognition as sr
import edge_tts
import asyncio
from openai import OpenAI
import os
import tempfile
from langdetect import detect, DetectorFactory
import re

class WorkerSignals(QObject):
    """定义工作线程的信号"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(str)
    status = pyqtSignal(str)

class AudioWorker(QThread):
    """处理音频识别的工作线程"""
    def __init__(self, recognizer):
        super().__init__()
        self.recognizer = recognizer
        self.signals = WorkerSignals()
        self.is_running = True
        self.is_speaking = False

    def set_speaking(self, speaking):
        """设置说话状态"""
        self.is_speaking = speaking

    def run(self):
        while self.is_running:
            if not self.is_speaking:  # 只在非说话状态时进行识别
                try:
                    with sr.Microphone() as source:
                        self.signals.status.emit("正在聆听...")
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        self.signals.status.emit("正在处理...")
                        text = self.recognizer.recognize_google(audio, language='zh-CN')
                        self.signals.result.emit(text)
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    self.signals.error.emit(str(e))
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
            communicate = edge_tts.Communicate(self.text, self.voice)
            asyncio.run(communicate.save("temp.mp3"))
            os.system("afplay temp.mp3")
            os.remove("temp.mp3")
            self.signals.status.emit("正在聆听...")
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()

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
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {'#3498db' if is_user else '#2ecc71'};
                border-radius: 15px;
                padding: 10px 15px;
                margin: 5px;
                color: white;
                font-size: 14px;
            }}
        """)
        self.setMaximumWidth(400)
        self.setWordWrap(True)
        
        layout = QVBoxLayout(self)
        label = QLabel(text)
        label.setStyleSheet("color: white;")
        label.setWordWrap(True)
        layout.addWidget(label)

class VoiceAssistantUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('智能语音助手')
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QTextEdit {
                background-color: white;
                border: 2px solid #dcdde1;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # 初始化语音识别
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 1.0
        self.recognizer.phrase_threshold = 0.5
        self.recognizer.non_speaking_duration = 0.8
        
        # 初始化AI客户端
        self.client = OpenAI(api_key="sk-1b53c98a3b8c4abcaa1f68540ab3252d", 
                           base_url="https://api.deepseek.com")
        self.messages = []
        
        # 设置系统提示
        system_prompt = """你是一个友好的语音助手。请：
1. 用简洁自然的语言回应
2. 自动适应用户的语言
3. 保持对话连贯性
4. 保持友好态度
5. 禁用任何emoji 和 markdown 格式
"""
        self.messages.append({"role": "system", "content": system_prompt})
        
        # 创建UI
        self.init_ui()
        
        # 对话状态
        self.is_speaking = False
        
        # 启动工作线程
        self.start_workers()
        
    def init_ui(self):
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建状态标签
        self.status_label = QLabel("正在聆听...")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #2c3e50;
                padding: 12px 20px;
                background-color: #ecf0f1;
                border-radius: 8px;
                border: 2px solid #bdc3c7;
            }
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumHeight(50)
        layout.addWidget(self.status_label)
        
        # 创建实时文字显示区域
        self.realtime_text = QTextEdit()
        self.realtime_text.setReadOnly(True)
        self.realtime_text.setMaximumHeight(200)
        self.realtime_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                color: #495057;
            }
        """)
        self.realtime_text.setPlaceholderText("对话内容将实时显示在这里...")
        layout.addWidget(self.realtime_text)
        
        # 创建聊天记录区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # 创建控制按钮
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.clear_button = QPushButton('清除记录')
        self.clear_button.clicked.connect(self.clear_chat)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
        
        # 添加欢迎消息
        self.add_message("助手", "你好！我是你的智能语音助手，请开始说话...")
        self.update_realtime_text("助手", "你好！我是你的智能语音助手，请开始说话...")
        
    def start_workers(self):
        """启动所有工作线程"""
        # 启动语音识别线程
        self.audio_worker = AudioWorker(self.recognizer)
        self.audio_worker.signals.result.connect(self.handle_recognized_text)
        self.audio_worker.signals.error.connect(self.handle_error)
        self.audio_worker.signals.status.connect(self.update_status)
        self.audio_worker.start()
        
        # 创建语音合成线程
        self.tts_worker = TTSWorker()
        self.tts_worker.signals.finished.connect(self.on_tts_finished)
        self.tts_worker.signals.error.connect(self.handle_error)
        self.tts_worker.signals.status.connect(self.update_status)

    def handle_recognized_text(self, text):
        """处理识别到的文字"""
        if not self.is_speaking:
            # 立即更新UI
            QApplication.processEvents()
            self.update_realtime_text("用户", text)
            self.add_message("用户", text)
            # 立即处理AI响应
            self.process_ai_response(text)
        
    def handle_error(self, error_msg):
        """处理错误"""
        self.add_message("系统", f"发生错误: {error_msg}")
        
    def update_status(self, status):
        """更新状态标签"""
        self.status_label.setText(status)
        
    def process_ai_response(self, text):
        """处理AI响应"""
        try:
            self.messages.append({"role": "user", "content": text})
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=self.messages
            )
            ai_response = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": ai_response})
            
            # 立即更新UI
            QApplication.processEvents()
            self.add_message("助手", ai_response)
            self.update_realtime_text("助手", ai_response)
            
            # 开始语音合成
            self.speak_response(ai_response)
        except Exception as e:
            error_msg = f"AI处理错误: {str(e)}"
            self.add_message("系统", error_msg)
            self.update_realtime_text("系统", error_msg)
            
    def add_message(self, sender, message):
        """添加消息到聊天显示"""
        if sender == "用户":
            self.chat_display.append(f'<div style="text-align: right;"><span style="background-color: #3498db; color: white; padding: 8px 15px; border-radius: 15px; display: inline-block; max-width: 70%;">{message}</span></div>')
        else:
            self.chat_display.append(f'<div style="text-align: left;"><span style="background-color: #2ecc71; color: white; padding: 8px 15px; border-radius: 15px; display: inline-block; max-width: 70%;">{message}</span></div>')
        # 立即滚动到底部
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
        # 强制更新UI
        QApplication.processEvents()
        
    def clear_chat(self):
        """清除聊天记录"""
        self.chat_display.clear()
        self.realtime_text.clear()
        self.messages = [self.messages[0]]  # 保留系统提示
        self.add_message("助手", "对话已重置，请继续...")
        self.update_realtime_text("助手", "对话已重置，请继续...")
        
    def speak_response(self, text):
        """语音合成并播放"""
        try:
            self.is_speaking = True
            self.audio_worker.set_speaking(True)
            self.update_status("正在说话...")
            self.tts_worker.set_text(text)
            self.tts_worker.start()
        except Exception as e:
            self.handle_error(str(e))

    def on_tts_finished(self):
        """语音合成完成后的处理"""
        self.is_speaking = False
        self.audio_worker.set_speaking(False)
        self.update_status("正在聆听...")

    def closeEvent(self, event):
        """关闭窗口时的处理"""
        self.audio_worker.stop()
        self.audio_worker.wait()
        self.tts_worker.wait()
        event.accept()

    def update_realtime_text(self, sender, message):
        """更新实时文字显示"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        if sender == "用户":
            self.realtime_text.append(f'<div style="text-align: right; margin: 5px 0;"><span style="color: #666;">{timestamp}</span><br><span style="background-color: #3498db; color: white; padding: 5px 10px; border-radius: 10px; display: inline-block;">{message}</span></div>')
        else:
            self.realtime_text.append(f'<div style="text-align: left; margin: 5px 0;"><span style="color: #666;">{timestamp}</span><br><span style="background-color: #2ecc71; color: white; padding: 5px 10px; border-radius: 10px; display: inline-block;">{message}</span></div>')
        # 立即滚动到底部
        self.realtime_text.verticalScrollBar().setValue(
            self.realtime_text.verticalScrollBar().maximum()
        )
        # 强制更新UI
        QApplication.processEvents()

def main():
    app = QApplication(sys.argv)
    window = VoiceAssistantUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 