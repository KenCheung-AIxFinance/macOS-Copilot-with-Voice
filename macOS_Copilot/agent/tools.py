import os
import subprocess
import time
import re
import glob
import psutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain.tools import tool

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
        """获取macOS系统信息，包括系统版本、CPU、内存和磁盘使用情况"""
        try:
            # 获取系统版本
            system_version = subprocess.check_output(
                ["sw_vers"], 
                text=True, 
                stderr=subprocess.PIPE
            )
            
            # 获取CPU信息
            cpu_info = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], 
                text=True, 
                stderr=subprocess.PIPE
            ).strip()
            
            # 获取内存信息
            mem = psutil.virtual_memory()
            mem_total = mem.total / (1024**3)  # 转换为GB
            mem_used_percent = mem.percent
            
            # 获取磁盘信息
            disk = psutil.disk_usage('/')
            disk_total = disk.total / (1024**3)  # 转换为GB
            disk_used_percent = disk.percent
            
            return f"""系统信息:
{system_version}
CPU: {cpu_info}
内存: {mem_total:.1f}GB 总内存, {mem_used_percent:.1f}% 使用率
磁盘: {disk_total:.1f}GB 总空间, {disk_used_percent:.1f}% 使用率"""
        except Exception as e:
            return f"获取系统信息失败: {str(e)}"
    
    @staticmethod
    @tool
    def get_running_processes() -> str:
        """获取正在运行的进程列表，按CPU使用率排序"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # 按CPU使用率排序
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            # 取前15个进程
            top_processes = processes[:15]
            
            result = "正在运行的进程 (按CPU使用率排序):\n"
            result += "{:<6} {:<20} {:<15} {:<10} {:<10}\n".format("PID", "名称", "用户", "CPU%", "内存%")
            result += "-" * 65 + "\n"
            
            for proc in top_processes:
                result += "{:<6} {:<20} {:<15} {:<10.1f} {:<10.1f}\n".format(
                    proc['pid'],
                    proc['name'][:20],
                    proc['username'][:15],
                    proc['cpu_percent'],
                    proc['memory_percent']
                )
                
            return result
        except Exception as e:
            return f"获取进程信息失败: {str(e)}"
    
    @staticmethod
    @tool
    def open_application(app_name: str) -> str:
        """打开指定的应用程序，支持模糊匹配"""
        try:
            # 获取所有应用程序
            all_apps = MacOSTools._get_all_applications()
            
            # 查找匹配的应用程序
            matching_apps = MacOSTools._find_matching_apps(app_name, all_apps)
            
            if not matching_apps:
                return f"未找到应用程序: {app_name}"
            
            # 如果找到多个匹配项，使用最佳匹配
            best_match = matching_apps[0]
            app_path = best_match['path']
            
            # 打开应用程序
            subprocess.Popen(["open", app_path], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
            
            return f"已打开 {best_match['name']}"
        except Exception as e:
            return f"打开应用程序失败: {str(e)}"
    
    @staticmethod
    def _get_all_applications() -> List[Dict[str, str]]:
        """获取所有已安装的应用程序"""
        apps = []
        
        # 搜索常见应用程序目录
        app_dirs = [
            "/Applications",
            "/System/Applications",
            "/System/Applications/Utilities",
            os.path.expanduser("~/Applications")
        ]
        
        for app_dir in app_dirs:
            if os.path.exists(app_dir):
                # 查找.app文件夹
                app_paths = glob.glob(os.path.join(app_dir, "*.app"))
                for app_path in app_paths:
                    app_name = os.path.basename(app_path).replace(".app", "")
                    apps.append({
                        "name": app_name,
                        "path": app_path
                    })
        
        return apps
    
    @staticmethod
    def _find_matching_apps(query: str, apps: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """查找匹配查询的应用程序"""
        # 定义归一化函数
        def norm(s):
            # 转换为小写
            s = s.lower()
            # 移除特殊字符
            s = re.sub(r'[^a-z0-9\s]', '', s)
            # 移除多余空格
            s = re.sub(r'\s+', ' ', s).strip()
            return s
        
        # 归一化查询
        norm_query = norm(query)
        
        # 精确匹配
        exact_matches = [app for app in apps if norm(app['name']) == norm_query]
        if exact_matches:
            return exact_matches
        
        # 前缀匹配
        prefix_matches = [app for app in apps if norm(app['name']).startswith(norm_query)]
        if prefix_matches:
            return prefix_matches
        
        # 包含匹配
        contains_matches = [app for app in apps if norm_query in norm(app['name'])]
        if contains_matches:
            return contains_matches
        
        # 模糊匹配 (简单实现)
        fuzzy_matches = []
        for app in apps:
            norm_name = norm(app['name'])
            # 计算简单的相似度分数
            query_parts = norm_query.split()
            score = sum(1 for part in query_parts if part in norm_name)
            if score > 0:
                fuzzy_matches.append((app, score))
        
        # 按分数排序
        fuzzy_matches.sort(key=lambda x: x[1], reverse=True)
        
        # 返回匹配的应用程序
        return [match[0] for match in fuzzy_matches[:5]] if fuzzy_matches else []
    
    @staticmethod
    @tool
    def execute_terminal_command(command: str) -> str:
        """执行终端命令并返回结果"""
        # 安全检查 - 避免危险命令
        dangerous_commands = ["rm", "mkfs", "dd", ">", "sudo"]
        for cmd in dangerous_commands:
            if cmd in command:
                return f"出于安全考虑，不执行包含 '{cmd}' 的命令"
        
        try:
            # 使用R1增强器优化命令（如果可用）
            if MacOSTools.r1_enhancer:
                optimized_command = MacOSTools.r1_enhancer.optimize_system_command(command)
                if optimized_command != command:
                    command = optimized_command
            
            # 执行命令
            result = subprocess.check_output(
                command, 
                shell=True, 
                text=True,
                stderr=subprocess.STDOUT,
                timeout=10
            )
            
            return result
        except subprocess.CalledProcessError as e:
            return f"命令执行错误 (返回码 {e.returncode}):\n{e.output}"
        except subprocess.TimeoutExpired:
            return "命令执行超时 (10秒)"
        except Exception as e:
            return f"执行命令时出错: {str(e)}"
    
    @staticmethod
    @tool
    def get_network_info() -> str:
        """获取网络接口和连接状态信息"""
        try:
            # 获取网络接口信息
            ifconfig_output = subprocess.check_output(
                ["ifconfig"], 
                text=True, 
                stderr=subprocess.PIPE
            )
            
            # 获取Wi-Fi信息
            try:
                airport_output = subprocess.check_output(
                    ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"], 
                    text=True, 
                    stderr=subprocess.PIPE
                )
            except:
                airport_output = "无法获取Wi-Fi信息"
            
            return f"网络接口信息:\n{ifconfig_output}\n\nWi-Fi信息:\n{airport_output}"
        except Exception as e:
            return f"获取网络信息失败: {str(e)}"
    
    @staticmethod
    @tool
    def get_battery_info() -> str:
        """获取电池状态和剩余电量信息"""
        try:
            # 使用pmset命令获取电池信息
            battery_info = subprocess.check_output(
                ["pmset", "-g", "batt"], 
                text=True, 
                stderr=subprocess.PIPE
            )
            
            return f"电池信息:\n{battery_info}"
        except Exception as e:
            return f"获取电池信息失败: {str(e)}"
    
    @staticmethod
    @tool
    def search_files(query: str, directory: str = "/Users") -> str:
        """在指定目录中搜索文件"""
        try:
            # 使用R1增强器增强搜索（如果可用）
            if MacOSTools.r1_enhancer:
                enhanced_results = MacOSTools.r1_enhancer.enhance_file_search(query, directory)
                if enhanced_results:
                    result = "搜索结果:\n"
                    for item in enhanced_results:
                        result += f"- {item['path']} ({item['type']})\n"
                    return result
            
            # 基本搜索实现
            search_command = f"find {directory} -name '*{query}*' -type f -not -path '*/\\.*' 2>/dev/null | head -n 20"
            search_result = subprocess.check_output(
                search_command, 
                shell=True, 
                text=True
            )
            
            if search_result.strip():
                return f"找到以下文件:\n{search_result}"
            else:
                return f"在 {directory} 中未找到包含 '{query}' 的文件"
        except Exception as e:
            return f"搜索文件失败: {str(e)}"
    
    @staticmethod
    @tool
    def get_installed_applications() -> str:
        """获取已安装的应用程序列表"""
        try:
            apps = MacOSTools._get_all_applications()
            
            result = "已安装的应用程序:\n"
            # 按名称排序
            apps.sort(key=lambda x: x['name'])
            
            for app in apps:
                result += f"{app['name']}\n"
                
            return result
        except Exception as e:
            return f"获取应用程序列表失败: {str(e)}"
    
    @staticmethod
    @tool
    def create_note(content: str, filename: str = None) -> str:
        """创建文本笔记文件"""
        try:
            # 如果没有提供文件名，使用当前时间生成
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"note_{timestamp}.txt"
            
            # 确保文件名有.txt扩展名
            if not filename.endswith(".txt"):
                filename += ".txt"
            
            # 保存到桌面
            desktop_path = os.path.expanduser("~/Desktop")
            file_path = os.path.join(desktop_path, filename)
            
            # 写入文件
            with open(file_path, 'w') as f:
                f.write(content)
            
            return f"笔记已创建: {file_path}"
        except Exception as e:
            return f"创建笔记失败: {str(e)}"
    
    @staticmethod
    @tool
    def set_system_volume(volume: int) -> str:
        """设置系统音量 (0-100)"""
        try:
            # 确保音量在有效范围内
            volume = max(0, min(100, volume))
            
            # 转换为0-10的范围
            osascript_volume = volume / 10
            
            # 使用osascript设置音量
            subprocess.run([
                "osascript", 
                "-e", 
                f"set volume output volume {volume}"
            ], check=True)
            
            return f"系统音量已设置为 {volume}%"
        except Exception as e:
            return f"设置音量失败: {str(e)}"
    
    @staticmethod
    @tool
    def get_current_time() -> str:
        """获取当前时间"""
        now = datetime.now()
        return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}" 