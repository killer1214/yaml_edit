import tkinter as tk
from tkinter import filedialog, messagebox
import json
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class JsonGraphEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON 图形编辑器")
        self.root.geometry("800x600")
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建主框架
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 图形显示区域
        self.figure, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.main_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 初始化图数据
        self.graph = nx.DiGraph()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开", command=self.open_file)
        menubar.add_cascade(label="文件", menu=file_menu)
        self.root.config(menu=menubar)
    
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.parse_json(data)
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {str(e)}")
    
    def parse_json(self, data):
        # 清除现有图形
        self.graph.clear()
        self.ax.clear()
        
        # 解析 JSON 数据
        for item in data:
            if isinstance(item, dict):
                name = item.get('name', '')
                value = item.get('value', '')
                depends = item.get('depend', [])
                
                # 添加节点
                node_label = f"{name}: {value}"
                self.graph.add_node(node_label)
                
                # 添加依赖关系
                for dep in depends:
                    for other_item in data:
                        if other_item.get('name') == dep:
                            dep_label = f"{other_item['name']}: {other_item['value']}"
                            self.graph.add_edge(dep_label, node_label)
        
        # 绘制图形
        self.draw_graph()
    
    def draw_graph(self):
        self.ax.clear()
        pos = nx.spring_layout(self.graph)
        nx.draw(
            self.graph,
            pos,
            ax=self.ax,
            with_labels=True,
            node_color='lightblue',
            node_size=2000,
            font_size=8,
            font_weight='bold',
            arrows=True
        )
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = JsonGraphEditor(root)
    root.mainloop() 