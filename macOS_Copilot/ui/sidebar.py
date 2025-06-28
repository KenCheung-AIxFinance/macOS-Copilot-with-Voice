from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal

class Sidebar(QWidget):
    """侧边栏组件"""
    
    # 定义信号
    page_changed = pyqtSignal(str)  # 页面切换信号：'chat' 或 'kb'
    preset_command_clicked = pyqtSignal(str)  # 预设命令点击信号
    
    def __init__(self, preset_commands=None, parent=None):
        super().__init__(parent)
        self.preset_commands = preset_commands or [
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
        self.current_page = "chat"  # 默认显示聊天页面
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setFixedWidth(300)
        self.setStyleSheet("""
            QWidget#sidebar {
                background-color: #f8f9fa;
                border-right: 1px solid #e5e5e5;
            }
        """)
        self.setObjectName("sidebar")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 创建导航栏
        nav_bar = self._create_nav_bar()
        layout.addWidget(nav_bar)
        
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
        layout.addWidget(title_label)
        
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
        layout.addWidget(preset_label)
        
        # 预设命令列表
        self.preset_list = self._create_preset_list()
        layout.addWidget(self.preset_list)
        
        # 状态指示器
        self.status_indicator = QLabel("🟢 系统正常")
        self.status_indicator.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #6c757d;
                padding: 8px 0;
            }
        """)
        layout.addWidget(self.status_indicator)
        
        layout.addStretch()
        
    def _create_nav_bar(self):
        """创建导航栏"""
        nav_bar = QWidget()
        nav_bar.setObjectName("nav_bar")
        nav_bar.setStyleSheet("QWidget#nav_bar { background-color: transparent; }")
        
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
        self.chat_nav_btn.clicked.connect(self._switch_to_chat)
        self.kb_nav_btn.clicked.connect(self._switch_to_kb)
        
        nav_bar_layout.addWidget(self.chat_nav_btn)
        nav_bar_layout.addWidget(self.kb_nav_btn)
        nav_bar_layout.addStretch(1)
        
        return nav_bar
    
    def _create_preset_list(self):
        """创建预设命令列表"""
        preset_list = QListWidget()
        preset_list.setObjectName("preset_list")
        preset_list.setStyleSheet("""
            QListWidget#preset_list {
                background-color: white;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                padding: 4px;
                font-size: 13px;
                color: #2c3e50;
            }
            QListWidget#preset_list::item {
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget#preset_list::item:hover {
                background-color: #f8f9fa;
            }
            QListWidget#preset_list::item:selected {
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
        
        # 添加预设命令
        for command in self.preset_commands:
            item = QListWidgetItem(command)
            preset_list.addItem(item)
        
        # 连接点击事件
        preset_list.itemClicked.connect(self._on_preset_clicked)
        
        return preset_list
    
    def _switch_to_chat(self):
        """切换到聊天页面"""
        self.chat_nav_btn.setChecked(True)
        self.kb_nav_btn.setChecked(False)
        self.current_page = "chat"
        self.page_changed.emit("chat")
    
    def _switch_to_kb(self):
        """切换到知识库页面"""
        self.chat_nav_btn.setChecked(False)
        self.kb_nav_btn.setChecked(True)
        self.current_page = "kb"
        self.page_changed.emit("kb")
    
    def _on_preset_clicked(self, item):
        """处理预设命令点击"""
        command = item.text()
        self.preset_command_clicked.emit(command)
    
    def update_preset_commands(self, commands):
        """更新预设命令列表"""
        self.preset_commands = commands
        self.preset_list.clear()
        for command in self.preset_commands:
            item = QListWidgetItem(command)
            self.preset_list.addItem(item)
    
    def update_status(self, status_text):
        """更新状态指示器文本"""
        self.status_indicator.setText(status_text) 