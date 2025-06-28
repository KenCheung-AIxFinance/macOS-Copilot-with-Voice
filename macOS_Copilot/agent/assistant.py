from typing import Generator, Dict, Any, Optional, List
import enum
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.callbacks.base import BaseCallbackHandler

from .types import ArchitectureType, TaskComplexity
from .streaming import EnhancedStreamingHandler
from .enhancer import DeepSeekR1Enhancer
from .tools import MacOSTools

class IntelligentMacOSAssistant:
    """增强智能的macOS系统助手"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化智能macOS助手
        
        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        
        # 创建基础LLM
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.7,
            streaming=True  # 启用流式响应
        )
        
        # 创建R1增强器
        self.r1_enhancer = DeepSeekR1Enhancer(api_key, base_url)
        
        # 注册R1增强器到MacOSTools类
        MacOSTools.set_r1_enhancer(self.r1_enhancer)
        
        # 初始化use_r1_enhancement标志
        self.use_r1_enhancement = False
        
        # 获取所有工具
        self.tools = [
            MacOSTools.get_system_info,
            MacOSTools.get_running_processes,
            MacOSTools.open_application,
            MacOSTools.execute_terminal_command,
            MacOSTools.get_network_info,
            MacOSTools.get_battery_info,
            MacOSTools.search_files,
            MacOSTools.get_installed_applications,
            MacOSTools.create_note,
            MacOSTools.set_system_volume,
            MacOSTools.get_current_time
        ]
        
        # 用户上下文记忆：保存用户偏好和使用模式
        self.user_context = {
            "preferred_complexity_level": None,  # 用户偏好的复杂度级别
            "common_tasks": {},                  # 常见任务及其复杂度
            "error_history": [],                 # 错误历史
            "successful_strategies": {}          # 成功策略记录
        }
        
        # 创建各种模式的系统提示
        self._init_system_prompts()
        
        # 为不同架构创建提示模板
        self._init_prompt_templates()
        
        # 创建不同类型的代理
        self._init_agents()
        
        # 聊天历史
        self.chat_history = []
        
        # 任务计数器（用于评估成功率）
        self.task_counter = 0
        self.success_counter = 0
    
    def _init_system_prompts(self):
        """初始化不同模式的系统提示"""
        # 基础提示
        self.base_prompt = """你是一个macOS系统助手，类似于Windows Copilot。你的主要功能包括：

1. 系统信息查询：获取系统状态、进程信息、网络状态、电池信息等
2. 应用程序管理：打开应用程序、查看已安装应用
3. 文件操作：搜索文件、创建笔记
4. 系统控制：设置音量、执行终端命令
5. 时间查询：获取当前时间

请根据用户的需求选择合适的工具来帮助用户。始终用中文回复，保持友好和专业的语气。

重要规则：
- 在执行任何可能影响系统的命令前，要谨慎并确认用户意图
- 对于危险操作，要提醒用户风险
- 优先使用安全的系统工具
- 如果用户请求的操作超出你的能力范围，要明确说明
"""

        # 思考链COT提示（包含详细的思考步骤）
        self.cot_prompt = self.base_prompt + """
执行任务时，请遵循以下思考链步骤：
1. 理解：明确用户的真实意图和请求的核心需求
2. 分析：思考满足需求的可能方法和步骤
3. 规划：确定执行步骤的顺序和依赖关系
4. 工具选择：选择合适的系统工具执行任务
5. 执行：按照规划执行操作，并记录结果
6. 验证：确认操作是否成功满足用户需求
7. 总结：简明扼要地向用户汇报结果

不要在回复中使用数字步骤编号，而是以流畅自然的方式呈现思考过程。
"""

        # ReAct模式提示（使用推理和行动循环）
        self.react_prompt = self.base_prompt + """
请使用ReAct（推理+行动）框架来完成任务：
1. 推理(Reasoning): 思考用户请求，推断需要的行动
2. 行动(Acting): 选择适当的工具执行行动
3. 观察(Observation): 观察行动结果
4. 继续推理: 根据观察结果继续推理...

对于每个步骤，请考虑：
- 当前状态分析
- 可能的行动选择
- 预期结果和风险
- 失败时的替代方案

进行多步骤操作时，确保每步都检查结果并适当调整后续行动。如果遇到错误，尝试理解错误原因并提供解决方案或替代方案。
"""

        # 完整Planner提示（包含详细的规划步骤）
        self.planner_prompt = self.base_prompt + """
请使用以下规划方法处理复杂任务：

1. 需求理解：深入分析用户需求，确认任务目标
2. 任务分解：将复杂任务分解为多个小任务
3. 依赖识别：确定子任务之间的依赖关系和执行顺序
4. 资源评估：评估完成任务所需的系统资源
5. 策略选择：为每个子任务选择最优工具和方法
6. 风险分析：识别可能的风险点和失败可能
7. 执行计划：按照规划执行各项子任务
8. 适应调整：根据执行情况动态调整后续计划
9. 结果验证：验证最终结果是否符合用户期望
10. 经验积累：记录解决方案，用于未来类似问题

处理任务时，首先生成完整计划，然后逐步执行，适当时向用户提供进度更新。
"""

    def _init_prompt_templates(self):
        """初始化不同架构的提示模板"""
        # 直接响应模板
        self.direct_prompt = ChatPromptTemplate.from_messages([
            ("system", self.base_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 基础COT模板
        self.basic_cot_prompt = ChatPromptTemplate.from_messages([
            ("system", self.base_prompt + "\n请在回答前先思考问题的解决步骤，但不要在回复中展示思考过程。"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 完整COT模板
        self.full_cot_prompt = ChatPromptTemplate.from_messages([
            ("system", self.cot_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # ReAct模板
        self.react_prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.react_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Planner模板
        self.planner_prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.planner_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
    
    def _init_agents(self):
        """初始化不同类型的代理"""
        # 直接响应代理
        self.direct_agent = create_openai_tools_agent(self.llm, self.tools, self.direct_prompt)
        self.direct_executor = AgentExecutor(agent=self.direct_agent, tools=self.tools, verbose=True)
        
        # 基础COT代理
        self.basic_cot_agent = create_openai_tools_agent(self.llm, self.tools, self.basic_cot_prompt)
        self.basic_cot_executor = AgentExecutor(agent=self.basic_cot_agent, tools=self.tools, verbose=True)
        
        # 完整COT代理
        self.full_cot_agent = create_openai_tools_agent(self.llm, self.tools, self.full_cot_prompt)
        self.full_cot_executor = AgentExecutor(agent=self.full_cot_agent, tools=self.tools, verbose=True)
        
        # ReAct代理
        self.react_agent = create_openai_tools_agent(self.llm, self.tools, self.react_prompt_template)
        self.react_executor = AgentExecutor(agent=self.react_agent, tools=self.tools, verbose=True)
        
        # Planner代理
        self.planner_agent = create_openai_tools_agent(self.llm, self.tools, self.planner_prompt_template)
        self.planner_executor = AgentExecutor(agent=self.planner_agent, tools=self.tools, verbose=True)
    
    def _evaluate_task_complexity(self, user_input: str) -> TaskComplexity:
        """评估任务复杂度"""
        # 基本关键词匹配
        simple_keywords = ["查看", "显示", "获取", "是什么", "当前"]
        medium_keywords = ["打开", "设置", "搜索", "创建", "调整"]
        complex_keywords = ["如何", "怎样", "分析", "诊断", "优化", "解决"]
        advanced_keywords = ["自动化", "批量", "监控", "定时", "脚本"]
        
        # 计算匹配的关键词数量
        simple_count = sum(1 for kw in simple_keywords if kw in user_input)
        medium_count = sum(1 for kw in medium_keywords if kw in user_input)
        complex_count = sum(1 for kw in complex_keywords if kw in user_input)
        advanced_count = sum(1 for kw in advanced_keywords if kw in user_input)
        
        # 根据匹配数量确定复杂度
        if advanced_count > 0:
            complexity = TaskComplexity.ADVANCED
        elif complex_count > 0:
            complexity = TaskComplexity.COMPLEX
        elif medium_count > 0:
            complexity = TaskComplexity.MEDIUM
        else:
            complexity = TaskComplexity.SIMPLE
        
        # 使用R1增强器进一步评估（如果启用）
        if self.use_r1_enhancement:
            enhanced_complexity = self.r1_enhancer.enhance_complexity_evaluation(user_input, complexity)
            return enhanced_complexity
        
        return complexity
    
    def _select_architecture(self, complexity: TaskComplexity) -> ArchitectureType:
        """根据任务复杂度选择架构"""
        # 如果用户有偏好的复杂度级别，优先使用
        if self.user_context["preferred_complexity_level"]:
            return self.user_context["preferred_complexity_level"]
        
        # 根据任务复杂度选择架构
        if complexity == TaskComplexity.SIMPLE:
            return ArchitectureType.DIRECT
        elif complexity == TaskComplexity.MEDIUM:
            return ArchitectureType.BASIC_COT
        elif complexity == TaskComplexity.COMPLEX:
            return ArchitectureType.FULL_COT
        elif complexity == TaskComplexity.ADVANCED:
            return ArchitectureType.PLANNER
        else:
            return ArchitectureType.DIRECT
    
    def _get_executor_for_architecture(self, architecture: ArchitectureType):
        """根据架构类型获取执行器"""
        if architecture == ArchitectureType.DIRECT:
            return self.direct_executor
        elif architecture == ArchitectureType.BASIC_COT:
            return self.basic_cot_executor
        elif architecture == ArchitectureType.FULL_COT:
            return self.full_cot_executor
        elif architecture == ArchitectureType.REACT:
            return self.react_executor
        elif architecture == ArchitectureType.PLANNER:
            return self.planner_executor
        else:
            return self.direct_executor
    
    def _track_success(self, complexity: TaskComplexity, architecture: ArchitectureType, successful: bool = True):
        """跟踪任务执行成功率"""
        self.task_counter += 1
        if successful:
            self.success_counter += 1
        
        # 更新成功策略记录
        key = f"{complexity.name}_{architecture.name}"
        if key not in self.user_context["successful_strategies"]:
            self.user_context["successful_strategies"][key] = {"count": 0, "success": 0}
        
        self.user_context["successful_strategies"][key]["count"] += 1
        if successful:
            self.user_context["successful_strategies"][key]["success"] += 1
    
    def chat_stream(self, user_input: str) -> Generator[str, None, None]:
        """流式聊天接口"""
        # 评估任务复杂度
        complexity = self._evaluate_task_complexity(user_input)
        
        # 选择架构
        architecture = self._select_architecture(complexity)
        
        # 获取对应的执行器
        executor = self._get_executor_for_architecture(architecture)
        
        # 创建流式处理器
        streaming_buffer = []
        
        def token_callback(token):
            streaming_buffer.append(token)
            yield token
        
        # 创建回调处理器
        class StreamingCallbackHandler(BaseCallbackHandler):
            def __init__(self, callback):
                self.callback = callback
            
            def on_llm_new_token(self, token, **kwargs):
                for t in self.callback(token):
                    pass
        
        # 执行代理
        try:
            # 将用户输入添加到聊天历史
            self.chat_history.append(HumanMessage(content=user_input))
            
            # 执行代理并流式返回结果
            response = executor.invoke(
                {
                    "input": user_input,
                    "chat_history": self.chat_history
                },
                config={"callbacks": [StreamingCallbackHandler(token_callback)]}
            )
            
            # 将助手回复添加到聊天历史
            self.chat_history.append(AIMessage(content=response["output"]))
            
            # 跟踪成功
            self._track_success(complexity, architecture, True)
            
            # 返回完整缓冲区
            full_response = "".join(streaming_buffer)
            return full_response
        except Exception as e:
            # 跟踪失败
            self._track_success(complexity, architecture, False)
            
            # 添加错误信息到历史
            error_msg = f"处理请求时出错: {str(e)}"
            self.user_context["error_history"].append({
                "input": user_input,
                "error": str(e),
                "timestamp": time.time()
            })
            
            # 返回错误信息
            return error_msg
    
    def stream_with_handler(self, user_input: str, custom_handler: EnhancedStreamingHandler) -> Generator[str, None, None]:
        """使用自定义处理器的流式聊天"""
        # 评估任务复杂度
        complexity = self._evaluate_task_complexity(user_input)
        
        # 选择架构
        architecture = self._select_architecture(complexity)
        
        # 获取对应的执行器
        executor = self._get_executor_for_architecture(architecture)
        
        # 创建函数调用跟踪器
        class FunctionCallTracker(BaseCallbackHandler):
            def __init__(self):
                self.current_function = None
            
            def on_tool_start(self, serialized, input_str, **kwargs):
                # 记录工具调用开始
                function_name = serialized.get("name", "unknown_function")
                
                # 提取参数
                try:
                    args = input_str
                    # 通知处理器
                    if custom_handler:
                        custom_handler.on_function_call(function_name, args)
                except Exception as e:
                    print(f"处理函数调用时出错: {e}")
            
            def on_tool_end(self, output, **kwargs):
                # 记录工具调用结束及其结果
                if custom_handler:
                    custom_handler.on_function_result(output)
        
        # 创建回调处理器列表
        callbacks = [custom_handler, FunctionCallTracker()]
        
        # 执行代理
        try:
            # 将用户输入添加到聊天历史
            self.chat_history.append(HumanMessage(content=user_input))
            
            # 通知处理器流开始
            if hasattr(custom_handler, 'on_llm_start'):
                custom_handler.on_llm_start()
            
            # 执行代理并流式返回结果
            response = executor.invoke(
                {
                    "input": user_input,
                    "chat_history": self.chat_history
                },
                config={"callbacks": callbacks}
            )
            
            # 将助手回复添加到聊天历史
            self.chat_history.append(AIMessage(content=response["output"]))
            
            # 跟踪成功
            self._track_success(complexity, architecture, True)
            
            # 通知处理器流结束
            if hasattr(custom_handler, 'on_llm_end'):
                custom_handler.on_llm_end()
            
            # 返回完整响应
            return response["output"]
        except Exception as e:
            # 跟踪失败
            self._track_success(complexity, architecture, False)
            
            # 添加错误信息到历史
            error_msg = f"处理请求时出错: {str(e)}"
            self.user_context["error_history"].append({
                "input": user_input,
                "error": str(e),
                "timestamp": time.time()
            })
            
            # 通知处理器流结束
            if hasattr(custom_handler, 'on_llm_end'):
                custom_handler.on_llm_end()
            
            # 返回错误信息
            return error_msg
    
    def chat(self, user_input: str) -> str:
        """非流式聊天接口"""
        # 收集流式输出的所有块
        chunks = []
        for chunk in self.chat_stream(user_input):
            chunks.append(chunk)
        
        # 返回完整响应
        return "".join(chunks)
    
    def reset_chat(self):
        """重置聊天状态"""
        self.chat_history = []
        
    def set_api_key(self, api_key: str):
        """设置API密钥"""
        self.api_key = api_key
        # 更新LLM的API密钥
        self.llm.openai_api_key = api_key
        # 更新R1增强器的API密钥
        self.r1_enhancer.api_key = api_key
        # 重新初始化代理
        self._init_agents() 