import tkinter as tk
from tkinter import filedialog, messagebox
import yaml
import networkx as nx
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from common import YamlParser, GraphData
from html_generator import HtmlGenerator  # 添加导入语句
from typing import List
from datetime import datetime

class YamlGraphEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("YAML 任务依赖编辑器")
        self.root.geometry("1000x800")
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建主框架
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 初始化图形
        self.figure, self.ax = plt.subplots(figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.main_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        # 初始化图数据
        self.graph = nx.DiGraph()
        self.node_positions = {}
        self.selected_node = None
        self.dragging = False
        self.drag_start = None
        
        # 绑定鼠标事件
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_motion)
        
        # 状态栏
        self.status_bar = tk.Label(root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.parser = YamlParser()

    def on_mouse_press(self, event):
        if event.inaxes != self.ax:
            return
            
        self.drag_start = (event.xdata, event.ydata)
        
        # 检查是否点击了节点
        for node, (x, y) in self.node_positions.items():
            dist = ((x - event.xdata) ** 2 + (y - event.ydata) ** 2) ** 0.5
            if dist < 0.1:
                self.selected_node = node
                self.dragging = True
                self.status_bar.config(text=f"选中节点: {node}")
                return

    def on_mouse_motion(self, event):
        if not self.dragging or not self.selected_node or event.inaxes != self.ax:
            return
            
        # 更新节点位置
        self.node_positions[self.selected_node] = (event.xdata, event.ydata)
        self.redraw_graph()
        self.status_bar.config(text=f"正在移动节点: {self.selected_node}")

    def on_mouse_release(self, event):
        if self.dragging:
            self.dragging = False
            self.status_bar.config(text=f"节点 {self.selected_node} 已放置")
        self.drag_start = None

    def redraw_graph(self):
        try:
            self.ax.clear()
            
            # 设置白色背景
            self.ax.set_facecolor('white')
            
            # 绘制边（箭头）
            for edge in self.graph.edges():
                start_pos = self.node_positions[edge[0]]
                end_pos = self.node_positions[edge[1]]
                # 增加箭头大小和可见度
                arrow = plt.arrow(
                    start_pos[0], start_pos[1],
                    end_pos[0] - start_pos[0], end_pos[1] - start_pos[1],
                    head_width=0.1,  # 增大箭头宽度
                    head_length=0.2,  # 增大箭头长度
                    fc='black',      # 更改颜色为黑色
                    ec='black',
                    width=0.02,      # 增加线条宽度
                    length_includes_head=True,
                    alpha=0.8        # 增加不透明度
                )
                self.ax.add_patch(arrow)
            
            # 绘制节点
            for node, pos in self.node_positions.items():
                # 增大节点尺寸
                color = 'lightcoral' if node == self.selected_node else '#87CEEB'  # 使用天蓝色
                circle = plt.Circle(pos, 0.15, color=color, alpha=0.9)  # 增大节点半径
                self.ax.add_patch(circle)
                
                # 改进节点标签显示
                self.ax.text(pos[0], pos[1], node,
                            horizontalalignment='center',
                            verticalalignment='center',
                            fontsize=12,        # 增大字体
                            fontweight='bold',
                            color='black',      # 黑色文字
                            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=2))
            
            # 设置图形属性
            self.ax.set_title("任务依赖关系图 (可拖拽节点)", fontsize=14, pad=20)
            self.ax.set_xlim(-2, 2)
            self.ax.set_ylim(-2, 2)
            self.ax.axis('equal')
            self.ax.grid(True, linestyle='--', alpha=0.3)  # 添加网格线
            
            # 移除坐标轴
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"重绘图形时出错: {str(e)}")
            messagebox.showerror("错误", f"重绘图形时出错: {str(e)}")

    def parse_yaml(self, data):
        try:
            self.graph.clear()
            self.node_positions.clear()
            
            jobs = data.get('jobs', [])
            if not isinstance(jobs, list):
                messagebox.showerror("错误", "jobs必须是列表格式")
                return
            
            # 存储原始任务数据
            self.original_jobs = jobs
            
            # 计算节点的初始位置（使用圆形布局）
            num_jobs = len(jobs)
            radius = 1.5  # 圆的半径
            
            for i, job_item in enumerate(jobs):
                if not isinstance(job_item, dict):
                    continue
                
                job_id = job_item.get('job', '')
                name = job_item.get('name', job_id)
                value = job_item.get('value', '')
                
                # 创建更有意义的节点标签
                node_label = f"{name}\n({value})" if value else name
                
                # 计算节点位置（圆形布局）
                angle = (2 * np.pi * i) / num_jobs
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                
                self.node_positions[node_label] = (x, y)
                self.graph.add_node(node_label)
            
            # 添加依赖关系（边）
            for job_item in jobs:
                if not isinstance(job_item, dict):
                    continue
                
                current_name = job_item.get('name', '')
                current_value = job_item.get('value', '')
                current_label = f"{current_name}\n({current_value})" if current_value else current_name
                
                depends = job_item.get('depend', [])
                if not isinstance(depends, list):
                    depends = [depends]
                
                for dep in depends:
                    if dep:
                        # 查找依赖节点的完整标签
                        dep_job = next((job for job in jobs if job.get('name') == dep), None)
                        if dep_job:
                            dep_value = dep_job.get('value', '')
                            dep_label = f"{dep}\n({dep_value})" if dep_value else dep
                            self.graph.add_edge(dep_label, current_label)
            
            self.redraw_graph()
            self.status_bar.config(text=f"已加载 {len(self.graph.nodes)} 个节点和 {len(self.graph.edges)} 个依赖关系")
            
        except Exception as e:
            print(f"解析YAML出错: {str(e)}")
            messagebox.showerror("错误", f"解析YAML数据时出错: {str(e)}")
            self.status_bar.config(text="解析出错")

    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开", command=self.open_file)
        file_menu.add_command(label="生成HTML视图", command=self.generate_html_view)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        self.root.config(menu=menubar)
    
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("YAML 文件", "*.yaml;*.yml"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                # 使用解析器加载文件
                jobs = self.parser.parse_file(file_path)
                
                # 验证依赖关系
                errors = self.parser.validate_dependencies()
                if errors:
                    messagebox.showwarning("警告", "\n".join(errors))
                
                # 创建图形数据
                graph_data = GraphData(jobs)
                nodes = graph_data.get_nodes()
                edges = graph_data.get_edges()
                
                # 更新图形显示
                self.update_graph(nodes, edges)
                
            except Exception as e:
                messagebox.showerror("错误", str(e))
    
    def draw_graph(self):
        try:
            print("开始绘制图形...")
            
            # 清除当前图形
            self.ax.clear()
            
            if len(self.graph) > 0:
                # 使用层次布局，更适合显依赖关系
                pos = nx.kamada_kawai_layout(self.graph)
                self.node_positions = pos
                
                # 绘制节点
                nx.draw_networkx_nodes(
                    self.graph,
                    pos,
                    ax=self.ax,
                    node_color='lightblue',
                    node_size=3000,
                    alpha=0.7
                )
                
                # 绘制边（带箭头）
                nx.draw_networkx_edges(
                    self.graph,
                    pos,
                    ax=self.ax,
                    edge_color='gray',
                    arrows=True,
                    arrowsize=20,
                    width=2
                )
                
                # 绘制节点标签
                nx.draw_networkx_labels(
                    self.graph,
                    pos,
                    ax=self.ax,
                    font_size=10,
                    font_weight='bold'
                )
                
                # 设置图形属性
                self.ax.set_title("任务依赖关系图")
                self.ax.set_xticks([])
                self.ax.set_yticks([])
                
                # 添加边框
                self.ax.spines['top'].set_visible(True)
                self.ax.spines['right'].set_visible(True)
                self.ax.spines['bottom'].set_visible(True)
                self.ax.spines['left'].set_visible(True)
                
                # 调整布局
                plt.tight_layout()
                
                print("图形绘制完成")
                self.canvas.draw()
            else:
                print("没有节点可以绘制")
                
        except Exception as e:
            print(f"绘制出错: {str(e)}")
            messagebox.showerror("错误", f"绘制图形时出错: {str(e)}")
    
    def on_node_click(self, event):
        if event.inaxes != self.ax:
            return
            
        # 获取点击位置
        click_x, click_y = event.xdata, event.ydata
        
        # 检查是否点击了节点
        for node, (x, y) in self.node_positions.items():
            # 计算点击位置与节点中心的距离
            dist = ((x - click_x) ** 2 + (y - click_y) ** 2) ** 0.5
            # 增加点击判定范围
            if dist < 0.2:  # 增大判定范围
                self.selected_node = node
                # 高亮显示选中的节点
                self.highlight_selected_node(node)
                # 显示节点信息
                self.show_node_info(node)
                break

    def highlight_selected_node(self, selected_node):
        """高亮显示选中的节点"""
        self.ax.clear()
        pos = self.node_positions
        
        # 绘制所节点
        node_colors = ['red' if node == selected_node else 'lightblue' 
                      for node in self.graph.nodes()]
        node_sizes = [4000 if node == selected_node else 3000 
                     for node in self.graph.nodes()]
        
        # 绘制节点
        nx.draw_networkx_nodes(
            self.graph,
            pos,
            ax=self.ax,
            node_color=node_colors,
            node_size=node_sizes
        )
        
        # 绘制边
        nx.draw_networkx_edges(
            self.graph,
            pos,
            ax=self.ax,
            edge_color='gray',
            arrows=True,
            arrowsize=20,
            width=2
        )
        
        # 绘制标签
        nx.draw_networkx_labels(
            self.graph,
            pos,
            ax=self.ax,
            font_size=10,
            font_weight='bold'
        )
        
        self.canvas.draw()

    def show_node_info(self, node):
        """显示节点详细信息"""
        # 查找原始任务信息
        node_info = "节点信息:\n"
        for job in self.original_jobs:
            if job.get('name') == node.split('\n')[0]:  # 假设节点标签格式为 "name\nvalue"
                node_info += f"任务ID: {job.get('job', '')}\n"
                node_info += f"名称: {job.get('name', '')}\n"
                node_info += f"值: {job.get('value', '')}\n"
                if 'depend' in job:
                    depends = job['depend']
                    if isinstance(depends, list):
                        node_info += f"依赖任务: {', '.join(depends)}\n"
                    else:
                        node_info += f"依赖任务: {depends}\n"
                break
        
        messagebox.showinfo("节点信息", node_info)
    
    def generate_html_view(self):
        """生成HTML视图"""
        if hasattr(self, 'parser') and self.parser.jobs:
            try:
                HtmlGenerator.generate_html(self.parser.jobs)
                self.status_bar.config(text="已生成HTML视图")
            except Exception as e:
                messagebox.showerror("错误", f"生成HTML视图时出错: {str(e)}")
        else:
            messagebox.showwarning("警告", "请先打开YAML文件")

    def buildflow(self):
        """构建完整的工作流程"""
        try:
            if not hasattr(self, 'parser') or not self.parser.jobs:
                messagebox.showwarning("警告", "请先打开YAML文件")
                return
            
            # 1. 验证依赖关系
            errors = self.parser.validate_dependencies()
            if errors:
                messagebox.showerror("错误", "依赖关系验证失败:\n" + "\n".join(errors))
                return
            
            # 2. 检查循环依赖
            try:
                cycles = list(nx.simple_cycles(self.graph))
                if cycles:
                    cycle_str = "\n".join([" -> ".join(cycle) for cycle in cycles])
                    messagebox.showerror("错误", f"检测到循环依赖:\n{cycle_str}")
                    return
            except Exception as e:
                messagebox.showerror("错误", f"检查循环依赖时出错: {str(e)}")
                return
            
            # 3. 获取任务执行顺序
            try:
                execution_order = list(nx.topological_sort(self.graph))
                
                # 4. 创建执行计划
                execution_plan = []
                for node in execution_order:
                    job = next((j for j in self.parser.jobs if j.name == node.split('\n')[0]), None)
                    if job:
                        execution_plan.append({
                            'job': job.job,
                            'name': job.name,
                            'value': job.value,
                            'depend': job.depend,
                            'status': 'pending'
                        })
                
                # 5. 生成执行报告
                report = self.generate_execution_report(execution_plan)
                
                # 6. 更新状态栏
                self.status_bar.config(text=f"工作流程构建完成，共 {len(execution_plan)} 个任务")
                
                # 7. 显示执行计划
                self.show_execution_plan(execution_plan)
                
                # 8. 生成并显示HTML视图
                self.generate_html_view()
                
                return execution_plan
                
            except nx.NetworkXUnfeasible:
                messagebox.showerror("错误", "任务依赖关系中存在循环")
                return None
            except Exception as e:
                messagebox.showerror("错误", f"生成执行顺序时出错: {str(e)}")
                return None
            
        except Exception as e:
            messagebox.showerror("错误", f"构建工作流程时出错: {str(e)}")
            return None

    def generate_execution_report(self, execution_plan: List[dict]) -> str:
        """生成执行报告
        
        Args:
            execution_plan: 执行计划列表
            
        Returns:
            str: 格式化的执行报告
        """
        report = "工作流程执行计划:\n\n"
        
        # 1. 基本信息
        report += f"总任务数: {len(execution_plan)}\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 2. 执行顺序
        report += "执行顺序:\n"
        for i, task in enumerate(execution_plan, 1):
            report += f"{i}. {task['name']} ({task['job']})\n"
            if task['depend']:
                report += f"   依赖任务: {', '.join(task['depend'])}\n"
        
        # 3. 保存报告
        report_file = "execution_report.txt"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"执行报告已保存到: {report_file}")
        except Exception as e:
            print(f"保存执行报告时出错: {str(e)}")
        
        return report

    def show_execution_plan(self, execution_plan: List[dict]):
        """显示执行计划对话框
        
        Args:
            execution_plan: 执行计划列表
        """
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("执行计划")
        dialog.geometry("600x400")
        
        # 创建文本框
        text_widget = tk.Text(dialog, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = tk.Scrollbar(dialog, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # 显示执行计划
        for i, task in enumerate(execution_plan, 1):
            text_widget.insert(tk.END, f"任务 {i}:\n")
            text_widget.insert(tk.END, f"  名称: {task['name']}\n")
            text_widget.insert(tk.END, f"  任务ID: {task['job']}\n")
            text_widget.insert(tk.END, f"  值: {task['value']}\n")
            if task['depend']:
                text_widget.insert(tk.END, f"  依赖任务: {', '.join(task['depend'])}\n")
            text_widget.insert(tk.END, f"  状态: {task['status']}\n")
            text_widget.insert(tk.END, "\n")
        
        # 设置只读
        text_widget.config(state=tk.DISABLED)
        
        # 添加关闭按钮
        tk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = YamlGraphEditor(root)
    app.generate_html_view()
    # root.mainloop() 