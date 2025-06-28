from PyQt6.QtWidgets import (QWidget, QTabWidget, QVBoxLayout)
from PyQt6.QtCore import pyqtSignal
from macOS_Copilot.ui.knowledge.search import KnowledgeSearchPage
from macOS_Copilot.ui.knowledge.manage import KnowledgeManagePage
from macOS_Copilot.models.knowledge import KnowledgeBase

class KnowledgeBasePage(QWidget):
    """知识库页面容器，包含标签页"""
    
    # 定义信号
    query_to_assistant = pyqtSignal(str)  # 将查询发送到助手的信号
    
    def __init__(self, knowledge_base=None, parent=None):
        super().__init__(parent)
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #e5e5e5; 
                border-radius: 8px; 
            }
            QTabBar::tab {
                background: #f8f9fa;
                color: #1976d2;
                border: 1px solid #e5e5e5;
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                min-width: 120px;
                min-height: 36px;
                font-size: 15px;
                font-weight: 600;
                margin-right: 4px;
                padding: 8px 18px;
            }
            QTabBar::tab:selected {
                background: #1976d2;
                color: white;
            }
        """)
        
        # 创建搜索/问答页面
        self.search_page = KnowledgeSearchPage(self.knowledge_base)
        # 连接搜索页面的查询信号
        self.search_page.query_to_assistant.connect(self.on_query_to_assistant)
        
        # 创建管理页面
        self.manage_page = KnowledgeManagePage(self.knowledge_base)
        self.manage_page.knowledge_updated.connect(self._on_knowledge_updated)
        
        # 添加标签页
        self.tab_widget.addTab(self.search_page, "🔍 检索/问答")
        self.tab_widget.addTab(self.manage_page, "📚 管理")
        
        # 设置默认标签页
        self.tab_widget.setCurrentIndex(0)
        
        # 添加标签页到布局
        layout.addWidget(self.tab_widget)
    
    def _on_knowledge_updated(self):
        """知识库更新处理"""
        # 通知搜索页面更新知识库
        self.search_page.update_knowledge_base(self.knowledge_base)
    
    def on_query_to_assistant(self, query):
        """处理从搜索页面发送到助手的查询"""
        # 转发信号
        self.query_to_assistant.emit(query)
    
    def set_knowledge_base(self, knowledge_base):
        """设置知识库"""
        self.knowledge_base = knowledge_base
        self.search_page.update_knowledge_base(knowledge_base)
        self.manage_page.update_knowledge_base(knowledge_base) 