from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve, 
                         QPoint, pyqtProperty)
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

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