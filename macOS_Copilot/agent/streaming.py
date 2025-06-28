from typing import Optional, Callable, Dict, Any
from langchain_core.callbacks.base import BaseCallbackHandler

class EnhancedStreamingHandler(BaseCallbackHandler):
    """增强的流式处理处理器，支持思考状态和函数调用跟踪"""
    
    def __init__(self, streaming_callback=None, thinking_callback=None, 
                 start_callback=None, end_callback=None,
                 function_call_callback=None, function_result_callback=None):
        """
        初始化增强流式处理器
        
        Args:
            streaming_callback: 处理流式令牌的回调函数
            thinking_callback: 处理思考状态变化的回调函数
            start_callback: LLM开始生成时的回调函数
            end_callback: LLM完成生成时的回调函数
            function_call_callback: 函数调用时的回调函数
            function_result_callback: 函数返回结果时的回调函数
        """
        # 保存回调函数
        self.streaming_callback = streaming_callback
        self.thinking_callback = thinking_callback
        self.start_callback = start_callback
        self.end_callback = end_callback
        self.function_call_callback = function_call_callback
        self.function_result_callback = function_result_callback
        
        # 状态标志
        self.is_thinking = False  # 是否处于思考状态
        self.function_name = None # 当前执行的函数名
        self.generated_tokens = []  # 生成的令牌列表
    
    def on_function_call(self, function_name, arguments):
        """
        函数调用事件处理
        
        Args:
            function_name: 被调用的函数名称
            arguments: 函数参数
        """
        if self.thinking_callback:
            # 进入思考状态，因为正在处理函数调用
            self.is_thinking = True
            self.thinking_callback(True)
            
        if self.function_call_callback:
            # 调用函数调用回调
            self.function_call_callback(function_name, arguments)
    
    def on_function_result(self, result):
        """
        函数结果事件处理
        
        Args:
            result: 函数执行结果
        """
        if self.function_result_callback:
            # 调用函数结果回调
            self.function_result_callback(result)
    
    def on_llm_start(self, *args, **kwargs):
        """LLM开始生成回调"""
        if self.start_callback:
            self.start_callback()
    
    def on_llm_new_token(self, token: str, **kwargs):
        """
        处理新的LLM令牌
        
        Args:
            token: 新生成的令牌
            **kwargs: 其他参数
        """
        # 添加到令牌列表
        self.generated_tokens.append(token)
        
        # 检测思考状态变化
        if "thinking" in token.lower() or "<thinking>" in token.lower():
            if not self.is_thinking and self.thinking_callback:
                self.is_thinking = True
                self.thinking_callback(True)
                return  # 不显示思考标记
        elif self.is_thinking and ("</thinking>" in token.lower() or token.strip() == ""):
            if self.thinking_callback:
                self.is_thinking = False
                self.thinking_callback(False)
                return  # 不显示思考结束标记
        
        # 如果不是思考状态，并且有流式回调，则调用回调
        if not self.is_thinking and self.streaming_callback:
            self.streaming_callback(token)
    
    def on_llm_end(self, *args, **kwargs):
        """LLM结束生成回调"""
        # 确保思考状态被重置
        if self.is_thinking and self.thinking_callback:
            self.is_thinking = False
            self.thinking_callback(False)
        
        # 调用结束回调
        if self.end_callback:
            self.end_callback() 