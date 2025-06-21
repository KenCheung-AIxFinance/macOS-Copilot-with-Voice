import os
import sys
import subprocess
import json
import psutil
import platform
from typing import List, Dict, Any, Optional
from datetime import datetime
import threading
import time

# LangChain imports
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.tools import BaseTool
from langchain.schema import BaseOutputParser
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

class MacOSAssistant:
    """macOS系统助手主类"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.7
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
    
    def chat(self, user_input: str) -> str:
        """处理用户输入并返回响应"""
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
    
    assistant = MacOSAssistant(api_key)
    
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
            response = assistant.chat(user_input)
            print('\n',"助手回答:",response)
            
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")

if __name__ == "__main__":
    main()
