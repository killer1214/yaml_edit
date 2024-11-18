import customtkinter as ctk
from typing import Tuple, Optional, Callable, Dict
import math

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
        
        self.place(relx=position[0]/1000, rely=position[1]/1000, anchor="center")
        
        self.after(10, self._create_anchor_points)
        
        self._drag_data = {"dragging": False, "last_x": 0, "last_y": 0}
        
        self.bind("<Button-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.bind("<ButtonRelease-1>", self._on_drag_stop)
        self.bind("<Configure>", self._on_configure)
        
    def _create_anchor_points(self):
        self.anchor_points = {
            'top': AnchorPoint(master=self, node=self, position='top'),
            'bottom': AnchorPoint(master=self, node=self, position='bottom'),
            'left': AnchorPoint(master=self, node=self, position='left'),
            'right': AnchorPoint(master=self, node=self, position='right')
        }
        self._update_anchor_positions()
        
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
        self.active_connection = anchor
        self.temp_line = self.master.canvas.create_line(
            *self.get_anchor_coords(anchor),
            *self.get_anchor_coords(anchor),
            fill="#4a9eff",
            width=2,
            smooth=True,
            arrow="last",
            arrowshape=(16, 20, 6)
        )
        
    def update_temp_connection(self, x: int, y: int):
        if self.temp_line:
            start_x, start_y = self.get_anchor_coords(self.active_connection)
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
            
            self.master.canvas.coords(
                self.temp_line,
                start_x, start_y,
                ctrl_x1, ctrl_y1,
                ctrl_x2, ctrl_y2,
                x, y
            )
            
    def _get_control_point(self, x1: int, y1: int, x2: int, y2: int, anchor_pos: str) -> Tuple[int, int]:
        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx * dx + dy * dy)
        ctrl_distance = distance / 3
        
        if anchor_pos == 'top':
            return (x1, y1 - ctrl_distance)
        elif anchor_pos == 'bottom':
            return (x1, y1 + ctrl_distance)
        elif anchor_pos == 'left':
            return (x1 - ctrl_distance, y1)
        elif anchor_pos == 'right':
            return (x1 + ctrl_distance, y1)
        elif anchor_pos == 'opposite':
            dx = x2 - x1
            dy = y2 - y1
            
            if abs(dx) > abs(dy):
                if dx > 0:
                    return (x2 - ctrl_distance, y2)
                else:
                    return (x2 + ctrl_distance, y2)
            else:
                if dy > 0:
                    return (x2, y2 - ctrl_distance)
                else:
                    return (x2, y2 + ctrl_distance)
        
        return (x1, y1)
        
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
        self._drag_data["dragging"] = True
        self._drag_data["last_x"] = event.x_root
        self._drag_data["last_y"] = event.y_root
        
    def _on_drag_stop(self, event):
        self._drag_data["dragging"] = False 