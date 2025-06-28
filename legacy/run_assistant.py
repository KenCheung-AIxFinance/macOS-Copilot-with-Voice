#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS系统助手启动脚本
"""

import sys
import os
import subprocess

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import langchain
        import langchain_openai
        import langchain_community
        import langchain_core
        import psutil
        import PyQt6
        import speech_recognition
        import edge_tts
        import openai
        print("✅ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_permissions():
    """检查系统权限"""
    print("🔍 检查系统权限...")
    
    # 检查麦克风权限（macOS）
    try:
        result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get properties'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  可能需要授予辅助功能权限")
            print("请前往: 系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能")
    except:
        pass
    
    print("✅ 权限检查完成")

def main():
    """主函数"""
    print("🤖 macOS系统助手 (旧版)")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 检查权限
    check_permissions()
    
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\n请选择运行模式:")
    print("1. 命令行版本 (推荐用于测试)")
    print("2. 图形界面版本 (推荐用于日常使用)")
    print("3. 退出")
    
    while True:
        try:
            choice = input("\n请输入选择 (1-3): ").strip()
            
            if choice == "1":
                print("\n🚀 启动命令行版本...")
                # 使用完整路径运行agent.py
                agent_path = os.path.join(current_dir, "agent.py")
                os.system(f"python \"{agent_path}\"")
                break
            elif choice == "2":
                print("\n🚀 启动图形界面版本...")
                # 使用完整路径运行macos_assistant_ui.py
                ui_path = os.path.join(current_dir, "macos_assistant_ui.py")
                os.system(f"python \"{ui_path}\"")
                break
            elif choice == "3":
                print("👋 再见！")
                break
            else:
                print("❌ 无效选择，请输入 1、2 或 3")
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main() 