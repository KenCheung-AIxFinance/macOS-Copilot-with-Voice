import os
import sys
import subprocess
import json
import psutil
import platform
from typing import List, Dict, Any, Optional, Generator, Tuple, Union, Callable
from datetime import datetime
import threading
import time
import re
import enum
import unicodedata

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
from langchain_core.callbacks.base import BaseCallbackHandler

# 全局变量，用于工具访问R1增强器
intelligent_assistant = None

class MacOSTools:
    """macOS系统工具集合"""
    
    # 添加一个类变量存储当前的R1增强器
    r1_enhancer = None
    
    @classmethod
    def set_r1_enhancer(cls, enhancer):
        """设置R1增强器"""
        cls.r1_enhancer = enhancer
    
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
        """增强：支持别名、拼音、英文、中文混输，模糊匹配"""
        try:
            import difflib
            import unicodedata
            # 获取所有已安装应用
            all_apps = MacOSTools._get_all_applications()
            if not all_apps:
                return "无法获取应用程序列表"
            # 别名表
            aliases = {
                'safari': ['safari', '浏览器', 'web', 'sāfārī', 'sfl', '苹果浏览器'],
                'chrome': ['chrome', 'google chrome', '谷歌浏览器', 'gǔgē', '谷歌', 'chromium'],
                'finder': ['finder', '访达', '文件管理器', 'fǎngdá'],
                'terminal': ['terminal', '终端', '命令行', 'zhōngduān'],
                'wechat': ['wechat', '微信', 'wēixìn'],
                'qq': ['qq', '腾讯qq', 'q q'],
                'vscode': ['visual studio code', 'vscode', 'vs code', '代码编辑器'],
                'notes': ['notes', '备忘录', '笔记'],
                'music': ['music', '音乐', 'itunes'],
                'photos': ['photos', '照片', '相册'],
                'mail': ['mail', '邮件', '邮箱'],
                'messages': ['messages', '信息', '短信'],
                'calendar': ['calendar', '日历'],
                'preview': ['preview', '预览'],
                'appstore': ['app store', 'appstore', '应用商店'],
                'reminders': ['reminders', '提醒事项'],
                'calculator': ['calculator', '计算器'],
                'sublime': ['sublime text', 'sublime', '文本编辑器'],
                'bilibili': ['bilibili', 'b站', '哔哩哔哩'],
                'alipay': ['alipay', '支付宝'],
                'taobao': ['taobao', '淘宝'],
                'jd': ['jd', '京东'],
                'netflix': ['netflix', '网飞'],
                'youtube': ['youtube', '油管'],
            }
            # 归一化
            def norm(s):
                return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii').lower()
            app_name_norm = norm(app_name)
            # 先查别名
            for key, alias_list in aliases.items():
                if app_name_norm in [norm(a) for a in alias_list]:
                    for app in all_apps:
                        if norm(app['name']) == norm(key):
                            subprocess.run(['open', app['path']])
                            return f"已打开 {app['name']}"
            # 模糊匹配
            all_names = [app['name'] for app in all_apps]
            matches = difflib.get_close_matches(app_name, all_names, n=1, cutoff=0.6)
            if matches:
                best = next(app for app in all_apps if app['name'] == matches[0])
                subprocess.run(['open', best['path']])
                return f"已打开 {best['name']}"
                return f"未找到匹配的应用程序: {app_name}"
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
        """分步执行&&分割的命令，逐步捕获异常"""
        try:
            dangerous_commands = [
                "rm -rf", "dd if=", "> /dev/", ":(){ :|:& };:",
                "chmod -R 777 /", "mv / /dev/null"
            ]
            for dc in dangerous_commands:
                if dc in command:
                    return f"为安全起见，系统拒绝执行包含 '{dc}' 的命令。请确保您的命令是安全的。"
            # 分步执行
            steps = [c.strip() for c in command.split('&&') if c.strip()]
            output = ""
            for step in steps:
                result = subprocess.run(step, shell=True, capture_output=True, text=True, timeout=10)
                out = result.stdout if result.stdout else ""
                err = result.stderr if result.stderr else ""
                if err:
                    output += f"命令: {step}\n错误: {err}\n"
                    break
                output += out
            return output if output else "命令执行成功"
        except subprocess.TimeoutExpired:
            return "命令超时（执行时间超过10秒）"
        except Exception as e:
            return f"执行命令时出错: {str(e)}"
    
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
        """搜索文件
        
        Args:
            query: 搜索查询
            directory: 搜索目录，默认为/Users
            
        Returns:
            搜索结果
        """
        try:
            # 尝试使用R1增强器进行搜索
            if MacOSTools.r1_enhancer and MacOSTools.r1_enhancer.is_available:
                enhanced_results = MacOSTools.r1_enhancer.enhance_file_search(query, directory)
                if enhanced_results:
                    result_text = "查找到以下文件:\n\n"
                    for item in enhanced_results:
                        result_text += f"{item['path']} (相关度: {item['relevance']})\n"
                    return result_text
            
            # 如果R1增强器不可用或未找到结果，使用基本搜索方法
            result = subprocess.run(["find", directory, "-name", f"*{query}*", "-type", "f"], 
                                   capture_output=True, text=True, timeout=10)
            
            if not result.stdout.strip():
                return f"在{directory}中未找到包含'{query}'的文件"
            
            files = result.stdout.strip().split('\n')
            return f"找到以下文件:\n\n" + '\n'.join(files[:10]) + (f"\n\n共找到{len(files)}个文件，仅显示前10个" if len(files) > 10 else "")
            
        except Exception as e:
            return f"搜索文件时出错: {str(e)}"
    
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
        """创建笔记文件，自动创建父目录，支持~、绝对、相对路径"""
        try:
            import os
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"note_{timestamp}.txt"
            # 展开~
            filepath = os.path.expanduser(filename)
            # 如果不是绝对路径，默认放桌面
            if not os.path.isabs(filepath):
                filepath = os.path.join(os.path.expanduser("~/Desktop"), filepath)
            # 自动创建父目录
            dirpath = os.path.dirname(filepath)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath, exist_ok=True)
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

class EnhancedStreamingHandler(BaseCallbackHandler):
    """增强的流式处理回调处理器
    
    支持以下回调:
    - streaming_callback: 每个token的回调
    - thinking_callback: 思考状态变化的回调
    - start_callback: 开始生成时的回调
    - end_callback: 结束生成时的回调
    - function_call_callback: 函数调用时的回调
    - function_result_callback: 函数返回结果时的回调
    """
    
    def __init__(self, streaming_callback=None, thinking_callback=None, 
                 start_callback=None, end_callback=None,
                 function_call_callback=None, function_result_callback=None):
        """初始化处理器
        
        Args:
            streaming_callback: token回调函数
            thinking_callback: 思考状态回调函数
            start_callback: 开始回调函数
            end_callback: 结束回调函数
            function_call_callback: 函数调用回调
            function_result_callback: 函数结果回调
        """
        self.streaming_callback = streaming_callback
        self.thinking_callback = thinking_callback
        self.start_callback = start_callback
        self.end_callback = end_callback
        self.function_call_callback = function_call_callback
        self.function_result_callback = function_result_callback
        
        # 内部状态
        self.response_started = False
        self.is_thinking = False
        self.current_token_buffer = ""
        self.thinking_buffer = ""
        self.thinking_markers = [
            "思考中", "让我思考", "分析一下", "思考:", "思考：",
            "分析:", "分析：", "让我想一想", "考虑一下", "推理:"
        ]
        
    def on_function_call(self, function_name, arguments):
        """函数调用时的回调
        
        Args:
            function_name: 函数名称
            arguments: 函数参数
        """
        # 如果之前在思考状态，退出思考状态
        if self.is_thinking:
            self.is_thinking = False
            if self.thinking_callback:
                self.thinking_callback(False)
                
        if self.function_call_callback:
            self.function_call_callback(function_name, arguments)
            
    def on_function_result(self, result):
        """函数返回结果时的回调
        
        Args:
            result: 函数返回结果
        """
        if self.function_result_callback:
            self.function_result_callback(result)
    
    def on_llm_start(self, *args, **kwargs):
        """LLM开始生成时的回调"""
        if self.start_callback:
            self.start_callback()
    
    def on_llm_new_token(self, token: str, **kwargs):
        """接收新token时的回调"""
        # 检测和处理思考模式
        if not self.response_started and token.strip():
            self.response_started = True
        
        # 更精确地检测思考状态
        # 检查是否进入思考状态
        if not self.is_thinking:
            # 将当前缓冲区与新token组合起来检查
            check_text = self.current_token_buffer + token
            if any(marker in check_text for marker in self.thinking_markers):
                self.is_thinking = True
                self.thinking_buffer = check_text  # 将当前文本作为思考的起始
                if self.thinking_callback:
                    self.thinking_callback(True)
                return
        
        # 如果是思考状态，将token加入思考缓冲区
        if self.is_thinking:
            self.thinking_buffer += token
            
            # 检查是否退出思考状态（识别思考结束标记）
            end_markers = ["结论:", "结论：", "回应:", "回应：", "回答:", 
                           "回答：", "总结:", "总结：", "因此,", "因此，"]
            if any(marker in self.thinking_buffer[-20:] for marker in end_markers):
                self.is_thinking = False
                if self.thinking_callback:
                    self.thinking_callback(False)
            
            # 在思考状态下不发送token给streaming_callback
            return
        
        # 缓冲和处理非思考状态的token
        self.current_token_buffer += token
        
        # 当缓冲区包含完整词或标点时才发送
        if (len(self.current_token_buffer) > 5 or 
            any(p in self.current_token_buffer for p in [" ", ".", ",", "!", "?", "\n"])):
            if self.streaming_callback:
                self.streaming_callback(self.current_token_buffer)
            self.current_token_buffer = ""
    
    def on_llm_end(self, *args, **kwargs):
        """LLM结束生成时的回调"""
        # 发送任何剩余的缓冲区内容
        if self.current_token_buffer and self.streaming_callback:
            self.streaming_callback(self.current_token_buffer)
            self.current_token_buffer = ""
        
        # 结束思考模式(如果仍在思考)
        if self.is_thinking and self.thinking_callback:
            self.is_thinking = False
            self.thinking_callback(False)
        
        # 调用结束回调
        if self.end_callback:
            self.end_callback()
            
        # 重置状态
        self.response_started = False
        self.thinking_buffer = ""

class DeepSeekR1Enhancer:
    """DeepSeek R1模型增强器
    
    用于在特定复杂场景下使用DeepSeek R1模型提高系统智能度
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """初始化R1增强器
        
        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        
        # 创建R1模型LLM (温度较低以提高准确性)
        try:
            self.r1_llm = ChatOpenAI(
                model="deepseek-reasoner",  # deepseek-reasoner模型(推理增强型)
                openai_api_key=api_key,
                openai_api_base=base_url,
                temperature=0.3,  # 较低的温度以获得更确定性的回答
                streaming=True
            )
            self.is_available = True
        except Exception as e:
            print(f"初始化DeepSeek Reasoner模型失败: {str(e)}")
            self.is_available = False
    
    def is_complex_technical_query(self, query: str) -> bool:
        """判断是否为复杂技术查询
        
        Args:
            query: 用户输入
            
        Returns:
            是否为复杂技术查询
        """
        # 复杂技术查询关键词
        technical_keywords = [
            "编译", "内核", "驱动程序", "文件系统", "进程管理", 
            "内存管理", "网络协议", "安全漏洞", "性能优化",
            "系统架构", "代码分析", "调试", "异常处理", 
            "集成", "API接口", "数据库", "缓存", "并发", 
            "线程", "同步", "异步", "脚本自动化"
        ]
        
        # 检查是否包含技术关键词
        for keyword in technical_keywords:
            if keyword in query:
                return True
                
        # 检查是否为长查询(长查询可能更复杂)
        if len(query) > 100:
            return True
            
        return False
    
    def enhance_complexity_evaluation(self, user_input: str, original_complexity: TaskComplexity) -> TaskComplexity:
        """增强任务复杂度评估
        
        Args:
            user_input: 用户输入
            original_complexity: 原始复杂度评估
            
        Returns:
            增强后的复杂度评估
        """
        if not self.is_available:
            return original_complexity
            
        # 对特定场景使用更精确的复杂度评估
        if self.is_complex_technical_query(user_input):
            try:
                complexity_prompt = """
请评估以下macOS相关任务的复杂度，并返回相应的复杂度级别编号:
1 = 简单任务 (直接查询、单一操作，如查看时间、打开应用)
2 = 中等任务 (2-3步操作，有条件判断，如查找特定文件) 
3 = 复杂任务 (多步骤，需要推理，系统诊断，如解决问题)
4 = 高级任务 (创造性解决方案，复杂诊断，自适应执行)

深入分析考虑:
- 任务涉及到的系统组件数量
- 需要的操作步骤
- 是否需要专业知识
- 是否需要处理异常情况
- 是否需要定制化解决方案

只返回一个数字，不要解释。用户任务："{user_input}"
"""
                result = self.r1_llm.invoke(complexity_prompt.format(user_input=user_input))
                complexity_text = result.content.strip()
                
                # 提取数字
                if '1' in complexity_text:
                    return TaskComplexity.SIMPLE
                elif '2' in complexity_text:
                    return TaskComplexity.MEDIUM
                elif '3' in complexity_text:
                    return TaskComplexity.COMPLEX
                else:
                    return TaskComplexity.ADVANCED
            except:
                return original_complexity
        
        return original_complexity
    
    def generate_advanced_plan(self, user_input: str) -> str:
        """使用R1模型生成高级执行计划
        
        Args:
            user_input: 用户输入
            
        Returns:
            详细的执行计划
        """
        if not self.is_available:
            return ""
            
        try:
            planning_prompt = f"""
针对用户在macOS环境下的以下请求，制定一个详细的执行计划:

用户请求: {user_input}

请提供以下内容的有结构的执行计划:
1. 任务分解: 将主要任务分解为具体子任务
2. 工具选择: 每个子任务使用哪些macOS命令行工具或系统API
3. 执行顺序: 子任务的最佳执行顺序
4. 潜在问题: 可能遇到的问题和解决方案

非常重要: 请以清晰的段落和结构返回，使用明确的标题分隔不同部分。
"""
            result = self.r1_llm.invoke(planning_prompt)
            plan_text = result.content
            
            # 格式化执行计划，确保有清晰的结构
            formatted_plan = "【执行计划】\n"
            formatted_plan += "-" * 40 + "\n"
            
            # 尝试识别计划中的各个部分并格式化
            sections = ["任务分解", "工具选择", "执行顺序", "潜在问题"]
            current_section = ""
            
            for line in plan_text.split('\n'):
                # 检查行是否是新的节标题
                is_section_header = False
                for section in sections:
                    if section in line and (":" in line or "：" in line or "#" in line or "步骤" in line):
                        current_section = section
                        formatted_plan += f"\n● {line.strip()}\n"
                        is_section_header = True
                        break
                
                if not is_section_header and line.strip():
                    if current_section:
                        formatted_plan += f"  {line.strip()}\n"
                    else:
                        formatted_plan += f"{line.strip()}\n"
            
            formatted_plan += "-" * 40
            return formatted_plan
        except Exception as e:
            print(f"生成高级计划失败: {str(e)}")
            return ""
    
    def optimize_system_command(self, command: str) -> str:
        """优化系统命令
        
        Args:
            command: 原始命令
            
        Returns:
            优化后的命令
        """
        if not self.is_available or not command:
            return command
            
        try:
            optimization_prompt = f"""
请优化以下macOS终端命令，提高其效率、安全性和可靠性:

原始命令: {command}

请考虑:
1. 安全性改进 (避免潜在风险或数据损失)
2. 效率优化 (更快执行或使用更高效的选项)
3. 错误处理 (添加错误检测或条件执行)
4. 可读性 (如果有助于维护但不影响功能)

只返回优化后的命令，不要解释。如果原命令已经最优，则返回原命令。
"""
            result = self.r1_llm.invoke(optimization_prompt)
            optimized = result.content.strip()
            
            # 如果优化结果为空或异常，返回原命令
            if not optimized or len(optimized) < len(command) / 2:
                return command
                
            return optimized
        except:
            return command
    
    def analyze_error(self, error_message: str, original_command: str) -> Dict[str, str]:
        """分析错误并提供修复建议
        
        Args:
            error_message: 错误消息
            original_command: 导致错误的原始命令
            
        Returns:
            包含错误分析和修复建议的字典
        """
        if not self.is_available:
            return {"analysis": "", "fix": ""}
            
        try:
            error_prompt = f"""
分析以下在macOS终端执行命令时遇到的错误，并提供修复建议:

原始命令: {original_command}
错误消息: {error_message}

请提供:
1. 简洁的错误根本原因分析
2. 推荐的修复命令

以JSON格式回答，包含两个字段: "analysis"和"fix"
"""
            result = self.r1_llm.invoke(error_prompt)
            
            # 尝试从回复中提取JSON
            content = result.content
            try:
                import json
                # 查找JSON内容
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    return json.loads(json_str)
            except:
                # 如果JSON解析失败，手动提取关键内容
                analysis = ""
                fix = ""
                
                if "分析" in content or "原因" in content:
                    analysis_start = content.find("分析") if "分析" in content else content.find("原因")
                    analysis_end = content.find("修复") if "修复" in content else len(content)
                    analysis = content[analysis_start:analysis_end].strip()
                
                if "修复" in content or "建议" in content:
                    fix_start = content.find("修复") if "修复" in content else content.find("建议")
                    fix_end = len(content)
                    fix = content[fix_start:fix_end].strip()
                    
                    # 尝试提取命令
                    if "`" in fix:
                        start_cmd = fix.find("`")
                        end_cmd = fix.find("`", start_cmd + 1)
                        if end_cmd > start_cmd:
                            fix = fix[start_cmd+1:end_cmd]
                
                return {"analysis": analysis, "fix": fix}
                
            return {"analysis": "无法分析错误", "fix": ""}
        except Exception as e:
            print(f"分析错误失败: {str(e)}")
            return {"analysis": "", "fix": ""}
    
    def enhance_file_search(self, query: str, directory: str) -> List[Dict[str, str]]:
        """增强文件搜索功能
        
        Args:
            query: 搜索查询
            directory: 搜索目录
            
        Returns:
            增强的搜索结果
        """
        if not self.is_available:
            return []
            
        try:
            # 使用R1模型生成更智能的搜索命令
            search_prompt = f"""
为在macOS上查找以下文件，生成一个高效、准确的find或mdfind命令:

搜索查询: {query}
搜索目录: {directory}

考虑:
1. 根据查询特点选择合适的搜索工具(find适合精确路径搜索，mdfind适合内容搜索)
2. 加入适当的过滤条件(文件类型、大小、修改时间等)
3. 排序方式(最近修改、名称相关性等)
4. 搜索深度限制(避免过深遍历)

只返回一个完整的命令，不要解释。
"""
            result = self.r1_llm.invoke(search_prompt)
            search_command = result.content.strip()
            
            if not search_command or len(search_command) < 10:
                return []
                
            # 提取实际命令(如果有代码块标记)
            if "```" in search_command:
                parts = search_command.split("```")
                for part in parts:
                    if part.strip() and not part.startswith("bash") and not part.startswith("sh"):
                        search_command = part.strip()
                        break
            
            # 执行搜索命令并解析结果
            import subprocess
            try:
                result = subprocess.run(search_command, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    files = result.stdout.strip().split('\n')
                    enhanced_results = []
                    
                    for file in files[:10]:  # 限制为前10个结果
                        if file.strip():
                            enhanced_results.append({
                                "path": file.strip(),
                                "relevance": "高"  # 可以进一步改进相关性评分
                            })
                    
                    return enhanced_results
            except:
                pass
                
        except Exception as e:
            print(f"增强文件搜索失败: {str(e)}")
            
        return []

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
        try:
            # 首先检查是否已有相似请求的复杂度评估
            for task, complexity in self.user_context["common_tasks"].items():
                if self._calculate_similarity(task, user_input) > 0.8:  # 80%相似度阈值
                    return complexity
            
            # 使用基本方法评估任务复杂度
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
                    initial_complexity = TaskComplexity.SIMPLE
                    break
            else:
                for pattern in medium_patterns:
                    if re.search(pattern, user_input):
                        initial_complexity = TaskComplexity.MEDIUM
                        break
                else:
                    for pattern in complex_patterns:
                        if re.search(pattern, user_input):
                            initial_complexity = TaskComplexity.COMPLEX
                            break
                    else:
                        for pattern in advanced_patterns:
                            if re.search(pattern, user_input):
                                initial_complexity = TaskComplexity.ADVANCED
                                break
                        else:
                            # 使用LLM评估复杂度
                            complexity_prompt = """
请评估以下用户请求的复杂度，并返回相应的复杂度级别编号:
1 = 简单任务 (直接查询、单一操作，如查看时间、打开应用)
2 = 中等任务 (2-3步操作，有条件判断，如查找特定文件) 
3 = 复杂任务 (多步骤，需要推理，系统诊断，如解决问题)
4 = 高级任务 (创造性解决方案，复杂诊断，自适应执行)

只返回一个数字，不要解释。用户请求："{user_input}"
"""
                            result = self.llm.invoke(complexity_prompt.format(user_input=user_input))
                            complexity_text = result.content.strip()
                            
                            # 提取数字
                            if '1' in complexity_text:
                                initial_complexity = TaskComplexity.SIMPLE
                            elif '2' in complexity_text:
                                initial_complexity = TaskComplexity.MEDIUM
                            elif '3' in complexity_text:
                                initial_complexity = TaskComplexity.COMPLEX
                            else:
                                initial_complexity = TaskComplexity.ADVANCED
            
            # 使用R1增强器进一步评估复杂度
            final_complexity = self.r1_enhancer.enhance_complexity_evaluation(
                user_input, initial_complexity
            )
            
            # 保存到用户上下文
            self.user_context["common_tasks"][user_input] = final_complexity
            return final_complexity
            
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
        """获取指定架构类型的执行器，对于复杂架构进行R1增强"""
        executor_map = {
            ArchitectureType.DIRECT: self.direct_executor,
            ArchitectureType.BASIC_COT: self.basic_cot_executor,
            ArchitectureType.FULL_COT: self.full_cot_executor,
            ArchitectureType.REACT: self.react_executor,
            ArchitectureType.PLANNER: self.planner_executor
        }
        
        executor = executor_map[architecture]
        
        # 对于PLANNER和REACT架构，可以考虑使用R1增强器
        if architecture in [ArchitectureType.PLANNER, ArchitectureType.REACT] and self.r1_enhancer.is_available:
            # 这里不直接修改执行器，而是记录使用R1增强器的标志
            # 实际增强会在chat_stream和stream_with_handler中进行
            self.use_r1_enhancement = True
        else:
            self.use_r1_enhancement = False
            
        return executor
    
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
        """根据用户输入生成流式AI响应
        
        使用智能任务复杂度评估和架构选择流水线处理用户请求
        如果遇到错误，会自动尝试使用更复杂的架构模型重试
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            生成文本块的生成器
        """
        try:
            # 任务计数增加
            self.task_counter += 1
            
            # 1. 评估任务复杂度
            complexity = self._evaluate_task_complexity(user_input)
            yield f"【评估复杂度】{complexity.name}\n"
            
            # 2. 选择合适的架构
            architecture = self._select_architecture(complexity)
            yield f"【选择架构】{architecture.name}\n"
            
            # 3. 获取对应的执行器
            executor = self._get_executor_for_architecture(architecture)
            
            # 4. 对于复杂任务，使用R1增强器生成高级执行计划
            enhanced_input = user_input
            plan = None
            if self.use_r1_enhancement and complexity in [TaskComplexity.COMPLEX, TaskComplexity.ADVANCED]:
                yield "【生成执行计划】\n"
                plan = self.r1_enhancer.generate_advanced_plan(user_input)
                if plan:
                    yield f"{plan}\n"
                    enhanced_input = f"{user_input}\n\n[系统提示：参考以下执行计划]\n{plan}"
            # 5. Planner架构下自动执行计划
            if architecture == ArchitectureType.PLANNER and plan:
                yield "【自动执行计划】\n"
                exec_results = self.execute_plan(plan)
                for idx, r in enumerate(exec_results, 1):
                    yield f"步骤{idx}: {r['task']}\n调用工具: {r['tool']}\n参数: {r['params']}\n结果: {r['result']}\n\n"
                yield "【计划执行完毕】\n"
                full_response = "\n".join([str(r['result']) for r in exec_results])
                # 6. 更新聊天历史
                self.chat_history.append(HumanMessage(content=user_input))
                self.chat_history.append(AIMessage(content=full_response))
                return
            
            # 5. 执行流式响应
            buffer = []  # 用于存储收到的令牌
            full_response = ""
            success = True
            is_thinking = False
            thinking_content = ""
            response_queue = []  # 用于存储需要yield的内容
            is_framework_output = False  # 用于标记框架输出
            has_shown_final_response = False  # 标记是否已显示最终回答标题
            
            # 重置函数调用结果计数
            self.function_results = []
            
            # 定义Token处理回调函数
            def token_callback(token):
                nonlocal buffer, thinking_content, is_thinking, is_framework_output
                if token:
                    # 检查是否是框架输出
                    if "> Entering new" in token or "Finished chain" in token:
                        is_framework_output = True
                        return
                        
                    # 如果之前是框架输出，检查是否已结束框架输出
                    if is_framework_output:
                        # 如果有明确的非框架输出标记，结束框架输出模式
                        if "【" in token or "调用工具" in token or "返回数据" in token:
                            is_framework_output = False
                        else:
                            return  # 继续忽略框架输出
                            
                    # 处理思考内容或正常输出
                    if is_thinking:
                        thinking_content += token
                    else:
                        buffer.append(token)  # 添加令牌到缓冲区
                    return token  # 返回令牌以供后续处理
            
            # 处理思考状态变化
            def handle_thinking_state(thinking):
                nonlocal is_thinking, thinking_content, response_queue
                is_thinking = thinking
                if thinking:
                    response_queue.append("\n\n🧠 【思考过程】\n")
                else:
                    if thinking_content.strip():
                        response_queue.append(f"{thinking_content}\n")
                        # 在思考结束后添加最终回答标记
                        response_queue.append("\n\n📝 【最终回答】\n")
                    thinking_content = ""
            
            # 处理函数调用
            def handle_function_call(name, args):
                nonlocal response_queue
                args_str = json.dumps(args, ensure_ascii=False, indent=2) if args else ""
                response_queue.append(f"\n\n🔧 【工具调用】{name}\n")
                if args_str:
                    response_queue.append(f"参数：{args_str}\n")
            
            # 处理函数返回结果
            def handle_function_result(result):
                nonlocal response_queue
                # 使用self的属性而不是nonlocal变量
                self.function_results.append(result)
                response_queue.append(f"\n📊 【工具返回 #{len(self.function_results)}】\n")
                for line in result.strip().split('\n'):
                    response_queue.append(f"  {line}\n")
            
            # 创建增强的流式处理器
            streaming_handler = EnhancedStreamingHandler(
                streaming_callback=token_callback,
                thinking_callback=handle_thinking_state,
                function_call_callback=handle_function_call,
                function_result_callback=handle_function_result
            )
            
            try:
                # 设置流式响应配置
                stream_config = {"callbacks": [streaming_handler]}
                
                # 仅在开始时添加一个标记，避免占用太多空间
                yield "\n【开始处理请求】\n"
                
                # 初始时添加最终回答标记，仅当没有思考过程时使用
                final_response_marked = False
                
                for chunk in executor.stream({
                    "input": enhanced_input,
                    "chat_history": self.chat_history
                }, config=stream_config):
                    # 首先处理queue中的响应
                    while response_queue:
                        item = response_queue.pop(0)
                        # 检查是否为最终回答标记
                        if "【最终回答】" in item:
                            final_response_marked = True
                        yield item
                        
                    if "output" in chunk:
                        # 获取新的文本片段
                        new_text = chunk["output"]
                        if new_text and new_text != full_response:
                            # 只返回新增的部分
                            delta = new_text[len(full_response):]
                            full_response = new_text
                            if delta and not is_thinking:
                                # 如果没有任何标记，添加一个最终回答标记
                                if not final_response_marked and not has_shown_final_response:
                                    has_shown_final_response = True
                                    yield "\n\n📝 【最终回答】\n"
                                    final_response_marked = True
                                yield delta
                            
                            # 处理缓冲区中的任何令牌
                            while buffer and not is_thinking:
                                token = buffer.pop(0)
                                if token:  # 避免空令牌
                                    yield token
                
                # 处理任何剩余的response_queue内容
                while response_queue:
                    item = response_queue.pop(0)
                    if "【最终回答】" in item:
                        final_response_marked = True
                    yield item
                    
                # 处理任何剩余的缓冲区内容
                while buffer and not is_thinking:
                    token = buffer.pop(0)
                    if token:
                        yield token
                
                # 只在最后输出一次处理完成
                tool_count = len(self.function_results)
                yield f"\n\n{'-' * 40}\n"
                yield f"✅ 处理完成 | 共调用 {tool_count} 个工具\n"
                yield f"{'-' * 40}\n"
                
            except Exception as e:
                error_msg = f"执行失败: {str(e)}"
                yield f"\n【错误】{error_msg}\n正在尝试使用更高级的架构...\n"
                
                # 如果失败，尝试使用R1增强器分析错误
                error_analysis = self.r1_enhancer.analyze_error(str(e), user_input)
                if error_analysis["analysis"] or error_analysis["fix"]:
                    yield f"\n【错误分析】{error_analysis['analysis']}\n"
                    if error_analysis["fix"]:
                        yield f"\n【修复建议】{error_analysis['fix']}\n"
                
                # 尝试升级到更复杂的架构
                success = False
                if architecture != ArchitectureType.PLANNER:
                    # 获取下一级架构
                    next_architecture = min(ArchitectureType(architecture.value + 1), ArchitectureType.PLANNER)
                    next_executor = self._get_executor_for_architecture(next_architecture)
                    
                    try:
                        yield f"\n【尝试架构】{next_architecture.name}\n"
                        result = next_executor.invoke({
                            "input": enhanced_input,
                            "chat_history": self.chat_history
                        })
                        yield f"\n【重试成功】\n{result['output']}\n"
                        full_response = result["output"]
                        # 更新成功策略
                        self._track_success(complexity, next_architecture, True)
                        # 记录当前架构的失败
                        self._track_success(complexity, architecture, False)
                        success = True
                    except Exception as retry_e:
                        yield f"\n【重试失败】{str(retry_e)}\n"
                        # 记录失败
                        self._track_success(complexity, next_architecture, False)
            
            # 6. 更新聊天历史
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=full_response))
            
            # 7. 跟踪成功率
            if success:
                self.success_counter += 1
                self._track_success(complexity, architecture, True)
            
        except Exception as e:
            error_msg = f"处理请求时发生错误: {str(e)}"
            print(error_msg)
            yield f"\n【系统错误】{error_msg}\n"
    
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
    
    def stream_with_handler(self, user_input: str, custom_handler) -> Generator[str, None, None]:
        """使用自定义处理器的流式输出，支持R1增强"""
        try:
            # 任务计数增加
            self.task_counter += 1
            
            # 1. 评估任务复杂度
            complexity = self._evaluate_task_complexity(user_input)
            
            # 2. 选择合适的架构
            architecture = self._select_architecture(complexity)
            
            # 3. 获取对应的执行器
            executor = self._get_executor_for_architecture(architecture)
            
            # 4. 对于复杂任务，使用R1增强器生成高级执行计划
            enhanced_input = user_input
            plan = None
            if self.use_r1_enhancement and complexity in [TaskComplexity.COMPLEX, TaskComplexity.ADVANCED]:
                yield "【生成执行计划】\n"
                plan = self.r1_enhancer.generate_advanced_plan(user_input)
                if plan:
                    yield f"{plan}\n"
                    enhanced_input = f"{user_input}\n\n[系统提示：参考以下执行计划]\n{plan}"
            # 5. Planner架构下自动执行计划
            if architecture == ArchitectureType.PLANNER and plan:
                yield "【自动执行计划】\n"
                exec_results = self.execute_plan(plan)
                for idx, r in enumerate(exec_results, 1):
                    yield f"步骤{idx}: {r['task']}\n调用工具: {r['tool']}\n参数: {r['params']}\n结果: {r['result']}\n\n"
                yield "【计划执行完毕】\n"
                full_response = "\n".join([str(r['result']) for r in exec_results])
                # 6. 更新聊天历史
                self.chat_history.append(HumanMessage(content=user_input))
                self.chat_history.append(AIMessage(content=full_response))
                return
            
            # 5. 执行流式响应
            full_response = ""
            success = True
            
            # 记录函数调用
            function_calls = []
            
            # 增加函数调用拦截
            class FunctionCallTracker(BaseCallbackHandler):
                def __init__(self):
                    self.function_calls = []
                    self.last_args = {}
                    self.last_results = {}
                    
                def on_tool_start(self, serialized, input_str, **kwargs):
                    # 记录工具调用开始
                    tool_name = serialized.get("name", "未知工具")
                    self.last_args[tool_name] = input_str
                    if hasattr(custom_handler, "on_function_call") and callable(custom_handler.on_function_call):
                        try:
                            # 转换输入为参数字典
                            args = json.loads(input_str) if isinstance(input_str, str) and input_str.strip().startswith("{") else {"input": input_str}
                            custom_handler.on_function_call(tool_name, args)
                        except:
                            pass
                    
                def on_tool_end(self, output, **kwargs):
                    # 记录工具调用结束及其结果
                    if hasattr(custom_handler, "on_function_result") and callable(custom_handler.on_function_result):
                        try:
                            custom_handler.on_function_result(output)
                        except:
                            pass
            
            # 创建函数调用跟踪器
            function_tracker = FunctionCallTracker()
            
            try:
                # 使用自定义处理器
                stream_config = {"callbacks": [custom_handler, function_tracker]}
                
                for chunk in executor.stream({
                    "input": enhanced_input,
                    "chat_history": self.chat_history
                }, config=stream_config):
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
                
                # 如果失败，尝试使用R1增强器分析错误
                error_analysis = self.r1_enhancer.analyze_error(str(e), user_input)
                if error_analysis["analysis"] or error_analysis["fix"]:
                    yield f"\n错误分析: {error_analysis['analysis']}"
                    if error_analysis["fix"]:
                        yield f"\n修复建议: {error_analysis['fix']}"
                
                # 尝试升级到更复杂的架构
                success = False
                if architecture != ArchitectureType.PLANNER:
                    # 获取下一级架构
                    next_architecture = min(ArchitectureType(architecture.value + 1), ArchitectureType.PLANNER)
                    next_executor = self._get_executor_for_architecture(next_architecture)
                    
                    try:
                        result = next_executor.invoke({
                            "input": enhanced_input,
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
            
            # 6. 更新聊天历史
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=full_response))
            
            # 7. 跟踪成功率
            if success:
                self.success_counter += 1
                self._track_success(complexity, architecture, True)
            
        except Exception as e:
            error_msg = f"处理请求时发生错误: {str(e)}"
            print(error_msg)
            yield error_msg

    def map_task_to_tool(self, task_text: str):
        """将自然语言任务映射到合适的tool及参数"""
        # 关键词与tool映射表
        mapping = [
            (r"创建文件夹|新建文件夹|建立文件夹|mkdir", MacOSTools.execute_terminal_command, lambda t: {"command": f"mkdir -p '{self._extract_path(t)}'"}),
            (r"写文件|创建文件|新建文件|保存内容", MacOSTools.execute_terminal_command, lambda t: {"command": f"echo '{self._extract_content(t)}' > '{self._extract_path(t)}'"}),
            (r"打开应用|启动应用|运行应用|open", MacOSTools.open_application, lambda t: {"app_name": self._extract_app_name(t)}),
            (r"网络信息|网络状态|网络连接|ip|ifconfig", MacOSTools.get_network_info, lambda t: {}),
            (r"系统信息|系统状态|硬件信息", MacOSTools.get_system_info, lambda t: {}),
            (r"电池信息|电量|电池状态", MacOSTools.get_battery_info, lambda t: {}),
            (r"进程|运行程序|进程列表", MacOSTools.get_running_processes, lambda t: {}),
            (r"搜索文件|查找文件|find|mdfind", MacOSTools.search_files, lambda t: {"query": self._extract_query(t)}),
            (r"音量|设置音量|调整音量", MacOSTools.set_system_volume, lambda t: {"volume": self._extract_volume(t)}),
            (r"当前时间|现在几点|时间", MacOSTools.get_current_time, lambda t: {}),
            (r"已安装应用|应用列表|列出应用", MacOSTools.get_installed_applications, lambda t: {}),
            (r"创建笔记|写笔记|保存笔记", MacOSTools.create_note, lambda t: {"content": self._extract_content(t)}),
        ]
        for pattern, tool, param_fn in mapping:
            if re.search(pattern, task_text, re.I):
                try:
                    params = param_fn(task_text)
                except Exception:
                    params = {}
                return tool, params
        # 默认尝试用终端命令
        return MacOSTools.execute_terminal_command, {"command": task_text}

    def _extract_path(self, text):
        # 简单提取路径
        m = re.search(r"(?:到|在|于|到达)?([~/\w\-./]+)", text)
        return m.group(1) if m else "~/Desktop/auto_folder"
    def _extract_content(self, text):
        m = re.search(r"内容为([\s\S]+)", text)
        return m.group(1).strip() if m else "自动生成内容"
    def _extract_app_name(self, text):
        m = re.search(r"打开(.*?)(?:应用|$)", text)
        return m.group(1).strip() if m else text.strip()
    def _extract_query(self, text):
        m = re.search(r"搜索(.*?)(?:文件|$)", text)
        return m.group(1).strip() if m else text.strip()
    def _extract_volume(self, text):
        m = re.search(r"(\d{1,3})%?", text)
        try:
            v = int(m.group(1))
            return min(max(v, 0), 100)
        except:
            return 50

    def llm_map_task_to_tool(self, task_text: str):
        """优先用LLM做mapping，失败时fallback到原有mapping"""
        prompt = f"""
你有如下工具可用：
1. open_application(app_name)
2. execute_terminal_command(command)
3. create_note(content, filename)
4. get_network_info()
5. get_system_info()
6. get_battery_info()
7. get_running_processes()
8. search_files(query)
9. set_system_volume(volume)
10. get_current_time()
11. get_installed_applications()
用户请求：{task_text}
请判断应该调用哪个工具，并给出参数，返回JSON格式：{{"tool": "...", "params": {{...}}}}
"""
        try:
            result = self.llm.invoke(prompt)
            data = json.loads(result.content)
            tool = getattr(MacOSTools, data["tool"])
            params = data["params"]
            return tool, params
        except Exception:
            return self.map_task_to_tool(task_text)

    def execute_plan(self, plan_text: str):
        """支持LLM结构化tool序列和普通文本计划"""
        # 1. 优先尝试LLM结构化输出
        plan_prompt = f"""
用户请求：{plan_text}
请将任务分解为一系列工具调用，输出JSON数组，每个元素形如：{{"tool": "...", "params": {{...}}}}
"""
        try:
            result = self.llm.invoke(plan_prompt)
            plan_data = json.loads(result.content)
            if isinstance(plan_data, list):
                results = []
                for step in plan_data:
                    tool = getattr(MacOSTools, step["tool"], None)
                    params = step.get("params", {})
                    if tool:
                        try:
                            res = tool(**params)
                        except Exception as e:
                            res = f"工具调用失败: {str(e)}"
                        results.append({"task": step, "tool": tool.__name__, "params": params, "result": res})
                return results
        except Exception:
            pass
        # fallback到原有文本解析
        tasks = self._parse_plan_to_tasks(plan_text)
        results = []
        for task in tasks:
            tool, params = self.llm_map_task_to_tool(task)
            try:
                result = tool(**params)
            except Exception as e:
                result = f"工具调用失败: {str(e)}"
            results.append({"task": task, "tool": tool.__name__, "params": params, "result": result})
        return results

    def _parse_plan_to_tasks(self, plan_text: str):
        """简单按行/序号/分段提取子任务"""
        # 支持1. 2. 3.、-、●、换行等
        lines = re.split(r"\n|\d+\. |\-|●|\u2022", plan_text)
        tasks = [l.strip() for l in lines if l.strip() and len(l.strip()) > 3]
        return tasks

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
            # 创建增强的流式处理器和令牌缓冲区
            buffer = []
            
            # 定义Token处理回调
            def token_callback(token):
                if token:
                    buffer.append(token)
                    return token
            
            # 创建处理器
            streaming_handler = EnhancedStreamingHandler(
                streaming_callback=token_callback
            )
            
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
                        
                        # 处理缓冲区中的标记
                        while buffer:
                            token = buffer.pop(0)
                            if token:
                                yield token
                        
                        full_response = new_text
            
            # 处理任何剩余的缓冲区内容
            while buffer:
                token = buffer.pop(0)
                if token:
                    yield token
            
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

    def stream_with_handler(self, user_input: str, custom_handler) -> Generator[str, None, None]:
        """使用自定义处理器的流式输出
        
        Args:
            user_input: 用户输入文本
            custom_handler: 自定义回调处理器(EnhancedStreamingHandler实例)
            
        Returns:
            生成文本块的生成器
        """
        try:
            # 执行代理流式响应
            full_response = ""
            
            # 使用自定义处理器
            for chunk in self.agent_executor.stream({
                "input": user_input,
                "chat_history": self.chat_history
            }, config={"callbacks": [custom_handler]}):
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

def main():
    """主函数 - 命令行界面"""
    global intelligent_assistant
    
    # 使用现有的API密钥
    api_key = "sk-1b53c98a3b8c4abcaa1f68540ab3252d"
    if not api_key:
        print("请设置OPENAI_API_KEY环境变量")
        sys.exit(1)
    
    print("\n🤖 macOS系统助手启动中...")
    print("=" * 60)
    print("版本: 1.2.0 (DeepSeek Reasoner增强)")
    print("最后更新: " + datetime.now().strftime("%Y-%m-%d"))
    print("=" * 60)
    
    # 初始化智能助手
    try:
        # 使用增强智能助手
        print("\n[系统初始化] 正在初始化智能助手...")
        intelligent_assistant = IntelligentMacOSAssistant(api_key)
        
        # 简单测试
        print("[系统初始化] 测试助手功能...", end="", flush=True)
        # result = intelligent_assistant.chat("获取当前时间")  # TEST
        print(" 完成!")
        print("\n✅ 助手已准备就绪！\n")
    except Exception as e:
        print(f"\n[系统初始化] 初始化智能助手失败: {str(e)}")
        print("[系统初始化] 正在回退到基础助手...", end="", flush=True)
        intelligent_assistant = MacOSAssistant(api_key)
        print(" 完成!")
        print("\n✅ 基础助手已准备就绪！\n")
    
    print("\n💡 使用指南:")
    print("  • 你可以询问关于macOS系统的任何问题")
    print("  • 例如：'打开Safari'、'查看系统信息'、'搜索文件'等")
    print("  • 输入 'quit' 或 'exit' 退出")
    print("\n" + "=" * 60)
    
    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n👋 再见！")
                break
            
            if not user_input:
                continue
            
            print("\n" + "=" * 60)
            print("🔄 开始处理请求...")
            
            # 记录函数调用和结果的变量
            function_calls = []
            function_results = []
            thinking_content = ""
            final_response = ""
            is_collecting_thinking = False
            is_chain_output = False  # 用于标记LangChain框架的输出
            has_shown_final_response_header = False  # 用于标记是否已显示最终回答标题
            
            # 使用流式响应
            # 创建自定义处理器
            def on_token(token):
                nonlocal final_response, thinking_content, is_collecting_thinking, is_chain_output, has_shown_final_response_header
                
                # 检查是否是LangChain框架的输出
                if "> Entering new" in token or "Finished chain" in token:
                    is_chain_output = True
                    return
                
                # 如果是思考内容，收集到thinking_content
                if is_collecting_thinking:
                    thinking_content += token
                elif not is_chain_output:  # 只有非框架输出才添加到最终响应
                    # 检查是否需要显示最终回答标题
                    if not has_shown_final_response_header and token.strip():
                        has_shown_final_response_header = True
                        print("\n\n📝 【最终回答】\n", end="", flush=True)
                        
                    final_response += token
                    print(token, end="", flush=True)
            
            def on_thinking_change(is_thinking):
                nonlocal is_collecting_thinking
                if is_thinking:
                    is_collecting_thinking = True
                    print("\n\n🧠 【思考过程】", flush=True)
                else:
                    is_collecting_thinking = False
                    if thinking_content.strip():
                        # 输出收集到的思考内容
                        print(thinking_content.strip())
            
            def on_function_call(name, args):
                nonlocal function_calls
                function_calls.append({"name": name, "args": args})
                formatted_args = json.dumps(args, ensure_ascii=False, indent=2) if args else ""
                print(f"\n\n🔧 【工具调用】{name}")
                if formatted_args:
                    print(f"参数：{formatted_args}")
            
            def on_function_result(result):
                nonlocal function_results
                function_results.append(result)
                print(f"\n📊 【工具返回 #{len(function_results)}】")
                # 分行显示返回数据，使其更易读
                for line in result.strip().split('\n'):
                    print(f"  {line}")
            
            # 创建增强的流式处理器
            streaming_handler = EnhancedStreamingHandler(
                streaming_callback=on_token,
                start_callback=lambda: print("", end="", flush=True),  # 空操作，使用on_thinking_change代替
                thinking_callback=on_thinking_change,
                end_callback=lambda: None,  # 不在这里输出处理完成
                function_call_callback=on_function_call,
                function_result_callback=on_function_result
            )
            
            # 使用自定义处理器的流式输出
            try:
                # 使用流式输出，但仅收集结果
                result = ""
                for chunk in intelligent_assistant.stream_with_handler(user_input, streaming_handler):
                    result += chunk
                
                # 在所有处理完成后，显示处理完成信息
                print(f"\n\n{'-' * 60}")
                print(f"✅ 处理完成 | 共调用 {len(function_calls)} 个工具")
                print(f"{'-' * 60}")
            except Exception as e:
                print(f"\n\n❌ 处理错误: {str(e)}")
            
            print("\n")  # 额外换行确保清晰分隔
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n\n❌ 系统错误: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            import traceback
            print(f"错误详情:\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
