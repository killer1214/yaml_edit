import tkinter as tk
import customtkinter as ctk
from typing import Dict, Set, Tuple, Optional
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
        
        # 创建画布
        self.canvas = tk.Canvas(
            self,
            bg="#2b2b2b",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # 存储节点和连线
        self.nodes: Dict[str, DraggableNode] = {}
        self.connections: Set[Tuple[DraggableNode, AnchorPoint, DraggableNode, AnchorPoint]] = set()
        self.connection_lines: Dict[int, Tuple[DraggableNode, AnchorPoint, DraggableNode, AnchorPoint]] = {}
        
        # 当前高亮的吸附点
        self.highlighted_anchor = None
        
        # 绑定画布事件
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        
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
            on_position_change=self._update_lines
        )
        self.nodes[name] = node
        return node
        
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
                
    def create_connection(self, source_node: DraggableNode, source_anchor: AnchorPoint,
                         target_node: DraggableNode, target_anchor: AnchorPoint):
        """创建永久连线"""
        for connection in self.connections:
            if (connection[0] == source_node and connection[1] == source_anchor and
                connection[2] == target_node and connection[3] == target_anchor):
                return
        
        if self.highlighted_anchor:
            self.highlighted_anchor[1].unhighlight()
            self.highlighted_anchor = None
            
        start_x, start_y = source_node.get_anchor_coords(source_anchor)
        end_x, end_y = target_node.get_anchor_coords(target_anchor)
        
        ctrl_x1, ctrl_y1 = source_node._get_control_point(
            start_x, start_y,
            end_x, end_y,
            source_anchor.position
        )
        ctrl_x2, ctrl_y2 = source_node._get_control_point(
            end_x, end_y,
            start_x, start_y,
            'opposite'
        )
        
        line = self.canvas.create_line(
            start_x, start_y,
            ctrl_x1, ctrl_y1,
            ctrl_x2, ctrl_y2,
            end_x, end_y,
            fill="#4a9eff",
            width=2,
            smooth=True,
            arrow="last",
            arrowshape=(16, 20, 6),
            tags="connection"
        )
        
        self.connections.add((source_node, source_anchor, target_node, target_anchor))
        self.connection_lines[line] = (source_node, source_anchor, target_node, target_anchor)
        
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
        for line_id, (source_node, source_anchor, target_node, target_anchor) in self.connection_lines.items():
            start_x, start_y = source_node.get_anchor_coords(source_anchor)
            end_x, end_y = target_node.get_anchor_coords(target_anchor)
            
            ctrl_x1, ctrl_y1 = source_node._get_control_point(
                start_x, start_y,
                end_x, end_y,
                source_anchor.position
            )
            ctrl_x2, ctrl_y2 = source_node._get_control_point(
                end_x, end_y,
                start_x, start_y,
                'opposite'
            )
            
            self.canvas.coords(
                line_id,
                start_x, start_y,
                ctrl_x1, ctrl_y1,
                ctrl_x2, ctrl_y2,
                end_x, end_y
            )
            
            x = (start_x + end_x) / 2
            y = (start_y + end_y) / 2
            for child in self.winfo_children():
                if isinstance(child, ctk.CTkButton) and child.cget("text") == "×":
                    child.place(x=x, y=y)
                    
    def _on_canvas_right_click(self, event):
        pass 