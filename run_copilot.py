#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
macOS Copilot 主程序入口
这个文件是应用程序的唯一入口点，负责启动整个应用程序

使用方法：
1. 直接运行: python run_copilot.py
2. 或者赋予执行权限后运行: ./run_copilot.py
"""

import os
import sys
import argparse
from typing import Optional

def setup_environment():
    """设置运行环境"""
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 将项目根目录添加到 Python 路径中
    sys.path.insert(0, script_dir)
    
    # 返回项目根目录
    return script_dir

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='macOS Copilot - 智能系统助手')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--api-key', type=str, help='设置API密钥')
    return parser.parse_args()

def run_application(debug: bool = False, api_key: Optional[str] = None):
    """运行应用程序"""
    try:
        # 导入必要的模块
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
    except ImportError as e:
        print(f"错误: 无法导入PyQt6模块 - {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)
    
    try:
        # 导入主窗口
        from macOS_Copilot.ui.main_window import MacOSAssistantUI
        
        # 创建应用程序
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # 打印启动信息
        if debug:
            print("调试模式已启用")
        print("启动macOS Copilot助手...")
        
        # 创建主窗口
        window = MacOSAssistantUI()
        
        # 如果提供了API密钥，设置它
        if api_key and hasattr(window, 'assistant') and hasattr(window.assistant, 'set_api_key'):
            window.assistant.set_api_key(api_key)
            print(f"已设置自定义API密钥")
        
        # 显示窗口
        window.show()
        
        # 进入应用程序主循环
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("无法启动程序，请确保项目结构完整")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def main():
    """主函数"""
    # 设置环境
    project_dir = setup_environment()
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 切换到项目目录
    os.chdir(project_dir)
    
    # 运行应用程序
    run_application(debug=args.debug, api_key=args.api_key)

if __name__ == "__main__":
    main() 