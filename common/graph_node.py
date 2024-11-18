import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from common.graph_window import GraphWindow
import customtkinter as ctk

def main():
    """测试函数"""
    # 创建主窗口
    app = GraphWindow()
    
    # 设置窗口样式
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # 添加测试节点
    node1 = app.add_node(
        name="开始节点",
        position=(300, 500)
    )
    
    node2 = app.add_node(
        name="结束节点",
        position=(700, 500)
    )
    
    # 启动主循环
    app.mainloop()

if __name__ == "__main__":
    main()
