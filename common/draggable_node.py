import customtkinter as ctk
from typing import Tuple, Optional, Callable, Dict, List
import math

from common.anchor_point import AnchorPoint

class DraggableNode(ctk.CTkButton):
    def __init__(self, master: any, text: str, position: Tuple[int, int] = (0, 0),
                 size: Tuple[int, int] = (100, 40), on_position_change: Optional[Callable] = None,
                 on_select: Optional[Callable] = None, **kwargs):
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
        self.on_select = on_select
        
        # 先创建吸附点
        self.anchor_points = {
            'top': AnchorPoint(master=self, node=self, position='top'),
            'bottom': AnchorPoint(master=self, node=self, position='bottom'),
            'left': AnchorPoint(master=self, node=self, position='left'),
            'right': AnchorPoint(master=self, node=self, position='right')
        }
        
        # 然后放置节点
        self.place(relx=position[0]/1000, rely=position[1]/1000, anchor="center")
        
        # 更新吸附点位置
        self._update_anchor_positions()
        
        self._drag_data = {"dragging": False, "last_x": 0, "last_y": 0}
        
        # 绑定事件
        self.bind("<Button-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.bind("<ButtonRelease-1>", self._on_drag_stop)
        self.bind("<Configure>", self._on_configure)
        
    def _update_anchor_positions(self):
        if not hasattr(self, 'anchor_points'):
            return
            
        w = self.winfo_width()
        h = self.winfo_height()
        
        positions = {
            'top': (w/2, 0),
            'bottom': (w/2, h),
            'left': (0, h/2),
            'right': (w, h/2)
        }
        
        for pos, point in self.anchor_points.items():
            x, y = positions[pos]
            point.place(x=x, y=y, anchor='center')
            
    def _on_drag_motion(self, event):
        if not self._drag_data["dragging"]:
            return
            
        delta_x = event.x_root - self._drag_data["last_x"]
        delta_y = event.y_root - self._drag_data["last_y"]
        
        self._drag_data["last_x"] = event.x_root
        self._drag_data["last_y"] = event.y_root
        
        current_relx = float(self.place_info()['relx'])
        current_rely = float(self.place_info()['rely'])
        
        new_relx = current_relx + delta_x / self.master.winfo_width()
        new_rely = current_rely + delta_y / self.master.winfo_height()
        
        new_relx = max(0, min(new_relx, 1))
        new_rely = max(0, min(new_rely, 1))
        
        self.place(relx=new_relx, rely=new_rely, anchor="center")
        self.position = (new_relx * 1000, new_rely * 1000)
        
        self._update_anchor_positions()
        
        if self.on_position_change:
            self.on_position_change(self)
            
    def _on_configure(self, event):
        self._update_anchor_positions()
        
    def start_connection(self, anchor: AnchorPoint):
        """开始创建连线"""
        self.active_connection = anchor
        # 创建临时折线
        start_x, start_y = self.get_anchor_coords(anchor)
        self.temp_line = self.master.canvas.create_line(
            start_x, start_y,  # 起点
            start_x, start_y,  # 初始时折点和终点重合
            start_x, start_y,
            fill="#4a9eff",
            width=2,
            arrow="last",
            arrowshape=(16, 20, 6),
            dash=(4, 4)  # 添加虚线效果
        )
        
    def update_temp_connection(self, x: int, y: int):
        """更新临时连线"""
        if not self.temp_line:
            return
            
        start_x, start_y = self.get_anchor_coords(self.active_connection)
        
        # 根据起点吸附点的位置和鼠标位置计算转折点
        if self.active_connection.position == 'top':
            if y < start_y:  # 向上拖动
                mid_point = (start_x, y)
            else:  # 向下拖动
                mid_y = (start_y + y) / 2
                mid_point = (start_x, mid_y)
                self.master.canvas.coords(
                    self.temp_line,
                    start_x, start_y,      # 起点
                    start_x, mid_y,        # 第一个转折点
                    x, mid_y,              # 第二个转折点
                    x, y                   # 终点
                )
                return
                
        elif self.active_connection.position == 'bottom':
            if y > start_y:  # 向下拖动
                mid_point = (start_x, y)
            else:  # 向上拖动
                mid_y = (start_y + y) / 2
                mid_point = (start_x, mid_y)
                self.master.canvas.coords(
                    self.temp_line,
                    start_x, start_y,
                    start_x, mid_y,
                    x, mid_y,
                    x, y
                )
                return
                
        elif self.active_connection.position == 'left':
            if x < start_x:  # 向左拖动
                mid_point = (x, start_y)
            else:  # 向右拖动
                mid_x = (start_x + x) / 2
                mid_point = (mid_x, start_y)
                self.master.canvas.coords(
                    self.temp_line,
                    start_x, start_y,
                    mid_x, start_y,
                    mid_x, y,
                    x, y
                )
                return
                
        elif self.active_connection.position == 'right':
            if x > start_x:  # 向右拖动
                mid_point = (x, start_y)
            else:  # 向左拖动
                mid_x = (start_x + x) / 2
                mid_point = (mid_x, start_y)
                self.master.canvas.coords(
                    self.temp_line,
                    start_x, start_y,
                    mid_x, start_y,
                    mid_x, y,
                    x, y
                )
                return
                
        # 默认情况：直接连接到鼠标位置
        self.master.canvas.coords(
            self.temp_line,
            start_x, start_y,  # 起点
            mid_point[0], mid_point[1],  # 转折点
            x, y  # 终点
        )
        
    def end_connection(self):
        if self.temp_line:
            target = self.master.find_target_anchor(self)
            if target:
                self.master.create_connection(self, self.active_connection, target[0], target[1])
            self.master.canvas.delete(self.temp_line)
            self.temp_line = None
            self.active_connection = None
            
    def get_anchor_coords(self, anchor: AnchorPoint) -> Tuple[int, int]:
        return anchor.get_coords()
        
    def _on_drag_start(self, event):
        """开始拖动时也触发选择事件"""
        self._drag_data["dragging"] = True
        self._drag_data["last_x"] = event.x_root
        self._drag_data["last_y"] = event.y_root
        
        # 触发选择回调
        if self.on_select:
            self.on_select(self)
        
    def _on_drag_stop(self, event):
        self._drag_data["dragging"] = False 
        
    def get_edge_point(self, target_x: int, target_y: int) -> Tuple[int, int]:
        """计算连线与节点边缘的交点，考��分辨率和缩放"""
        # 获取节点的实际位置和尺寸
        node_x = self.winfo_x()
        node_y = self.winfo_y()
        node_width = self.winfo_width()
        node_height = self.winfo_height()
        
        # 计算节点中心点
        center_x = node_x + node_width / 2
        center_y = node_y + node_height / 2
        
        # 计算方向向量
        dx = target_x - center_x
        dy = target_y - center_y
        
        # 获取缩放因子
        try:
            scaling = self._get_window_scaling()
        except:
            scaling = 1.0
            
        # 调整节点尺寸（考虑缩放）
        half_width = (node_width / 2) / scaling
        half_height = (node_height / 2) / scaling
        
        # 计算出射点
        if abs(dx) == 0 and abs(dy) == 0:
            # 如果目标点就是中心点，默认从右边出发
            return (center_x + half_width, center_y)
            
        # 计算角度（相对于水平线）
        angle = math.atan2(dy, dx)
        
        # 根据角度确定出射点
        if abs(math.cos(angle)) * half_height > abs(math.sin(angle)) * half_width:
            # 从左右边缘出发
            x = center_x + (half_width if dx > 0 else -half_width)
            y = center_y + math.tan(angle) * (half_width)
        else:
            # 从上下边缘出发
            y = center_y + (half_height if dy > 0 else -half_height)
            x = center_x + (half_height / math.tan(angle) if math.tan(angle) != 0 else 0)
            
        return (x, y)
        
    def _get_window_scaling(self) -> float:
        """获取窗口缩放因子"""
        try:
            # 对于Windows系统
            from ctypes import windll
            return windll.shcore.GetScaleFactorForDevice(0) / 100
        except:
            # 对于其他系统，使用tk的缩放因子
            return self.winfo_fpixels('1i') / 72
        
    def _get_control_points(self, x1: int, y1: int, x2: int, y2: int, target_node: 'DraggableNode') -> List[Tuple[int, int]]:
        """计算连线的控制点，优化连线路径"""
        # 计算两个节点的边缘点
        start_point = self.get_edge_point(x2, y2)
        end_point = target_node.get_edge_point(x1, y1)
        
        # 计算方向向量
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        
        # 计算转折点
        # 使用1/3和2/3位置作为转折点，使连线更平滑
        first_x = start_point[0] + dx / 3
        second_x = start_point[0] + dx * 2 / 3
        
        # 返回路径点
        return [
            start_point,
            (first_x, start_point[1]),   # 第一个转折点
            (second_x, end_point[1]),    # 第二个转折点
            end_point
        ]
        