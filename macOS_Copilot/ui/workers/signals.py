from PyQt6.QtCore import QObject, pyqtSignal

class WorkerSignals(QObject):
    """定义工作线程的信号"""
    finished = pyqtSignal()             # 完成信号
    error = pyqtSignal(str)             # 错误信号
    result = pyqtSignal(str)            # 结果信号
    status = pyqtSignal(str)            # 状态信号
    stream_chunk = pyqtSignal(str)      # 流式文本块信号
    stream_start = pyqtSignal()         # 流式输出开始信号
    stream_end = pyqtSignal()           # 流式输出结束信号
    stream_thinking = pyqtSignal(bool)  # 流式思考状态信号（用于显示思考指示器） 