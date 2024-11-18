import tkinter as tk
import customtkinter as ctk
from typing import Tuple, Optional, Callable, Dict, Set, List

class AnchorPoint(tk.Canvas):
    """吸附点类"""
    def __init__(
        self,
        master: any,
        position: str,  # 'top', 'bottom', 'left', 'right'
        size: int = 6,
        **kwargs
    ):
        super().__init__(
            master=master,
            width=size,
            height=size,
            bg="#4a9eff",
            highlightthickness=0,
            **kwargs
        )
        
        self.position = position
        self.size = size
        self.active = False
        
        # 绑定事件
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        
    def _on_enter(self, event):
        self.configure(bg="#ff9f4a")
        
    def _on_leave(self, event):
        if not self.active:
            self.configure(bg="#4a9eff")
            
    def _on_click(self, event):
        self.active = True
        # 通知父节点开始连线
        self.master.start_connection(self)
        
    def _on_drag(self, event):
        if self.active:
            # 通知父节点更新临时连线
            x = self.winfo_rootx() + event.x - self.master.winfo_rootx()
            y = self.winfo_rooty() + event.y - self.master.winfo_rooty()
            self.master.update_temp_connection(x, y)
            
    def _on_release(self, event):
        self.active = False
        self.configure(bg="#4a9eff")
        # 通知父节点结束连线
        self.master.end_connection()

class DraggableNode(ctk.CTkButton):
    def __init__(self, master: any, text: str, position: Tuple[int, int] = (0, 0),
                 size: Tuple[int, int] = (100, 40), on_position_change: Optional[Callable] = None, **kwargs):
        super().__init__(
            master=master,
            text=text,
            width=size[0],
            height=size[1],
            **kwargs
        )
        
        self.position = position
        self.size = size
        self.on_position_change = on_position_change
        
        # 创建吸附点
        self.anchor_points = {
            'top': AnchorPoint(self, 'top'),
            'bottom': AnchorPoint(self, 'bottom'),
            'left': AnchorPoint(self, 'left'),
            'right': AnchorPoint(self, 'right')
        }
        
        self._update_anchor_positions()
        self.place(relx=position[0]/1000, rely=position[1]/1000, anchor="center")
        
        # 拖动相关数据
        self._drag_data = {"dragging": False, "last_x": 0, "last_y": 0}
        
        # 当前活动的连线
        self.active_connection = None
        self.temp_line = None
        
        # 绑定事件
        self.bind("<Button-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.bind("<ButtonRelease-1>", self._on_drag_stop)
        
    def _update_anchor_positions(self):
        """更新吸附点位置"""
        w, h = self.size
        for pos, point in self.anchor_points.items():
            if pos == 'top':
                point.place(x=w/2-3, y=-3)
            elif pos == 'bottom':
                point.place(x=w/2-3, y=h-3)
            elif pos == 'left':
                point.place(x=-3, y=h/2-3)
            elif pos == 'right':
                point.place(x=w-3, y=h/2-3)
                
    def start_connection(self, anchor: AnchorPoint):
        """开始创建连线"""
        self.active_connection = anchor
        # 创建临时连线
        self.temp_line = self.master.canvas.create_line(
            self.get_anchor_coords(anchor),
            self.get_anchor_coords(anchor),
            fill="#4a9eff",
            width=2
        )
        
    def update_temp_connection(self, x: int, y: int):
        """更新临时连线"""
        if self.temp_line:
            start_x, start_y = self.get_anchor_coords(self.active_connection)
            self.master.canvas.coords(
                self.temp_line,
                start_x, start_y, x, y
            )
            
    def end_connection(self):
        """结束连线"""
        if self.temp_line:
            # 检查是否有目标吸附点
            target = self.master.find_target_anchor(self)
            if target:
                # 创建永久连线
                self.master.create_connection(self, self.active_connection, target[0], target[1])
            # 删除临时连线
            self.master.canvas.delete(self.temp_line)
            self.temp_line = None
            self.active_connection = None
            
    def get_anchor_coords(self, anchor: AnchorPoint) -> Tuple[int, int]:
        """获取吸附点的全局坐标"""
        return (
            self.winfo_rootx() + anchor.winfo_x() + anchor.size/2 - self.master.winfo_rootx(),
            self.winfo_rooty() + anchor.winfo_y() + anchor.size/2 - self.master.winfo_rooty()
        )
        
    def _on_drag_start(self, event):
        """开始拖动"""
        self._drag_data["dragging"] = True
        self._drag_data["last_x"] = event.x_root
        self._drag_data["last_y"] = event.y_root
        
    def _on_drag_motion(self, event):
        """拖动过程中"""
        if not self._drag_data["dragging"]:
            return
            
        # 计算移动的相对距离
        delta_x = event.x_root - self._drag_data["last_x"]
        delta_y = event.y_root - self._drag_data["last_y"]
        
        # 更新最后位置
        self._drag_data["last_x"] = event.x_root
        self._drag_data["last_y"] = event.y_root
        
        # 获取当前相对位置
        current_relx = float(self.place_info()['relx'])
        current_rely = float(self.place_info()['rely'])
        
        # 计算新的相对位置
        new_relx = current_relx + delta_x / self.master.winfo_width()
        new_rely = current_rely + delta_y / self.master.winfo_height()
        
        # 确保节点不会被拖出窗口
        new_relx = max(0, min(new_relx, 1))
        new_rely = max(0, min(new_rely, 1))
        
        # 更新位置
        self.place(relx=new_relx, rely=new_rely, anchor="center")
        self.position = (new_relx * 1000, new_rely * 1000)
        
        # 调用回调函数
        if self.on_position_change:
            self.on_position_change(self)
            
    def _on_drag_stop(self, event):
        """停止拖动"""
        self._drag_data["dragging"] = False

class GraphWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("任务依赖图")
        self.geometry("800x600")
        
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
        
        # 绑定画布事件
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)
        
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
        
        for node in self.nodes.values():
            if node == source_node:
                continue
            for anchor in node.anchor_points.values():
                ax, ay = node.get_anchor_coords(anchor)
                # 检查鼠标是否在吸附点范围内
                if abs(mouse_x - ax) < 10 and abs(mouse_y - ay) < 10:
                    return (node, anchor)
        return None
        
    def create_connection(self, source_node: DraggableNode, source_anchor: AnchorPoint,
                         target_node: DraggableNode, target_anchor: AnchorPoint):
        """创建永久连线"""
        # 创建连线
        line = self.canvas.create_line(
            source_node.get_anchor_coords(source_anchor),
            target_node.get_anchor_coords(target_anchor),
            fill="#4a9eff",
            width=2,
            tags="connection"
        )
        
        # 存储连线信息
        self.connections.add((source_node, source_anchor, target_node, target_anchor))
        self.connection_lines[line] = (source_node, source_anchor, target_node, target_anchor)
        
        # 创建删除按钮
        self._create_delete_button(line)
        
    def _create_delete_button(self, line_id: int):
        """为连线创建删除按钮"""
        btn = ctk.CTkButton(
            self,
            text="×",
            width=20,
            height=20,
            command=lambda: self._delete_connection(line_id)
        )
        # 计算按钮位置
        coords = self.canvas.coords(line_id)
        x = (coords[0] + coords[2]) / 2
        y = (coords[1] + coords[3]) / 2
        btn.place(x=x, y=y)
        
    def _delete_connection(self, line_id: int):
        """删除连线"""
        if line_id in self.connection_lines:
            connection = self.connection_lines[line_id]
            self.connections.remove(connection)
            del self.connection_lines[line_id]
            self.canvas.delete(line_id)
            
    def _update_lines(self, node: Optional[DraggableNode] = None):
        """更新所有连线位置"""
        for line_id, (source_node, source_anchor, target_node, target_anchor) in self.connection_lines.items():
            # 更新连线坐标
            self.canvas.coords(
                line_id,
                *source_node.get_anchor_coords(source_anchor),
                *target_node.get_anchor_coords(target_anchor)
            )
            # 更新删除按钮位置
            coords = self.canvas.coords(line_id)
            x = (coords[0] + coords[2]) / 2
            y = (coords[1] + coords[3]) / 2
            for child in self.winfo_children():
                if isinstance(child, ctk.CTkButton) and child.cget("text") == "×":
                    child.place(x=x, y=y)
                    
    def _on_canvas_right_click(self, event):
        """画布右键点击事件"""
        pass

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
        position=(300, 500)  # 在窗口30%宽度，50%高度的位置
    )
    
    node2 = app.add_node(
        name="结束节点",
        position=(700, 500)  # 在窗口70%宽度，50%高度的位置
    )
    
    # 启动主循环
    app.mainloop()

if __name__ == "__main__":
    main()
