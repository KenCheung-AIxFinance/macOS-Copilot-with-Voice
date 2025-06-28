from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                            QPushButton, QTextEdit, QLabel, QScrollArea,
                            QFrame, QSplitter, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import markdown

class KnowledgeSearchPage(QWidget):
    """知识库搜索/问答页面"""
    
    # 定义信号
    query_to_assistant = pyqtSignal(str)  # 将查询发送到助手的信号
    
    def __init__(self, knowledge_base, parent=None):
        super().__init__(parent)
        self.knowledge_base = knowledge_base
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)
        
        # 标题
        title = QLabel("🔍 知识库检索")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1976d2; margin-bottom: 12px;")
        layout.addWidget(title)
        
        # 搜索/提问输入行
        ask_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("请输入检索内容或提问...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                font-size: 14px; 
                border-radius: 8px; 
                padding: 8px 12px; 
                border: 1px solid #e5e5e5; 
                color: #222;
            }
            QLineEdit:focus {
                border: 1px solid #1976d2;
            }
        """)
        self.search_input.returnPressed.connect(self.search_knowledge)
        
        search_btn = QPushButton("🔍 检索")
        search_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; 
                padding: 8px 18px; 
                border-radius: 8px; 
                background: #1976d2; 
                color: white; 
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1565c0;
            }
        """)
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.clicked.connect(self.search_knowledge)
        
        ask_assistant_btn = QPushButton("💬 问助手")
        ask_assistant_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; 
                padding: 8px 18px; 
                border-radius: 8px; 
                background: #4caf50; 
                color: white; 
                font-weight: 600;
            }
            QPushButton:hover {
                background: #388e3c;
            }
        """)
        ask_assistant_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ask_assistant_btn.clicked.connect(self.ask_assistant)
        
        ask_row.addWidget(self.search_input, 1)
        ask_row.addWidget(search_btn, 0)
        ask_row.addWidget(ask_assistant_btn, 0)
        layout.addLayout(ask_row)
        
        # 创建分割器，上面是搜索结果列表，下面是详情
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e0e0e0;
            }
        """)
        
        # 搜索结果列表
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                color: #2c3e50;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #e5e5e5;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
        self.results_list.itemClicked.connect(self.show_item_detail)
        
        # 结果详情区域
        self.detail_area = QTextEdit()
        self.detail_area.setReadOnly(True)
        self.detail_area.setStyleSheet("""
            QTextEdit {
                font-size: 15px; 
                color: #333; 
                background: #fff; 
                border-radius: 8px; 
                padding: 16px;
                border: 1px solid #e5e5e5;
            }
        """)
        
        # 添加到分割器
        splitter.addWidget(self.results_list)
        splitter.addWidget(self.detail_area)
        
        # 设置初始大小比例
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter, 1)
        
        # 添加提示文本
        tip_label = QLabel("提示: 您可以直接检索知识库，或将问题发送给助手进行回答")
        tip_label.setStyleSheet("color: #757575; font-size: 12px;")
        layout.addWidget(tip_label, 0, Qt.AlignmentFlag.AlignRight)
    
    def search_knowledge(self):
        """搜索知识库"""
        query = self.search_input.text().strip()
        if not query:
            self.detail_area.setHtml("<p style='color:#dc3545'>请输入您的问题或检索内容。</p>")
            return
        
        # 使用语义搜索获取结果
        results = self.knowledge_base.semantic_search(query)
        
        # 清空结果列表
        self.results_list.clear()
        
        if not results:
            self.detail_area.setHtml("<p style='color:#dc3545'>未找到相关知识。</p>")
            return
            
        # 显示结果列表
        for item in results:
            list_item = QListWidgetItem(item.title)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.results_list.addItem(list_item)
        
        # 自动选择第一个结果
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
            self.show_item_detail(self.results_list.item(0))
    
    def show_item_detail(self, list_item):
        """显示知识条目详情"""
        item = list_item.data(Qt.ItemDataRole.UserRole)
        if not item:
            return
            
        # 使用Markdown渲染内容
        try:
            html_content = markdown.markdown(item.content)
            
            # 构建完整的HTML
            full_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
                    h1, h2, h3, h4, h5, h6 {{ color: #1976d2; }}
                    code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 4px; }}
                    pre {{ background-color: #f5f5f5; padding: 12px; border-radius: 8px; overflow-x: auto; }}
                    blockquote {{ border-left: 4px solid #1976d2; margin-left: 0; padding-left: 16px; color: #555; }}
                </style>
            </head>
            <body>
                <h2>{item.title}</h2>
                {html_content}
            </body>
            </html>
            """
            
            self.detail_area.setHtml(full_html)
        except Exception as e:
            print(f"渲染Markdown失败: {e}")
            self.detail_area.setPlainText(f"{item.title}\n\n{item.content}")
    
    def ask_assistant(self):
        """将查询发送给助手"""
        query = self.search_input.text().strip()
        if not query:
            self.detail_area.setHtml("<p style='color:#dc3545'>请输入您的问题。</p>")
            return
            
        # 发送信号
        self.query_to_assistant.emit(query)
    
    def update_knowledge_base(self, knowledge_base):
        """更新知识库引用"""
        self.knowledge_base = knowledge_base
        self.results_list.clear()
        self.detail_area.clear() 