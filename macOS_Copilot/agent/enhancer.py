import re
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from .types import TaskComplexity

class DeepSeekR1Enhancer:
    """DeepSeek R1 增强器，提供高级推理能力"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化DeepSeek R1增强器
        
        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        
        # 创建增强型LLM
        self.enhancer_llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.2  # 低温度以获得更确定性的结果
        )
    
    def is_complex_technical_query(self, query: str) -> bool:
        """
        判断查询是否为复杂技术查询
        
        Args:
            query: 用户查询
        
        Returns:
            bool: 是否为复杂技术查询
        """
        # 检测技术关键词
        technical_keywords = [
            "诊断", "优化", "修复", "配置", "设置", "安装", "卸载", 
            "更新", "升级", "降级", "编译", "构建", "调试", "分析",
            "网络", "系统", "性能", "内存", "磁盘", "CPU", "进程",
            "端口", "服务", "驱动", "内核", "防火墙", "权限", "安全"
        ]
        
        # 检测复杂度指示词
        complexity_indicators = [
            "如何", "怎样", "为什么", "原因", "问题", "错误", "失败",
            "无法", "不能", "不工作", "慢", "卡顿", "崩溃", "冻结",
            "不响应", "蓝屏", "黑屏", "白屏", "闪退", "死机"
        ]
        
        # 计算技术关键词匹配数
        tech_matches = sum(1 for keyword in technical_keywords if keyword in query)
        
        # 计算复杂度指示词匹配数
        complexity_matches = sum(1 for indicator in complexity_indicators if indicator in query)
        
        # 如果同时匹配技术关键词和复杂度指示词，认为是复杂技术查询
        return tech_matches > 0 and complexity_matches > 0
    
    def enhance_complexity_evaluation(self, user_input: str, original_complexity: TaskComplexity) -> TaskComplexity:
        """
        增强任务复杂度评估
        
        Args:
            user_input: 用户输入
            original_complexity: 原始复杂度评估
        
        Returns:
            TaskComplexity: 增强后的复杂度评估
        """
        # 如果不是复杂技术查询，保留原始评估
        if not self.is_complex_technical_query(user_input):
            return original_complexity
        
        try:
            # 构建提示
            prompt = f"""请分析以下用户查询的复杂度，并按照以下标准分类:
1 = 简单任务：直接查询、单一操作
2 = 中等任务：2-3步操作，有条件判断
3 = 复杂任务：多步骤，需要推理，系统诊断
4 = 高级任务：创造性解决方案，复杂诊断，自适应执行

用户查询: "{user_input}"

只需返回一个数字 (1-4)，不要解释。"""
            
            # 获取增强评估
            response = self.enhancer_llm.invoke(prompt)
            result = response.content.strip()
            
            # 尝试解析结果
            if result and result[0].isdigit():
                complexity_level = int(result[0])
                if 1 <= complexity_level <= 4:
                    return TaskComplexity(complexity_level)
        except Exception:
            pass
        
        # 如果评估失败，返回原始评估
        return original_complexity
    
    def generate_advanced_plan(self, user_input: str) -> str:
        """
        生成高级执行计划
        
        Args:
            user_input: 用户输入
        
        Returns:
            str: 执行计划
        """
        try:
            # 构建提示
            prompt = f"""作为macOS系统专家，请为以下用户请求创建详细的执行计划:

用户请求: "{user_input}"

请按照以下格式提供执行计划:
1. 任务分析: [分析用户请求的核心需求]
2. 执行步骤:
   a. [第一步] - [使用的工具/命令]
   b. [第二步] - [使用的工具/命令]
   ...
3. 可能的问题和解决方案:
   - [可能的问题1]: [解决方案]
   - [可能的问题2]: [解决方案]
   ...

请确保计划详细、全面且针对macOS系统。"""
            
            # 获取执行计划
            response = self.enhancer_llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            return f"无法生成执行计划: {str(e)}"
    
    def optimize_system_command(self, command: str) -> str:
        """
        优化系统命令
        
        Args:
            command: 原始命令
        
        Returns:
            str: 优化后的命令
        """
        try:
            # 构建提示
            prompt = f"""作为macOS系统专家，请优化以下终端命令，使其更高效、更安全、更符合macOS最佳实践:

原始命令: "{command}"

如果命令已经是最优的，请直接返回原始命令。
如果命令有问题或可以优化，请提供优化后的命令。
只返回优化后的命令，不要解释。"""
            
            # 获取优化命令
            response = self.enhancer_llm.invoke(prompt)
            optimized_command = response.content.strip()
            
            # 如果优化结果为空或明显不是命令，返回原始命令
            if not optimized_command or optimized_command.startswith("原始命令已经是最优的") or len(optimized_command) > 3 * len(command):
                return command
                
            return optimized_command
        except Exception:
            return command
    
    def analyze_error(self, error_message: str, original_command: str) -> Dict[str, str]:
        """
        分析错误信息并提供解决方案
        
        Args:
            error_message: 错误信息
            original_command: 原始命令
        
        Returns:
            Dict[str, str]: 错误分析和解决方案
        """
        try:
            # 构建提示
            prompt = f"""作为macOS系统专家，请分析以下命令执行时产生的错误，并提供解决方案:

原始命令: "{original_command}"
错误信息: "{error_message}"

请按照以下JSON格式回答:
{{
    "error_type": "错误类型",
    "cause": "错误原因简要说明",
    "solution": "解决方案",
    "improved_command": "改进后的命令(如果适用)"
}}

只返回JSON格式的回答，不要添加其他文本。"""
            
            # 获取错误分析
            response = self.enhancer_llm.invoke(prompt)
            analysis_text = response.content.strip()
            
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis_text = json_match.group(0)
            
            # 简单处理为字典
            result = {}
            for line in analysis_text.strip('{}').split(','):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().strip('"\'')
                    value = value.strip().strip('"\'')
                    result[key] = value
            
            return result
        except Exception as e:
            return {
                "error_type": "分析失败",
                "cause": f"无法分析错误: {str(e)}",
                "solution": "请查看原始错误信息并手动解决",
                "improved_command": original_command
            }
    
    def enhance_file_search(self, query: str, directory: str) -> List[Dict[str, str]]:
        """
        增强文件搜索功能
        
        Args:
            query: 搜索查询
            directory: 搜索目录
        
        Returns:
            List[Dict[str, str]]: 增强的搜索结果
        """
        try:
            # 构建提示
            prompt = f"""作为macOS系统专家，请帮助设计一个高效的文件搜索命令，以在指定目录中查找与查询相关的文件:

搜索查询: "{query}"
搜索目录: "{directory}"

请提供一个高效的find或mdfind命令，考虑:
1. 文件名匹配
2. 内容匹配(如果适用)
3. 排除系统和隐藏文件
4. 限制结果数量
5. 提高搜索效率

只返回命令本身，不要解释。"""
            
            # 获取优化的搜索命令
            response = self.enhancer_llm.invoke(prompt)
            search_command = response.content.strip()
            
            # 如果命令看起来合理，使用它
            if search_command and ('find' in search_command or 'mdfind' in search_command):
                import subprocess
                
                # 执行命令
                result = subprocess.check_output(
                    search_command, 
                    shell=True, 
                    text=True,
                    stderr=subprocess.STDOUT
                )
                
                # 解析结果
                files = []
                for line in result.splitlines():
                    if line.strip():
                        file_path = line.strip()
                        file_type = "文件夹" if file_path.endswith('/') else "文件"
                        files.append({
                            "path": file_path,
                            "type": file_type
                        })
                
                return files[:20]  # 限制结果数量
        except Exception:
            pass
        
        # 如果增强搜索失败，返回空列表
        return [] 