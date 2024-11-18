import tkinter as tk
import customtkinter as ctk
from typing import Dict, Set, Tuple, Optional, List
import math

from common.draggable_node import DraggableNode
from common.anchor_point import AnchorPoint

class GraphWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("任务依赖图")
        self.geometry("800x600")
        
        # 设置窗口背景色
        self.configure(fg_color="#2b2b2b")
        
        # 创建顶部工具栏框架
        self.toolbar = ctk.CTkFrame(self, fg_color="#1f1f1f")
        self.toolbar.pack(side="top", fill="x", padx=5, pady=5)
        
        # 创建添加节点按钮
        self.add_button = ctk.CTkButton(
            self.toolbar,
            text="增加节点",
            width=100,
            height=32,
            command=self._show_add_node_dialog
        )
        self.add_button.pack(side="left", padx=5, pady=5)
        
        # 创建删除节点按钮（初始状态为禁用）
        self.delete_button = ctk.CTkButton(
            self.toolbar,
            text="删除节点",
            width=100,
            height=32,
            command=self._delete_selected_node,
            state="disabled",  # 初始状态为禁用
            fg_color="#666666",  # 禁用状态的颜色
            hover_color="#444444"
        )
        self.delete_button.pack(side="left", padx=5, pady=5)
        
        # 当前选中的节点
        self.selected_nodes = set()  # 存储选中的节点
        
        # 选择框相关
        self.selection_box = None
        self.selection_start = None
        self.is_selecting = False
        
        # 创建画布
        self.canvas = tk.Canvas(
            self,
            bg="#2b2b2b",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # 存储节点和连线
        self.nodes: Dict[str, DraggableNode] = {}
        self.connections: Set[Tuple[DraggableNode, DraggableNode]] = set()
        self.connection_lines: Dict[int, Tuple[DraggableNode, DraggableNode]] = {}
        
        # 当前高亮的吸附点
        self.highlighted_anchor = None
        
        # 绑定画布事件
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Control-Button-1>", self._on_selection_start)
        self.canvas.bind("<Control-B1-Motion>", self._on_selection_drag)
        self.canvas.bind("<Control-ButtonRelease-1>", self._on_selection_end)
        self.bind("<KeyRelease-Control_L>", self._cleanup_selection)
        self.bind("<KeyRelease-Control_R>", self._cleanup_selection)
        
    def _show_add_node_dialog(self):
        """显示添加节点对话框"""
        dialog = ctk.CTkInputDialog(
            text="请输入节点名称:",
            title="添加新节点"
        )
        
        node_name = dialog.get_input()
        
        if node_name:
            if node_name in self.nodes:
                self._show_error_message("节点已存在", f"名称为 '{node_name}' 的节点已存在")
                return
                
            self.add_node(
                name=node_name,
                position=(500, 500)  # 默认在窗口中间
            )
            
    def _show_error_message(self, title: str, message: str):
        """显示错误消息对话框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("300x150")
        
        dialog.transient(self)
        dialog.grab_set()
        
        label = ctk.CTkLabel(dialog, text=message, wraplength=250)
        label.pack(pady=20)
        
        button = ctk.CTkButton(dialog, text="确定", command=dialog.destroy)
        button.pack(pady=10)
        
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
    def add_node(self, name: str, position: Tuple[int, int] = (500, 500)) -> DraggableNode:
        node = DraggableNode(
            master=self,
            text=name,
            position=position,
            on_position_change=self._update_lines,
            on_select=self._on_node_select  # 添加选择回调
        )
        self.nodes[name] = node
        return node
        
    def _on_node_select(self, node: DraggableNode):
        """处理节点选择事件"""
        # 如果按住Ctrl键，添加到选择
        if self.winfo_toplevel().winfo_children()[0].focus_get() and '<Control>' in self.winfo_toplevel().winfo_children()[0].focus_get().state():
            if node in self.selected_nodes:
                # 取消选择
                self.selected_nodes.remove(node)
                node.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            else:
                # 添加到选择
                self._add_to_selection(node)
        else:
            # 清除其他选择
            self._clear_selection()
            self._add_to_selection(node)
            
    def _clear_selection(self):
        """清除所有选择"""
        for node in self.selected_nodes:
            node.configure(fg_color=["#3B8ED0", "#1F6AA5"])
        self.selected_nodes.clear()
        self.delete_button.configure(
            state="disabled",
            fg_color="#666666",
            hover_color="#444444"
        )
        
    def _on_canvas_click(self, event):
        """处理画布点击事件"""
        # 点击空白处取消所有选择
        # 检查是否点击到了节点
        clicked_widget = event.widget.winfo_containing(event.x_root, event.y_root)
        if clicked_widget == self.canvas:  # 只有点击到画布空白处才清除选择
            self._clear_selection()
            
    def _cleanup_selection(self, event=None):
        """清理选择框"""
        if self.selection_box:
            try:
                self.canvas.delete(self.selection_box)
            except:
                pass  # 忽略可能的删除错误
            finally:
                self.selection_box = None
                self.is_selecting = False
                self.selection_start = None
        
    def _on_selection_start(self, event):
        """开始框选"""
        if not self.is_selecting:  # 只有在没有选择进行时才开始新的选择
            self.selection_start = (event.x, event.y)
            self.is_selecting = True
            self.selection_box = self.canvas.create_rectangle(
                event.x, event.y, event.x, event.y,
                outline="#ff9f4a",
                width=2,
                dash=(4, 4)
            )
        
    def _on_selection_drag(self, event):
        """更新选择框"""
        if self.is_selecting and self.selection_box:
            try:
                # 获取鼠标当前位置相对于画布的坐标
                canvas_x = self.canvas.canvasx(event.x)
                canvas_y = self.canvas.canvasy(event.y)
                
                # 更新选择框
                self.canvas.coords(
                    self.selection_box,
                    self.selection_start[0], self.selection_start[1],
                    canvas_x, canvas_y
                )
            except:
                pass  # 忽略可能的坐标错误，但不清除选择框
            
    def _on_selection_end(self, event):
        """结束框选"""
        if not self.is_selecting:
            return
            
        try:
            # 获取选择框范围
            x1, y1 = self.selection_start
            x2, y2 = event.x, event.y
            
            # 确保坐标正确排序
            left = min(x1, x2)
            right = max(x1, x2)
            top = min(y1, y2)
            bottom = max(y1, y2)
            
            # 检查节点是否在选择框内
            for node in self.nodes.values():
                node_x = node.winfo_x() + node.winfo_width() / 2
                node_y = node.winfo_y() + node.winfo_height() / 2
                
                if (left <= node_x <= right and top <= node_y <= bottom):
                    self._add_to_selection(node)
        except Exception as e:
            print(f"Selection error: {e}")  # 添加错误日志
            
        # 注意：这里不清理选择框，等待Ctrl键释放时清理
        
    def _add_to_selection(self, node: DraggableNode):
        """添加节点到选择集合"""
        self.selected_nodes.add(node)
        node.configure(fg_color=["#ff9f4a", "#ff7f24"])
        
        # 启用删除按钮
        self.delete_button.configure(
            state="normal",
            fg_color=["#DC3545", "#B02A37"],
            hover_color=["#BB2D3B", "#8B222C"]
        )
        
    def _delete_selected_node(self):
        """删除选中的节点"""
        if not self.selected_nodes:
            return
            
        # 删除所有选中的节点
        for node in list(self.selected_nodes):
            # 获取要删除的节点名称
            node_name = node.cget("text")
            
            # 删除与该节点相关的所有连线
            lines_to_delete = []
            for line_id, (source_node, target_node) in self.connection_lines.items():
                if source_node == node or target_node == node:
                    lines_to_delete.append(line_id)
                    
            for line_id in lines_to_delete:
                self._delete_connection(line_id)
            
            # 从节点字典中移除
            if node_name in self.nodes:
                del self.nodes[node_name]
            
            # 销毁节点控件
            node.destroy()
        
        # 清除选择状态
        self.selected_nodes.clear()
        
        # 禁用删除按钮
        self.delete_button.configure(
            state="disabled",
            fg_color="#666666",
            hover_color="#444444"
        )
        
    def find_target_anchor(self, source_node: DraggableNode) -> Optional[Tuple[DraggableNode, AnchorPoint]]:
        """查找目标吸附点"""
        mouse_x = self.winfo_pointerx() - self.winfo_rootx()
        mouse_y = self.winfo_pointery() - self.winfo_rooty()
        
        closest_anchor = None
        min_distance = float('inf')
        SNAP_DISTANCE = 20
        
        for node in self.nodes.values():
            if node == source_node:
                continue
                
            for anchor in node.anchor_points.values():
                ax, ay = node.get_anchor_coords(anchor)
                distance = math.sqrt((mouse_x - ax) ** 2 + (mouse_y - ay) ** 2)
                
                if distance < SNAP_DISTANCE and distance < min_distance:
                    min_distance = distance
                    closest_anchor = (node, anchor)
        
        if self.highlighted_anchor and self.highlighted_anchor != closest_anchor:
            self.highlighted_anchor[1].unhighlight()
            
        if closest_anchor:
            closest_anchor[1].highlight()
            self.highlighted_anchor = closest_anchor
        elif self.highlighted_anchor:
            self.highlighted_anchor[1].unhighlight()
            self.highlighted_anchor = None
            
        return closest_anchor
        
    def _on_canvas_motion(self, event):
        for node in self.nodes.values():
            if hasattr(node, 'active_connection') and node.active_connection:
                self.find_target_anchor(node)
                break
                
    def create_connection(self, source_node: DraggableNode, target_node: DraggableNode):
        """创建节点间的连线"""
        # 获取节点中心点
        source_center = (
            source_node.winfo_x() + source_node.winfo_width() / 2,
            source_node.winfo_y() + source_node.winfo_height() / 2
        )
        target_center = (
            target_node.winfo_x() + target_node.winfo_width() / 2,
            target_node.winfo_y() + target_node.winfo_height() / 2
        )
        
        # 获取路径点
        points = source_node._get_control_points(
            *source_center,
            *target_center,
            target_node
        )
        
        # 创建折线
        line = self.canvas.create_line(
            *[coord for point in points for coord in point],
            fill="#4a9eff",
            width=2,
            arrow="last",
            arrowshape=(16, 20, 6),
            tags="connection"
        )
        
        # 存储连线信息
        self.connections.add((source_node, target_node))
        self.connection_lines[line] = (source_node, target_node)
        
        # 创建删除按钮
        self._create_delete_button(line)
        
    def _create_delete_button(self, line_id: int):
        btn = ctk.CTkButton(
            self,
            text="×",
            width=20,
            height=20,
            command=lambda: self._delete_connection(line_id)
        )
        coords = self.canvas.coords(line_id)
        x = (coords[0] + coords[2]) / 2
        y = (coords[1] + coords[3]) / 2
        btn.place(x=x, y=y)
        
    def _delete_connection(self, line_id: int):
        if line_id in self.connection_lines:
            connection = self.connection_lines[line_id]
            self.connections.remove(connection)
            del self.connection_lines[line_id]
            self.canvas.delete(line_id)
            
    def _update_lines(self, node: Optional[DraggableNode] = None):
        """更新所有连线位置"""
        # 删除所有现有的连线
        for line_id in list(self.connection_lines.keys()):
            self.canvas.delete(line_id)
            
        # 重新创建所有连线
        for source_node, target_node in self.connections:
            # 获取节点中心点
            source_center = (
                source_node.winfo_x() + source_node.winfo_width() / 2,
                source_node.winfo_y() + source_node.winfo_height() / 2
            )
            target_center = (
                target_node.winfo_x() + target_node.winfo_width() / 2,
                target_node.winfo_y() + target_node.winfo_height() / 2
            )
            
            # 获取路径点
            points = source_node._get_control_points(
                *source_center,
                *target_center,
                target_node
            )
            
            # 创建新的连线
            line = self.canvas.create_line(
                *[coord for point in points for coord in point],
                fill="#4a9eff",
                width=2,
                arrow="last",
                arrowshape=(16, 20, 6),
                tags="connection"
            )
            
            # 更新连线信息
            self.connection_lines[line] = (source_node, target_node)
            
            # 更新删除按钮位置
            x = (source_center[0] + target_center[0]) / 2
            y = (source_center[1] + target_center[1]) / 2
            for child in self.winfo_children():
                if isinstance(child, ctk.CTkButton) and child.cget("text") == "×":
                    child.place(x=x, y=y)
                    
    def _on_canvas_right_click(self, event):
        """处理画布右键点击事件"""
        pass 
    
    def create_dependency(self, source_name: str, target_name: str, 
                         source_pos: Tuple[int, int] = None,
                         target_pos: Tuple[int, int] = None):
        """创建依赖关系"""
        # 获取或创建节点
        if source_name in self.nodes:
            source_node = self.nodes[source_name]
        else:
            if source_pos is None:
                source_pos = (300, 500)
            source_node = self.add_node(source_name, source_pos)
            
        if target_name in self.nodes:
            target_node = self.nodes[target_name]
        else:
            if target_pos is None:
                target_pos = (500, 500)
            target_node = self.add_node(target_name, target_pos)
            
        # 创建连线
        self.create_connection(source_node, target_node)
        
    def create_dependencies_from_yaml(self, dependencies: List[Tuple[str, str]]):
        """从YAML依赖关系创建节点和连线
        
        Args:
            dependencies: 依赖关系列表，每个元素为(依赖任务, 当前任务)的元组
        """
        # 计算节点位置
        node_positions = self._calculate_node_positions(dependencies)
        
        # 创建所有依赖关系
        for dep_from, dep_to in dependencies:
            self.create_dependency(
                dep_from, dep_to,
                source_pos=node_positions.get(dep_from),
                target_pos=node_positions.get(dep_to)
            )
            
    def _calculate_node_positions(self, dependencies: List[Tuple[str, str]]) -> Dict[str, Tuple[int, int]]:
        """计算节点的合适位置
        
        Args:
            dependencies: 依赖关系列表
            
        Returns:
            Dict[str, Tuple[int, int]]: 节点名称到位置的映射
        """
        # 收集所有唯一的节点名称
        nodes = set()
        for dep_from, dep_to in dependencies:
            nodes.add(dep_from)
            nodes.add(dep_to)
            
        # 计算每个节点的层级（最长路径）
        levels: Dict[str, int] = {}
        
        def calculate_level(node: str, visited: set) -> int:
            if node in levels:
                return levels[node]
            if node in visited:
                return 0
                
            visited.add(node)
            max_level = 0
            for dep_from, dep_to in dependencies:
                if dep_to == node:
                    level = calculate_level(dep_from, visited) + 1
                    max_level = max(max_level, level)
            visited.remove(node)
            
            levels[node] = max_level
            return max_level
            
        # 计算每个节点的层级
        for node in nodes:
            if node not in levels:
                calculate_level(node, set())
                
        # 根据层级分配位置
        positions = {}
        level_counts = {}  # 每个层级的节点数量
        level_current = {}  # 每个层级当前的节点索引
        
        # 计算每个层级的节点数量
        for node, level in levels.items():
            level_counts[level] = level_counts.get(level, 0) + 1
            
        # 初始化当前索引
        for level in level_counts:
            level_current[level] = 0
            
        # 分配位置
        window_width = 800  # 窗口宽度
        window_height = 600  # 窗口高度
        horizontal_spacing = window_width / (max(levels.values()) + 2)  # 水平间距
        
        for node, level in sorted(levels.items(), key=lambda x: (x[1], x[0])):
            count = level_counts[level]
            current = level_current[level]
            
            # 计算位置
            x = (level + 1) * horizontal_spacing
            if count > 1:
                vertical_spacing = window_height / (count + 1)
                y = (current + 1) * vertical_spacing
            else:
                y = window_height / 2
                
            positions[node] = (int(x), int(y))
            level_current[level] += 1
            
        return positions