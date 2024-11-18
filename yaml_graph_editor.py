import tkinter as tk
from tkinter import filedialog, messagebox
import yaml  # 替换json为yaml
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class YamlGraphEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("YAML 图形编辑器")
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
            filetypes=[("YAML 文件", "*.yaml;*.yml"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)  # 使用yaml.safe_load替换json.load
                self.parse_yaml(data)
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {str(e)}")
    
    def parse_yaml(self, data):
        # 清除现有图形
        self.graph.clear()
        self.ax.clear()
        
        # 解析 YAML 数据
        if not isinstance(data, dict) or 'jobs' not in data:
            messagebox.showerror("错误", "YAML文件格式错误：需要以jobs字段开始")
            return
        
        jobs = data['jobs']
        if not isinstance(jobs, list):
            messagebox.showerror("错误", "YAML文件格式错误：jobs必须是列表")
            return
        
        # 创建节点映射，用于快速查找
        node_map = {}
        for job_item in jobs:
            if isinstance(job_item, dict):
                # 使用job字段作为唯一标识符
                job_id = job_item.get('job', '')
                name = job_item.get('name', '')
                value = job_item.get('value', '')
                
                # 创建节点标签
                node_label = f"{name}: {value}"
                # 使用job_id作为映射键
                node_map[job_id] = node_label
                self.graph.add_node(node_label)
        
        # 添加依赖关系
        for job_item in jobs:
            if isinstance(job_item, dict):
                job_id = job_item.get('job', '')
                depends = job_item.get('depend', [])
                
                if job_id in node_map:
                    current_node = node_map[job_id]
                    
                    # 处理依赖关系
                    if isinstance(depends, list):
                        for dep in depends:
                            if dep in node_map:
                                self.graph.add_edge(node_map[dep], current_node)
        
        # 绘制图形
        self.draw_graph()
    
    def draw_graph(self):
        self.ax.clear()
        if len(self.graph) > 0:  # 只在有节点时绘制
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
    app = YamlGraphEditor(root)
    root.mainloop() 