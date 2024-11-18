import sys
import customtkinter as ctk
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from common.graph_window import GraphWindow

def main():
    """主程序入口"""
    # 创建主窗口
    app = GraphWindow()
    
    # 设置窗口样式
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # 创建依赖关系
    dependencies = [
        ("任务A", "任务B"),
        ("任务B", "任务C"),
        ("任务A", "任务D"),
        ("任务D", "任务C")
    ]
    
    # 创建节点和连线
    app.create_dependencies_from_yaml(dependencies)
    
    # 启动主循环
    app.mainloop()

if __name__ == "__main__":
    main() 