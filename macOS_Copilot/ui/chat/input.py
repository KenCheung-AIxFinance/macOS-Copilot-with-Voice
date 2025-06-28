from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                            QPushButton, QLabel, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal


class InputArea(QWidget):
    """聊天输入区域组件"""
    
    # 定义信号
    message_sent = pyqtSignal(str)  # 消息发送信号
    tts_toggled = pyqtSignal(bool)  # TTS开关信号
    voice_input_toggled = pyqtSignal(bool)  # 语音输入开关信号
    clear_chat_requested = pyqtSignal()  # 清空聊天请求信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 状态
        self.is_tts_enabled = False
        self.is_voice_input_enabled = False
        
        # 架构和复杂度显示
        self.current_architecture = "直接响应"
        self.current_complexity = "简单"
        self.arch_color = "#007AFF"
        self.complexity_color = "#28a745"
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 16, 32, 24)
        layout.setSpacing(16)
        
        # 创建控制面板
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # 输入框和发送按钮区域
        input_row = QHBoxLayout()
        input_row.setSpacing(16)
        input_row.setContentsMargins(0, 0, 0, 0)
        
        # 创建输入框
        self.input_text = self._create_input_textbox()
        input_row.addWidget(self.input_text, 1)
        
        # 创建发送按钮
        send_btn_container = self._create_send_button_container()
        input_row.addWidget(send_btn_container, 0)
        
        layout.addLayout(input_row)
        
        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-top: 1px solid #e5e5e5;
            }
        """)
    
    def _create_control_panel(self):
        """创建控制面板"""
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
        status_container = self._create_status_display_container()
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
        button_container = self._create_button_container()
        control_panel_layout.addWidget(button_container, 2)
        
        return control_panel
    
    def _create_status_display_container(self):
        """创建状态显示容器"""
        status_container = QWidget()
        status_container.setStyleSheet("background-color: transparent; border: none;")
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(16)
        
        # TTS状态指示器
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
        
        # 语音输入状态指示器
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
        
        # 智能架构状态指示器
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
        
        self.arch_status = QLabel(self.current_architecture)
        self.arch_status.setStyleSheet(f"font-size: 13px; color: {self.arch_color}; font-weight: 500;")
        arch_status_layout.addWidget(self.arch_status)
        
        status_layout.addWidget(arch_status_widget)
        
        # 任务复杂度指示器
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
        
        self.complexity_status = QLabel(self.current_complexity)
        self.complexity_status.setStyleSheet(f"font-size: 13px; color: {self.complexity_color}; font-weight: 500;")
        complexity_status_layout.addWidget(self.complexity_status)
        
        status_layout.addWidget(complexity_status_widget)
        
        status_layout.addStretch(1)
        
        return status_container
    
    def _create_button_container(self):
        """创建按钮容器"""
        button_container = QWidget()
        button_container.setStyleSheet("background-color: transparent; border: none;")
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(12)
        
        # AI朗读切换按钮
        self.tts_button = QPushButton(" 🔊 AI朗读 ")
        self.tts_button.clicked.connect(self._on_tts_toggled)
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
        self.voice_input_button.clicked.connect(self._on_voice_input_toggled)
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
        self.clear_button.clicked.connect(self._on_clear_chat_clicked)
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
        
        return button_container
    
    def _create_input_textbox(self):
        """创建输入框"""
        input_text = QTextEdit()
        input_text.setMaximumHeight(120)
        input_text.setMinimumHeight(60)
        input_text.setPlaceholderText("输入您的问题或命令...")
        input_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #e5e5e5;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                color: #000000;
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
        
        # 设置文本交互标志，确保可以输入和选择文本
        input_text.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextEditorInteraction
        )
        
        # 设置快捷键处理器
        input_text.keyPressEvent = lambda event: self._handle_input_keypress(event)
        
        return input_text
    
    def _handle_input_keypress(self, event):
        """处理输入框快捷键"""
        # Ctrl+Enter 或 Command+Enter 发送消息
        if (event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter) and \
           (event.modifiers() == Qt.KeyboardModifier.ControlModifier or 
            event.modifiers() == Qt.KeyboardModifier.MetaModifier):
            self.send_message()
            return
        
        # 继承原始QTextEdit的keyPressEvent
        QTextEdit.keyPressEvent(self.input_text, event)
    
    def _create_send_button_container(self):
        """创建发送按钮容器"""
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
        
        return send_btn_container
    
    def _on_tts_toggled(self):
        """处理TTS开关切换"""
        self.is_tts_enabled = self.tts_button.isChecked()
        
        # 更新状态显示
        if self.is_tts_enabled:
            self.tts_status.setText("已启用")
            self.tts_status.setStyleSheet("font-size: 13px; color: #28a745; font-weight: 500;")
        else:
            self.tts_status.setText("已关闭")
            self.tts_status.setStyleSheet("font-size: 13px; color: #dc3545; font-weight: 500;")
        
        # 发送信号
        self.tts_toggled.emit(self.is_tts_enabled)
    
    def _on_voice_input_toggled(self):
        """处理语音输入开关切换"""
        self.is_voice_input_enabled = self.voice_input_button.isChecked()
        
        # 更新状态显示
        if self.is_voice_input_enabled:
            self.voice_input_status.setText("已启用")
            self.voice_input_status.setStyleSheet("font-size: 13px; color: #28a745; font-weight: 500;")
        else:
            self.voice_input_status.setText("已关闭")
            self.voice_input_status.setStyleSheet("font-size: 13px; color: #dc3545; font-weight: 500;")
        
        # 发送信号
        self.voice_input_toggled.emit(self.is_voice_input_enabled)
    
    def _on_clear_chat_clicked(self):
        """处理清空聊天按钮点击"""
        self.clear_chat_requested.emit()
    
    def send_message(self):
        """发送消息"""
        text = self.input_text.toPlainText().strip()
        if not text:
            return
        
        # 发送消息信号
        self.message_sent.emit(text)
        
        # 清空输入框
        self.input_text.clear()
        
        # 设置发送按钮状态
        self._set_sending_state(True)
    
    def _set_sending_state(self, is_sending):
        """设置发送状态"""
        if is_sending:
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
        else:
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
    
    def reset_sending_state(self):
        """重置发送状态"""
        self._set_sending_state(False)
    
    def update_intelligence_indicators(self, architecture, complexity, arch_color="#007AFF", complexity_color="#28a745"):
        """更新智能指标显示"""
        self.current_architecture = architecture
        self.current_complexity = complexity
        self.arch_color = arch_color
        self.complexity_color = complexity_color
        
        # 更新显示
        self.arch_status.setText(architecture)
        self.arch_status.setStyleSheet(f"font-size: 13px; color: {arch_color}; font-weight: 500;")
        
        self.complexity_status.setText(complexity)
        self.complexity_status.setStyleSheet(f"font-size: 13px; color: {complexity_color}; font-weight: 500;") 