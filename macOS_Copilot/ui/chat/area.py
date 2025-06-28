from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QHBoxLayout,
                           QLabel, QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, QTimer

from macOS_Copilot.ui.chat.bubble import ChatBubble

class ChatArea(QWidget):
    """聊天区域组件，管理聊天消息的显示与布局"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_assistant_bubble = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)
        
        # 聊天显示区域
        self.scroll_area = self._create_scroll_area()
        
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
        self.scroll_area.setWidget(self.chat_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 添加滚动区域到主布局
        layout.addWidget(self.scroll_area)
    
    def _create_scroll_area(self):
        """创建滚动区域"""
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("""
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
        
        return scroll_area
        
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
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
        
    def clear_chat(self):
        """清空聊天记录"""
        # 清除当前助手气泡引用
        if hasattr(self, 'current_assistant_bubble') and self.current_assistant_bubble:
            self.current_assistant_bubble = None
        
        # 清除所有聊天消息，保留stretch
        while self.chat_layout.count() > 1:
            child = self.chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater() 