from PyQt6.QtCore import QThread, QTimer
from macOS_Copilot.ui.workers.signals import WorkerSignals
from macOS_Copilot.agent.streaming import EnhancedStreamingHandler

class StreamingAssistantWorker(QThread):
    """处理助手流式响应的工作线程"""
    def __init__(self, assistant, user_input):
        super().__init__()
        self.assistant = assistant
        self.user_input = user_input
        self.signals = WorkerSignals()
        self.active = True  # 控制线程是否继续处理
        
        # 流式处理器配置
        self.streaming_handler = None

    def stop(self):
        """停止流式输出处理"""
        self.active = False

    def run(self):
        try:
            # 发送流式输出开始信号
            self.signals.stream_start.emit()
            
            # 创建增强的流式处理器
            self.streaming_handler = self._create_streaming_handler()
            
            # 使用流式响应
            full_response = ""
            
            # 使用包含回调处理器的流式方法
            response = self.assistant.stream_with_handler(self.user_input, self.streaming_handler)
            
            # 如果返回值是生成器，则迭代处理
            if hasattr(response, '__iter__'):
                for chunk in response:
                    if not self.active:
                        break  # 如果被停止则中断处理
                    
                    if chunk:  # 确保块不为空
                        full_response += chunk
            else:
                # 如果是字符串，直接使用
                full_response = response
            
            # 发送完整响应用于其他处理（如TTS）
            if self.active:  # 只在正常完成时发送结果
                self.signals.result.emit(full_response)
                
            # 发送流式输出结束信号
            self.signals.stream_end.emit()
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()
            
    def _create_streaming_handler(self):
        """创建流式处理器，配置所有回调"""
        return EnhancedStreamingHandler(
            streaming_callback=lambda token: self.handle_token(token),
            thinking_callback=lambda is_thinking: self.signals.stream_thinking.emit(is_thinking),
            start_callback=lambda: self.signals.stream_start.emit(),
            end_callback=lambda: self.signals.stream_end.emit(),
            function_call_callback=lambda name, args: self.handle_function_call(name, args),
            function_result_callback=lambda result: self.handle_function_result(result)
        )
            
    def handle_token(self, token):
        """处理从增强流式处理器收到的单个令牌"""
        if not self.active:
            return
        
        # 发送文本块
        self.signals.stream_chunk.emit(token)
    
    def handle_function_call(self, name, args):
        """处理函数调用事件"""
        if not self.active:
            return
        
        # 这里可以添加函数调用的UI反馈，例如显示正在执行的工具
        function_message = f"正在执行: {name}"
        self.signals.status.emit(function_message)
    
    def handle_function_result(self, result):
        """处理函数结果事件"""
        if not self.active:
            return
        
        # 这里可以添加函数结果的UI反馈
        # 例如，可以在UI中显示工具执行结果的摘要
        pass 