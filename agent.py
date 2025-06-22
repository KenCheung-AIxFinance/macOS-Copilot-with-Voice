import os
import sys
import subprocess
import json
import psutil
import platform
from typing import List, Dict, Any, Optional, Generator, Tuple, Union
from datetime import datetime
import threading
import time
import re
import enum

# LangChain imports
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.tools import BaseTool
from langchain.schema import BaseOutputParser
from langchain_core.callbacks import StreamingStdOutCallbackHandler
import asyncio

class MacOSTools:
    """macOS系统工具集合"""
    
    @staticmethod
    @tool
    def get_system_info() -> str:
        """获取macOS系统信息"""
        try:
            # 系统版本信息
            version_info = subprocess.run(['sw_vers'], capture_output=True, text=True)
            # CPU信息
            cpu_info = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True)
            # 内存信息
            memory = psutil.virtual_memory()
            # 磁盘信息
            disk = psutil.disk_usage('/')
            
            info = f"""
系统信息:
{version_info.stdout}
CPU: {cpu_info.stdout.strip()}
内存: {memory.total // (1024**3)}GB 总内存, {memory.percent}% 使用率
磁盘: {disk.total // (1024**3)}GB 总空间, {disk.percent}% 使用率
            """
            return info
        except Exception as e:
            return f"获取系统信息失败: {str(e)}"
    
    @staticmethod
    @tool
    def get_running_processes() -> str:
        """获取正在运行的进程列表"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 按CPU使用率排序，取前10个
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            top_processes = processes[:10]
            
            result = "正在运行的进程 (按CPU使用率排序):\n"
            for proc in top_processes:
                result += f"PID: {proc['pid']}, 名称: {proc['name']}, CPU: {proc['cpu_percent']:.1f}%, 内存: {proc['memory_percent']:.1f}%\n"
            
            return result
        except Exception as e:
            return f"获取进程信息失败: {str(e)}"
    
    @staticmethod
    @tool
    def open_application(app_name: str) -> str:
        """打开指定的应用程序"""
        try:
            # 首先获取所有已安装的应用程序
            all_apps = MacOSTools._get_all_applications()
            
            if not all_apps:
                return "无法获取应用程序列表"
            
            # 智能匹配应用程序
            matched_apps = MacOSTools._find_matching_apps(app_name, all_apps)
            
            if not matched_apps:
                return f"未找到匹配的应用程序: {app_name}"
            
            # 如果找到多个匹配项，选择最佳匹配
            best_match = matched_apps[0]
            
            # 打开应用程序
            subprocess.run(['open', best_match['path']])
            
            if len(matched_apps) > 1:
                # 如果有多个匹配项，提供建议
                suggestions = [app['name'] for app in matched_apps[1:3]]  # 显示前3个匹配项
                return f"已打开 {best_match['name']}。其他可能的匹配: {', '.join(suggestions)}"
            else:
                return f"已打开 {best_match['name']}"
                
        except Exception as e:
            return f"打开应用程序失败: {str(e)}"
    
    @staticmethod
    def _get_all_applications():
        """获取所有已安装的应用程序"""
        apps = []
        
        # 搜索系统应用程序目录
        search_paths = [
            '/Applications',
            '/System/Applications',
            '/System/Applications/Utilities',
            os.path.expanduser('~/Applications')
        ]
        
        for search_path in search_paths:
            if os.path.exists(search_path):
                try:
                    result = subprocess.run(['find', search_path, '-name', '*.app', '-type', 'd'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.stdout.strip():
                        for app_path in result.stdout.strip().split('\n'):
                            if app_path and os.path.exists(app_path):
                                app_name = os.path.basename(app_path).replace('.app', '')
                                apps.append({
                                    'name': app_name,
                                    'path': app_path,
                                    'display_name': app_name
                                })
                except:
                    continue
        
        return apps
    
    @staticmethod
    def _find_matching_apps(query, apps):
        """智能匹配应用程序"""
        query_lower = query.lower().strip()
        matches = []
        
        for app in apps:
            app_name_lower = app['name'].lower()
            display_name_lower = app['display_name'].lower()
            
            # 计算匹配分数
            score = 0
            
            # 完全匹配
            if query_lower == app_name_lower or query_lower == display_name_lower:
                score = 100
            # 开头匹配
            elif app_name_lower.startswith(query_lower) or display_name_lower.startswith(query_lower):
                score = 80
            # 包含匹配
            elif query_lower in app_name_lower or query_lower in display_name_lower:
                score = 60
            # 部分词匹配
            else:
                query_words = query_lower.split()
                app_words = app_name_lower.split()
                
                for query_word in query_words:
                    for app_word in app_words:
                        if query_word in app_word or app_word in query_word:
                            score += 20
                            break
            
            # 特殊处理常见应用程序的别名
            aliases = {
                'safari': ['safari', '浏览器', 'web'],
                'chrome': ['chrome', 'google chrome', '谷歌浏览器'],
                'terminal': ['terminal', '终端', '命令行'],
                'finder': ['finder', '访达', '文件管理器'],
                'calculator': ['calculator', '计算器', 'calc'],
                'mail': ['mail', '邮件', '邮箱'],
                'messages': ['messages', '信息', '短信'],
                'facetime': ['facetime', '视频通话'],
                'photos': ['photos', '照片', '相册'],
                'music': ['music', '音乐', 'itunes'],
                'tv': ['tv', '电视', '视频'],
                'podcasts': ['podcasts', '播客'],
                'books': ['books', '图书', '阅读'],
                'notes': ['notes', '备忘录', '笔记'],
                'reminders': ['reminders', '提醒事项'],
                'calendar': ['calendar', '日历'],
                'contacts': ['contacts', '通讯录', '联系人'],
                'maps': ['maps', '地图'],
                'weather': ['weather', '天气'],
                'stocks': ['stocks', '股票'],
                'voice_memos': ['voice memos', '语音备忘录'],
                'home': ['home', '家庭'],
                'shortcuts': ['shortcuts', '快捷指令'],
                'settings': ['settings', '系统偏好设置', '设置'],
                'vscode': ['visual studio code', 'vscode', 'vs code', '代码编辑器'],
                'premiere': ['adobe premiere pro', 'premiere', 'pr', '视频编辑'],
                'photoshop': ['adobe photoshop', 'photoshop', 'ps', '图像编辑'],
                'illustrator': ['adobe illustrator', 'illustrator', 'ai', '矢量图'],
                'after_effects': ['adobe after effects', 'after effects', 'ae', '特效'],
                'xd': ['adobe xd', 'xd', '设计'],
                'figma': ['figma', '设计工具'],
                'sketch': ['sketch', '设计'],
                'xcode': ['xcode', '开发工具'],
                'intellij': ['intellij idea', 'intellij', '开发工具'],
                'pycharm': ['pycharm', 'python开发'],
                'sublime': ['sublime text', 'sublime', '文本编辑器'],
                'atom': ['atom', '文本编辑器'],
                'spotify': ['spotify', '音乐播放器'],
                'zoom': ['zoom', '视频会议'],
                'teams': ['microsoft teams', 'teams', '团队协作'],
                'slack': ['slack', '团队沟通'],
                'discord': ['discord', '游戏聊天'],
                'wechat': ['wechat', '微信'],
                'qq': ['qq', '腾讯qq'],
                'alipay': ['alipay', '支付宝'],
                'taobao': ['taobao', '淘宝'],
                'jd': ['jd', '京东'],
                'netflix': ['netflix', '网飞'],
                'youtube': ['youtube', '油管'],
                'bilibili': ['bilibili', 'b站', '哔哩哔哩']
            }
            
            # 检查别名匹配
            for app_key, alias_list in aliases.items():
                if query_lower in alias_list:
                    if app_name_lower in alias_list or any(alias in app_name_lower for alias in alias_list):
                        score = max(score, 90)
            
            if score > 0:
                matches.append((app, score))
        
        # 按分数排序，返回前5个最佳匹配
        matches.sort(key=lambda x: x[1], reverse=True)
        return [app for app, score in matches[:5]]
    
    @staticmethod
    @tool
    def execute_terminal_command(command: str) -> str:
        """执行终端命令"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return f"命令执行成功:\n{result.stdout}"
            else:
                return f"命令执行失败:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "命令执行超时"
        except Exception as e:
            return f"执行命令失败: {str(e)}"
    
    @staticmethod
    @tool
    def get_network_info() -> str:
        """获取网络连接信息"""
        try:
            # 获取网络接口信息
            interfaces = psutil.net_if_addrs()
            # 获取网络连接状态
            connections = psutil.net_connections()
            
            result = "网络信息:\n"
            
            # 显示网络接口
            for interface, addrs in interfaces.items():
                result += f"\n接口: {interface}\n"
                for addr in addrs:
                    result += f"  {addr.family.name}: {addr.address}\n"
            
            # 显示活跃连接
            active_connections = [conn for conn in connections if conn.status == 'ESTABLISHED']
            result += f"\n活跃连接数: {len(active_connections)}"
            
            return result
        except Exception as e:
            return f"获取网络信息失败: {str(e)}"
    
    @staticmethod
    @tool
    def get_battery_info() -> str:
        """获取电池信息"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                plugged = "已连接电源" if battery.power_plugged else "使用电池"
                percent = battery.percent
                time_left = battery.secsleft if battery.secsleft != -1 else "未知"
                
                if time_left != "未知":
                    hours = time_left // 3600
                    minutes = (time_left % 3600) // 60
                    time_str = f"{hours}小时{minutes}分钟"
                else:
                    time_str = "未知"
                
                return f"电池状态: {plugged}\n电量: {percent}%\n剩余时间: {time_str}"
            else:
                return "无法获取电池信息"
        except Exception as e:
            return f"获取电池信息失败: {str(e)}"
    
    @staticmethod
    @tool
    def search_files(query: str, directory: str = "/Users") -> str:
        """搜索文件"""
        try:
            # 使用find命令搜索文件
            command = f'find "{directory}" -name "*{query}*" -type f 2>/dev/null | head -20'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.stdout.strip():
                files = result.stdout.strip().split('\n')
                return f"找到以下文件:\n" + "\n".join(files)
            else:
                return f"在 {directory} 中未找到包含 '{query}' 的文件"
        except Exception as e:
            return f"搜索文件失败: {str(e)}"
    
    @staticmethod
    @tool
    def get_installed_applications() -> str:
        """获取已安装的应用程序列表"""
        try:
            # 使用新的动态获取方法
            all_apps = MacOSTools._get_all_applications()
            
            if not all_apps:
                return "未找到应用程序"
            
            # 按名称排序
            all_apps.sort(key=lambda x: x['name'].lower())
            
            # 只显示前30个应用程序
            apps_to_show = all_apps[:30]
            
            result = f"已安装的应用程序 (共{len(all_apps)}个，显示前30个):\n"
            for i, app in enumerate(apps_to_show, 1):
                result += f"{i}. {app['name']}\n"
            
            if len(all_apps) > 30:
                result += f"\n... 还有 {len(all_apps) - 30} 个应用程序"
            
            return result
        except Exception as e:
            return f"获取应用程序列表失败: {str(e)}"
    
    @staticmethod
    @tool
    def create_note(content: str, filename: str = None) -> str:
        """创建笔记文件"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"note_{timestamp}.txt"
            
            # 确保文件路径在用户目录下
            filepath = os.path.expanduser(f"~/Desktop/{filename}")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n")
                f.write(content)
            
            return f"笔记已创建: {filepath}"
        except Exception as e:
            return f"创建笔记失败: {str(e)}"
    
    @staticmethod
    @tool
    def set_system_volume(volume: int) -> str:
        """设置系统音量 (0-100)"""
        try:
            if not 0 <= volume <= 100:
                return "音量必须在0-100之间"
            
            # 使用osascript设置音量
            script = f'set volume output volume {volume}'
            subprocess.run(['osascript', '-e', script])
            return f"系统音量已设置为 {volume}%"
        except Exception as e:
            return f"设置音量失败: {str(e)}"
    
    @staticmethod
    @tool
    def get_current_time() -> str:
        """获取当前时间"""
        now = datetime.now()
        return f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}"

class TaskComplexity(enum.Enum):
    """任务复杂度枚举"""
    SIMPLE = 1   # 简单任务：直接查询、单一操作
    MEDIUM = 2   # 中等任务：2-3步操作，有条件判断
    COMPLEX = 3  # 复杂任务：多步骤，需要推理，系统诊断
    ADVANCED = 4 # 高级任务：创造性解决方案，复杂诊断，自适应执行

class ArchitectureType(enum.Enum):
    """架构类型枚举"""
    DIRECT = 1       # 直接响应，无思考链
    BASIC_COT = 2    # 基础思考链
    FULL_COT = 3     # 完整思考链
    REACT = 4        # Reasoning + Acting 架构
    PLANNER = 5      # 完整规划架构

class IntelligentMacOSAssistant:
    """增强智能的macOS系统助手"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
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
        # 任务复杂度评估提示
        complexity_prompt = """
请评估以下用户请求的复杂度，并返回相应的复杂度级别编号:
1 = 简单任务 (直接查询、单一操作，如查看时间、打开应用)
2 = 中等任务 (2-3步操作，有条件判断，如查找特定文件) 
3 = 复杂任务 (多步骤，需要推理，系统诊断，如解决问题)
4 = 高级任务 (创造性解决方案，复杂诊断，自适应执行)

只返回一个数字，不要解释。用户请求："{user_input}"
"""
        
        try:
            # 检查是否已有相似请求的复杂度评估
            for task, complexity in self.user_context["common_tasks"].items():
                if self._calculate_similarity(task, user_input) > 0.8:  # 80%相似度阈值
                    return complexity
            
            # 检查关键词模式
            # 简单任务
            simple_patterns = [
                r"时间|现在几点", 
                r"打开\s*[\w\s]+", 
                r"(?:设置|调整)\s*音量", 
                r"(?:查看|显示)\s*(?:系统信息|电池|网络|时间)"
            ]
            
            # 中等任务
            medium_patterns = [
                r"搜索\s*[\w\s]+", 
                r"创建\s*(?:笔记|文件)", 
                r"运行\s*(?:命令|脚本)",
                r"进程|安装的应用"
            ]
            
            # 复杂任务
            complex_patterns = [
                r"(?:诊断|解决|修复)\s*问题",
                r"(?:比较|分析)\s*[\w\s]+",
                r"(?:优化|提高)\s*[\w\s]+",
                r"如何\s*(?!打开|设置|调整|查看|显示)"  # 如何+动词，但排除简单操作
            ]
            
            # 高级任务
            advanced_patterns = [
                r"自动化\s*[\w\s]+",
                r"编写\s*(?:脚本|程序)",
                r"监控\s*[\w\s]+",
                r"实现\s*[\w\s]+功能"
            ]
            
            # 检查模式匹配
            for pattern in simple_patterns:
                if re.search(pattern, user_input):
                    self.user_context["common_tasks"][user_input] = TaskComplexity.SIMPLE
                    return TaskComplexity.SIMPLE
                    
            for pattern in medium_patterns:
                if re.search(pattern, user_input):
                    self.user_context["common_tasks"][user_input] = TaskComplexity.MEDIUM
                    return TaskComplexity.MEDIUM
                    
            for pattern in complex_patterns:
                if re.search(pattern, user_input):
                    self.user_context["common_tasks"][user_input] = TaskComplexity.COMPLEX
                    return TaskComplexity.COMPLEX
                    
            for pattern in advanced_patterns:
                if re.search(pattern, user_input):
                    self.user_context["common_tasks"][user_input] = TaskComplexity.ADVANCED
                    return TaskComplexity.ADVANCED
            
            # 使用LLM评估复杂度
            result = self.llm.invoke(complexity_prompt.format(user_input=user_input))
            complexity_text = result.content.strip()
            
            # 提取数字
            if '1' in complexity_text:
                complexity = TaskComplexity.SIMPLE
            elif '2' in complexity_text:
                complexity = TaskComplexity.MEDIUM
            elif '3' in complexity_text:
                complexity = TaskComplexity.COMPLEX
            else:
                complexity = TaskComplexity.ADVANCED
            
            # 保存到用户上下文
            self.user_context["common_tasks"][user_input] = complexity
            return complexity
            
        except Exception as e:
            print(f"复杂度评估错误: {str(e)}")
            # 默认返回中等复杂度
            return TaskComplexity.MEDIUM
    
    def _select_architecture(self, complexity: TaskComplexity) -> ArchitectureType:
        """根据任务复杂度选择合适的架构"""
        # 如果用户有特定偏好，优先使用
        if self.user_context["preferred_complexity_level"]:
            return self.user_context["preferred_complexity_level"]
        
        # 根据任务复杂度映射到架构类型
        architecture_map = {
            TaskComplexity.SIMPLE: ArchitectureType.DIRECT,
            TaskComplexity.MEDIUM: ArchitectureType.BASIC_COT,
            TaskComplexity.COMPLEX: ArchitectureType.FULL_COT,
            TaskComplexity.ADVANCED: ArchitectureType.PLANNER
        }
        
        # 查看成功策略历史，调整架构选择
        for task_type, strategies in self.user_context["successful_strategies"].items():
            if task_type == complexity and strategies:
                # 返回最成功的策略
                return max(strategies, key=strategies.get)
        
        return architecture_map[complexity]
    
    def _get_executor_for_architecture(self, architecture: ArchitectureType):
        """获取指定架构类型的执行器"""
        executor_map = {
            ArchitectureType.DIRECT: self.direct_executor,
            ArchitectureType.BASIC_COT: self.basic_cot_executor,
            ArchitectureType.FULL_COT: self.full_cot_executor,
            ArchitectureType.REACT: self.react_executor,
            ArchitectureType.PLANNER: self.planner_executor
        }
        return executor_map[architecture]
    
    def _track_success(self, complexity: TaskComplexity, architecture: ArchitectureType, successful: bool = True):
        """跟踪策略成功率"""
        if complexity not in self.user_context["successful_strategies"]:
            self.user_context["successful_strategies"][complexity] = {arch_type: 0 for arch_type in ArchitectureType}
        
        if successful:
            self.user_context["successful_strategies"][complexity][architecture] += 1
        else:
            # 失败时减少计数，但不低于0
            current = self.user_context["successful_strategies"][complexity][architecture]
            self.user_context["successful_strategies"][complexity][architecture] = max(0, current - 1)
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算两个字符串的简单相似度"""
        # 这里使用一个简单的方法，实际可以使用更复杂的算法
        s1_words = set(s1.lower().split())
        s2_words = set(s2.lower().split())
        
        if not s1_words or not s2_words:
            return 0.0
            
        intersection = len(s1_words.intersection(s2_words))
        union = len(s1_words.union(s2_words))
        
        return intersection / union if union > 0 else 0.0
    
    def chat_stream(self, user_input: str) -> Generator[str, None, None]:
        """处理用户输入并返回流式响应"""
        try:
            # 任务计数增加
            self.task_counter += 1
            
            # 1. 评估任务复杂度
            complexity = self._evaluate_task_complexity(user_input)
            
            # 2. 选择合适的架构
            architecture = self._select_architecture(complexity)
            
            # 3. 获取对应的执行器
            executor = self._get_executor_for_architecture(architecture)
            
            # 4. 执行流式响应
            streaming_handler = StreamingStdOutCallbackHandler()
            full_response = ""
            success = True
            
            try:
                for chunk in executor.stream({
                    "input": user_input,
                    "chat_history": self.chat_history
                }, config={"callbacks": [streaming_handler]}):
                    if "output" in chunk:
                        # 获取新的文本片段
                        new_text = chunk["output"]
                        if new_text and new_text != full_response:
                            # 只返回新增的部分
                            delta = new_text[len(full_response):]
                            if delta:
                                yield delta
                            full_response = new_text
            except Exception as e:
                error_msg = f"执行失败: {str(e)}"
                yield f"\n{error_msg}\n正在尝试使用更高级的架构..."
                
                # 如果失败，尝试升级到更复杂的架构
                success = False
                if architecture != ArchitectureType.PLANNER:
                    # 获取下一级架构
                    next_architecture = min(ArchitectureType(architecture.value + 1), ArchitectureType.PLANNER)
                    next_executor = self._get_executor_for_architecture(next_architecture)
                    
                    try:
                        result = next_executor.invoke({
                            "input": user_input,
                            "chat_history": self.chat_history
                        })
                        yield f"\n使用高级架构重试成功:\n{result['output']}"
                        full_response = result["output"]
                        # 更新成功策略
                        self._track_success(complexity, next_architecture, True)
                        # 记录当前架构的失败
                        self._track_success(complexity, architecture, False)
                        success = True
                    except Exception as retry_e:
                        yield f"\n高级架构也失败了: {str(retry_e)}"
                        # 记录失败
                        self._track_success(complexity, next_architecture, False)
            
            # 5. 更新聊天历史
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=full_response))
            
            # 6. 跟踪成功率
            if success:
                self.success_counter += 1
                self._track_success(complexity, architecture, True)
            
        except Exception as e:
            error_msg = f"处理请求时发生错误: {str(e)}"
            print(error_msg)
            yield error_msg
    
    def chat(self, user_input: str) -> str:
        """处理用户输入并返回完整响应（非流式）"""
        try:
            # 收集流式响应片段
            full_response = "".join([chunk for chunk in self.chat_stream(user_input)])
            return full_response
        except Exception as e:
            error_msg = f"处理请求时发生错误: {str(e)}"
            print(error_msg)
            return error_msg
    
    def reset_chat(self):
        """重置聊天历史"""
        self.chat_history = []
    
    def set_user_preference(self, complexity_level: Optional[ArchitectureType] = None):
        """设置用户偏好"""
        self.user_context["preferred_complexity_level"] = complexity_level
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        success_rate = self.success_counter / self.task_counter if self.task_counter > 0 else 0
        
        return {
            "total_tasks": self.task_counter,
            "successful_tasks": self.success_counter,
            "success_rate": success_rate,
            "strategy_effectiveness": self.user_context["successful_strategies"]
        }

# 保留原始的MacOSAssistant类以向后兼容
class MacOSAssistant:
    """macOS系统助手主类"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.7,
            streaming=True  # 启用流式响应
        )
        
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
        
        # 创建系统提示
        self.system_prompt = """你是一个macOS系统助手，类似于Windows Copilot。你的主要功能包括：

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

        # 创建提示模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 创建代理
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
        
        # 聊天历史
        self.chat_history = []
    
    def chat_stream(self, user_input: str) -> Generator[str, None, None]:
        """处理用户输入并返回流式响应"""
        try:
            # 创建流式回调处理器
            streaming_handler = StreamingStdOutCallbackHandler()
            
            # 执行代理流式响应
            full_response = ""
            for chunk in self.agent_executor.stream({
                "input": user_input,
                "chat_history": self.chat_history
            }, config={"callbacks": [streaming_handler]}):
                if "output" in chunk:
                    # 获取新的文本片段
                    new_text = chunk["output"]
                    if new_text and new_text != full_response:
                        # 只返回新增的部分
                        delta = new_text[len(full_response):]
                        if delta:
                            yield delta
                        full_response = new_text
            
            # 更新聊天历史
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=full_response))
            
        except Exception as e:
            error_msg = f"处理请求时发生错误: {str(e)}"
            print(error_msg)
            yield error_msg
    
    def chat(self, user_input: str) -> str:
        """处理用户输入并返回完整响应（非流式）"""
        try:
            # 执行代理
            result = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": self.chat_history
            })
            
            # 更新聊天历史
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=result["output"]))
            
            return result["output"]
        except Exception as e:
            error_msg = f"处理请求时发生错误: {str(e)}"
            print(error_msg)
            return error_msg
    
    def reset_chat(self):
        """重置聊天历史"""
        self.chat_history = []

def main():
    """主函数 - 命令行界面"""
    # 使用现有的API密钥
    api_key = "sk-1b53c98a3b8c4abcaa1f68540ab3252d"
    
    print("🤖 macOS系统助手启动中...")
    print("=" * 50)
    
    # 使用增强智能助手
    assistant = IntelligentMacOSAssistant(api_key)
    
    print("✅ 助手已准备就绪！")
    print("💡 你可以询问我关于macOS系统的任何问题")
    print("💡 例如：'打开Safari'、'查看系统信息'、'搜索文件'等")
    print("💡 输入 'quit' 或 'exit' 退出")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            if not user_input:
                continue
            
            print("\n🤖 助手: ", end="", flush=True)
            
            # 使用流式响应
            for chunk in assistant.chat_stream(user_input):
                print(chunk, end="", flush=True)
            
            print()  # 换行
            
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")

if __name__ == "__main__":
    main()
