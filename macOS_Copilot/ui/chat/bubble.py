import markdown
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QTextBrowser, 
                            QSizePolicy)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCursor, QTextOption

from macOS_Copilot.ui.widgets.animation import BreathingDotIndicator

class ChatBubble(QFrame):
    """聊天气泡组件，支持Markdown渲染与流式输出"""
    
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
        self.text_browser = self._create_text_browser()
        
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
    
    def _create_text_browser(self):
        """创建文本浏览器组件"""
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        
        # 完全禁用滚动条
        text_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        text_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 设置优化的自动换行
        text_browser.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        
        # 设置大小策略为完全自适应
        text_browser.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        # 文本不可编辑，但可选择
        text_browser.setReadOnly(True)
        text_browser.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        
        # 设置文本浏览器样式
        if self.is_user:
            text_browser.setStyleSheet(self._get_user_text_browser_style())
        else:
            text_browser.setStyleSheet(self._get_assistant_text_browser_style())
            
        return text_browser
    
    def _get_user_text_browser_style(self):
        """获取用户消息文本浏览器样式"""
        return """
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
        """
    
    def _get_assistant_text_browser_style(self):
        """获取助手消息文本浏览器样式"""
        return """
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
        """
    
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
                cursor.movePosition(QTextCursor.MoveOperation.End)
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