import sys
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
from typing import Tuple, Optional, Callable, Dict, Set, List
import math

sys.path.append(str(Path(__file__).parent.parent))
from common.anchor_point import AnchorPoint

class DraggableNode(ctk.CTkButton):
    def __init__(self, master: any, text: str, position: Tuple[int, int] = (0, 0),
                 size: Tuple[int, int] = (100, 40), on_position_change: Optional[Callable] = None, **kwargs):
        super().__init__(
            master=master,
            text=text,
            width=size[0],
            height=size[1],
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            **kwargs
        )
        
        self.position = position
        self.size = size
        self.on_position_change = on_position_change
        
        # 先放置节点
        self.place(relx=position[0]/1000, rely=position[1]/1000, anchor="center")
        
        # 等待节点渲染完成后再创建吸附点
        self.after(10, self._create_anchor_points)
        
        # 拖动相关数据
        self._drag_data = {"dragging": False, "last_x": 0, "last_y": 0}
        
        # 绑定事件
        self.bind("<Button-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.bind("<ButtonRelease-1>", self._on_drag_stop)
        self.bind("<Configure>", self._on_configure)
        
    def _create_anchor_points(self):
        """创建吸附点"""
        # 创建吸附点
        self.anchor_points = {
            'top': AnchorPoint(master=self, node=self, position='top'),
            'bottom': AnchorPoint(master=self, node=self, position='bottom'),
            'left': AnchorPoint(master=self, node=self, position='left'),
            'right': AnchorPoint(master=self, node=self, position='right')
        }
        self._update_anchor_positions()
        
    def _update_anchor_positions(self):
        """更新吸附点位置"""
        if not hasattr(self, 'anchor_points'):
            return
            
        # 获取节点的实际尺寸
        w = self.winfo_width()
        h = self.winfo_height()
        
        # 吸附点位置配置（相对于节点）
        positions = {
            'top': (w/2, 0),      # 顶部中心
            'bottom': (w/2, h),    # 底部中心
            'left': (0, h/2),      # 左侧中心
            'right': (w, h/2)      # 右侧中心
        }
        
        # 更新所有吸附点位置
        for pos, point in self.anchor_points.items():
            x, y = positions[pos]
            point.place(x=x, y=y, anchor='center')
            
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
        
        # 更新吸附点位置
        self._update_anchor_positions()
        
        # 调用回调函数
        if self.on_position_change:
            self.on_position_change(self)
            
    def _on_configure(self, event):
        """窗口大小或位置改变时更新吸附点"""
        self._update_anchor_positions()
        
    def start_connection(self, anchor: AnchorPoint):
        """开始创建连线"""
        self.active_connection = anchor
        # 创建临时连线（使用平滑曲线）
        self.temp_line = self.master.canvas.create_line(
            *self.get_anchor_coords(anchor),
            *self.get_anchor_coords(anchor),
            fill="#4a9eff",
            width=2,
            smooth=True,  # 启用平滑
            arrow="last",  # 添加箭头
            arrowshape=(16, 20, 6)  # 箭头形状(长度, 总宽度, 尾部宽度)
        )
        
    def update_temp_connection(self, x: int, y: int):
        """更新临时连线"""
        if self.temp_line:
            start_x, start_y = self.get_anchor_coords(self.active_connection)
            # 计算控制点来创建平滑曲线
            ctrl_x1, ctrl_y1 = self._get_control_point(
                start_x, start_y, 
                x, y, 
                self.active_connection.position
            )
            ctrl_x2, ctrl_y2 = self._get_control_point(
                x, y,
                start_x, start_y,
                'opposite'
            )
            
            # 更新曲线坐标
            self.master.canvas.coords(
                self.temp_line,
                start_x, start_y,  # 起点
                ctrl_x1, ctrl_y1,  # 第一控制点
                ctrl_x2, ctrl_y2,  # 第二控制点
                x, y  # 终点
            )
            
    def _get_control_point(self, x1: int, y1: int, x2: int, y2: int, anchor_pos: str) -> Tuple[int, int]:
        """计算贝塞尔曲线的控制点
        
        Args:
            x1, y1: 起点坐标
            x2, y2: 终点坐标
            anchor_pos: 起点的吸附点位置
            
        Returns:
            控制点坐标
        """
        # 计算两点间的距离
        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx * dx + dy * dy)
        
        # 控制点距离为总距离的1/3，确保曲线平滑
        ctrl_distance = distance / 3
        
        if anchor_pos == 'top':
            # 从顶部吸附点垂直向上延伸
            return (x1, y1 - ctrl_distance)
            
        elif anchor_pos == 'bottom':
            # 从底部吸附点垂直向下延伸
            return (x1, y1 + ctrl_distance)
            
        elif anchor_pos == 'left':
            # 从左侧吸附点水平向左延伸
            return (x1 - ctrl_distance, y1)
            
        elif anchor_pos == 'right':
            # 从右侧吸附点水平向右延伸
            return (x1 + ctrl_distance, y1)
            
        elif anchor_pos == 'opposite':
            # 对于终点，根据起点的位置决定控制点
            # 找到最近的吸附点方向
            dx = x2 - x1
            dy = y2 - y1
            
            # 判断主导方向
            if abs(dx) > abs(dy):
                # 水平方向为主
                if dx > 0:
                    # 终点在右侧
                    return (x2 - ctrl_distance, y2)
                else:
                    # 终点在左侧
                    return (x2 + ctrl_distance, y2)
            else:
                # 垂直方向为主
                if dy > 0:
                    # 终点在下方
                    return (x2, y2 - ctrl_distance)
                else:
                    # 终点在上方
                    return (x2, y2 + ctrl_distance)
        
        return (x1, y1)
        
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
        return anchor.get_coords()
        
    def _on_drag_start(self, event):
        """开始拖动"""
        self._drag_data["dragging"] = True
        self._drag_data["last_x"] = event.x_root
        self._drag_data["last_y"] = event.y_root
        
    def _on_drag_stop(self, event):
        """停止拖动"""
        self._drag_data["dragging"] = False

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
        # 创建对话框窗口
        dialog = ctk.CTkInputDialog(
            text="请输入节点名称:",
            title="添加新节点"
        )
        
        # 获取用户输入
        node_name = dialog.get_input()
        
        if node_name:  # 如果用户输入了名称
            # 检查是否已存在同名节点
            if node_name in self.nodes:
                self._show_error_message("节点已存在", f"名称为 '{node_name}' 的节点已存在")
                return
                
            # 计算窗口中心位置
            center_x = 500  # 默认在窗口中间
            center_y = 500
            
            # 添加新节点
            self.add_node(
                name=node_name,
                position=(center_x, center_y)
            )
            
    def _show_error_message(self, title: str, message: str):
        """显示错误消息对话框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("300x150")
        
        # 设置模态
        dialog.transient(self)
        dialog.grab_set()
        
        # 添加错误消息
        label = ctk.CTkLabel(
            dialog,
            text=message,
            wraplength=250
        )
        label.pack(pady=20)
        
        # 添加确定按钮
        button = ctk.CTkButton(
            dialog,
            text="确定",
            command=dialog.destroy
        )
        button.pack(pady=10)
        
        # 居中显示
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
        SNAP_DISTANCE = 20  # 增加吸附范围
        
        for node in self.nodes.values():
            if node == source_node:
                continue
                
            for anchor in node.anchor_points.values():
                ax, ay = node.get_anchor_coords(anchor)
                # 计算鼠标到吸附点的距离
                distance = math.sqrt((mouse_x - ax) ** 2 + (mouse_y - ay) ** 2)
                
                if distance < SNAP_DISTANCE and distance < min_distance:
                    min_distance = distance
                    closest_anchor = (node, anchor)
        
        # 更新高亮状态
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
        """处理画布上的鼠标移动"""
        # 当有活动连线时，实时查找目标吸附点
        for node in self.nodes.values():
            if hasattr(node, 'active_connection') and node.active_connection:
                self.find_target_anchor(node)
                break
                
    def create_connection(self, source_node: DraggableNode, source_anchor: AnchorPoint,
                         target_node: DraggableNode, target_anchor: AnchorPoint):
        """创建永久连线"""
        # 检查是否已存在相同的连线
        for connection in self.connections:
            if (connection[0] == source_node and connection[1] == source_anchor and
                connection[2] == target_node and connection[3] == target_anchor):
                return  # 如果连线已存在，直接返回
        
        # 取消高亮
        if self.highlighted_anchor:
            self.highlighted_anchor[1].unhighlight()
            self.highlighted_anchor = None
            
        # 获取起点和终点坐标
        start_x, start_y = source_node.get_anchor_coords(source_anchor)
        end_x, end_y = target_node.get_anchor_coords(target_anchor)
        
        # 计算控制点
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
        
        # 创建平滑曲线
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
            # 获取新的坐标
            start_x, start_y = source_node.get_anchor_coords(source_anchor)
            end_x, end_y = target_node.get_anchor_coords(target_anchor)
            
            # 计算新的控制点
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
            
            # 更新曲线坐标
            self.canvas.coords(
                line_id,
                start_x, start_y,
                ctrl_x1, ctrl_y1,
                ctrl_x2, ctrl_y2,
                end_x, end_y
            )
            
            # 更新删除按钮位置
            x = (start_x + end_x) / 2
            y = (start_y + end_y) / 2
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
