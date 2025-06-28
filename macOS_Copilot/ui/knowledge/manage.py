from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                            QPushButton, QTextEdit, QLabel, QListWidget,
                            QListWidgetItem, QDialog, QMessageBox, QMenu,
                            QSplitter, QFrame, QToolButton, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
import os
import time
import markdown

class KnowledgeManagePage(QWidget):
    """知识库管理页面"""
    
    # 定义信号
    knowledge_updated = pyqtSignal()  # 知识库更新信号
    
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
        title = QLabel("📚 知识库管理")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1976d2; margin-bottom: 12px;")
        layout.addWidget(title)
        
        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        # 添加知识按钮
        add_btn = QPushButton("➕ 添加知识")
        add_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; 
                padding: 6px 18px; 
                border-radius: 8px; 
                background: #e3f2fd; 
                color: #1976d2; 
                font-weight: 600;
            }
            QPushButton:hover {
                background: #bbdefb;
            }
        """)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.show_add_dialog)
        toolbar.addWidget(add_btn)
        
        # 导入/导出按钮
        import_btn = QPushButton("📥 导入")
        import_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; 
                padding: 6px 18px; 
                border-radius: 8px; 
                background: #f5f5f5; 
                color: #555; 
                font-weight: 600;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self.import_knowledge)
        toolbar.addWidget(import_btn)
        
        export_btn = QPushButton("📤 导出")
        export_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; 
                padding: 6px 18px; 
                border-radius: 8px; 
                background: #f5f5f5; 
                color: #555; 
                font-weight: 600;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self.export_knowledge)
        toolbar.addWidget(export_btn)
        
        # 添加搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索知识条目...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                font-size: 14px; 
                border-radius: 8px; 
                padding: 6px 12px; 
                border: 1px solid #e5e5e5; 
                color: #222;
            }
            QLineEdit:focus {
                border: 1px solid #1976d2;
            }
        """)
        self.search_input.textChanged.connect(self.filter_items)
        toolbar.addWidget(self.search_input, 1)  # 搜索框占据剩余空间
        
        layout.addLayout(toolbar)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e0e0e0;
            }
        """)
        
        # 知识点列表
        self.kb_list_widget = QListWidget()
        self.kb_list_widget.setStyleSheet("""
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
        self.kb_list_widget.itemClicked.connect(self.show_detail)
        self.kb_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.kb_list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        # 知识详情区
        detail_container = QWidget()
        detail_layout = QVBoxLayout(detail_container)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(12)
        
        # 详情标题
        self.detail_title = QLabel("选择一个知识条目查看详情")
        self.detail_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976d2; padding: 8px 0;")
        detail_layout.addWidget(self.detail_title)
        
        # 创建时间和更新时间
        self.time_info = QLabel("")
        self.time_info.setStyleSheet("font-size: 12px; color: #757575;")
        detail_layout.addWidget(self.time_info)
        
        # 详情内容
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setStyleSheet("""
            QTextEdit {
                font-size: 15px; 
                color: #444; 
                background: #fff; 
                border-radius: 8px; 
                padding: 12px;
                border: 1px solid #e5e5e5;
            }
        """)
        detail_layout.addWidget(self.detail_text, 1)
        
        # 添加到分割器
        splitter.addWidget(self.kb_list_widget)
        splitter.addWidget(detail_container)
        
        # 设置初始大小比例 (1:2)
        splitter.setSizes([300, 600])
        
        layout.addWidget(splitter, 1)
        
        # 添加统计信息
        self.stats_label = QLabel(f"共 {len(self.knowledge_base.get_all_items())} 条知识")
        self.stats_label.setStyleSheet("color: #757575; font-size: 12px;")
        layout.addWidget(self.stats_label, 0, Qt.AlignmentFlag.AlignRight)
        
        # 初始化列表
        self.refresh_list()
    
    def refresh_list(self):
        """刷新知识列表"""
        self.kb_list_widget.clear()
        for item in self.knowledge_base.get_all_items():
            list_item = QListWidgetItem(item.title)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.kb_list_widget.addItem(list_item)
        
        # 更新统计信息
        self.stats_label.setText(f"共 {len(self.knowledge_base.get_all_items())} 条知识")
    
    def filter_items(self, text):
        """根据搜索文本过滤知识条目"""
        search_text = text.lower()
        for i in range(self.kb_list_widget.count()):
            item = self.kb_list_widget.item(i)
            kb_item = item.data(Qt.ItemDataRole.UserRole)
            if search_text in kb_item.title.lower() or search_text in kb_item.content.lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def show_detail(self, item):
        """显示知识详情"""
        idx = self.kb_list_widget.row(item)
        items = self.knowledge_base.get_all_items()
        if 0 <= idx < len(items):
            kb_item = items[idx]
            self.detail_title.setText(kb_item.title)
            
            # 格式化时间信息
            created_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(kb_item.created_at))
            updated_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(kb_item.updated_at))
            self.time_info.setText(f"创建时间: {created_time} | 更新时间: {updated_time}")
            
            # 使用Markdown渲染内容
            try:
                html_content = markdown.markdown(kb_item.content)
                
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
                    {html_content}
                </body>
                </html>
                """
                
                self.detail_text.setHtml(full_html)
            except Exception as e:
                print(f"渲染Markdown失败: {e}")
                self.detail_text.setPlainText(kb_item.content)
    
    def show_context_menu(self, pos):
        """显示上下文菜单"""
        item = self.kb_list_widget.itemAt(pos)
        if item:
            idx = self.kb_list_widget.row(item)
            menu = QMenu()
            edit_action = menu.addAction("✏️ 编辑知识点")
            del_action = menu.addAction("🗑️ 删除知识点")
            action = menu.exec(self.kb_list_widget.mapToGlobal(pos))
            
            if action == del_action:
                self.remove_item(idx)
            elif action == edit_action:
                self.edit_item(idx)
    
    def show_add_dialog(self):
        """显示添加知识对话框"""
        dialog = KnowledgeEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title = dialog.title_input.text().strip()
            content = dialog.content_input.toPlainText().strip()
            if title and content:
                self.knowledge_base.add_item_from_values(title, content)
                self.refresh_list()
                self.knowledge_updated.emit()
    
    def remove_item(self, index):
        """删除知识条目"""
        confirm = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个知识点吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.knowledge_base.remove_item(index)
            self.refresh_list()
            self.detail_text.clear()
            self.detail_title.setText("选择一个知识条目查看详情")
            self.time_info.setText("")
            self.knowledge_updated.emit()
    
    def edit_item(self, index):
        """编辑知识条目"""
        items = self.knowledge_base.get_all_items()
        if 0 <= index < len(items):
            item = items[index]
            dialog = KnowledgeEditDialog(self, item.title, item.content)
            dialog.setWindowTitle("编辑知识点")
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                title = dialog.title_input.text().strip()
                content = dialog.content_input.toPlainText().strip()
                if title and content:
                    self.knowledge_base.update_item(index, title, content)
                    self.refresh_list()
                    self.knowledge_updated.emit()
    
    def import_knowledge(self):
        """导入知识库"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入知识库", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                imported_kb = self.knowledge_base.load_from_file(file_path)
                
                # 确认导入
                confirm = QMessageBox.question(
                    self,
                    "确认导入",
                    f"发现 {len(imported_kb.get_all_items())} 条知识条目，是否导入？\n"
                    "注意：这将替换当前的知识库内容",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if confirm == QMessageBox.StandardButton.Yes:
                    self.knowledge_base = imported_kb
                    self.refresh_list()
                    self.knowledge_updated.emit()
                    QMessageBox.information(self, "导入成功", f"成功导入 {len(imported_kb.get_all_items())} 条知识条目")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"导入知识库失败：{str(e)}")
    
    def export_knowledge(self):
        """导出知识库"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出知识库", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                self.knowledge_base.save_to_file(file_path)
                QMessageBox.information(self, "导出成功", f"成功导出 {len(self.knowledge_base.get_all_items())} 条知识条目")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出知识库失败：{str(e)}")
    
    def update_knowledge_base(self, knowledge_base):
        """更新知识库引用"""
        self.knowledge_base = knowledge_base
        self.refresh_list()


class KnowledgeEditDialog(QDialog):
    """添加/编辑知识对话框"""
    
    def __init__(self, parent=None, title="", content=""):
        super().__init__(parent)
        self.setWindowTitle("添加知识点")
        self.resize(700, 500)
        self.init_ui(title, content)
    
    def init_ui(self, title, content):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 标题输入
        title_label = QLabel("标题：")
        title_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #333;")
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("知识标题")
        self.title_input.setText(title)
        self.title_input.setStyleSheet("""
            QLineEdit {
                font-size: 14px; 
                padding: 8px; 
                border-radius: 4px; 
                border: 1px solid #ccc;
            }
            QLineEdit:focus {
                border: 1px solid #1976d2;
            }
        """)
        layout.addWidget(self.title_input)
        
        # 内容输入
        content_label = QLabel("内容：")
        content_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #333;")
        layout.addWidget(content_label)
        
        # 添加Markdown提示
        markdown_tip = QLabel("支持Markdown格式")
        markdown_tip.setStyleSheet("font-size: 12px; color: #757575;")
        layout.addWidget(markdown_tip)
        
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("知识内容（支持Markdown格式）")
        self.content_input.setPlainText(content)
        self.content_input.setStyleSheet("""
            QTextEdit {
                font-size: 14px; 
                padding: 8px; 
                border-radius: 4px; 
                border: 1px solid #ccc;
                font-family: monospace;
            }
            QTextEdit:focus {
                border: 1px solid #1976d2;
            }
        """)
        layout.addWidget(self.content_input, 1)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; 
                padding: 8px 16px;
                border-radius: 4px;
                background: #f5f5f5;
                color: #333;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        btn_layout.addWidget(cancel_btn)
        
        # 确认按钮
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; 
                padding: 8px 16px; 
                border-radius: 4px;
                background: #1976d2; 
                color: white;
            }
            QPushButton:hover {
                background: #1565c0;
            }
        """)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout) 