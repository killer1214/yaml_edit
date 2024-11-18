import tkinter as tk
from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from common.graph_node import DraggableNode

class AnchorPoint(tk.Canvas):
    """吸附点类"""
    def __init__(
        self,
        master: any,
        node: 'DraggableNode',
        position: str,
        size: int = 12,
        **kwargs
    ):
        super().__init__(
            master=master,
            width=size,
            height=size,
            bg="#2b2b2b",
            highlightthickness=0
        )
        
        self.node = node
        self.position = position
        self.size = size
        self.active = False
        
        # 创建更大的圆形吸附点
        padding = 2
        self.circle = self.create_oval(
            padding, padding,
            size-padding, size-padding,
            fill="#4a9eff",
            outline="#ffffff",
            width=1.5
        )
        
        # 绑定事件
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        
    def _on_enter(self, event):
        self.itemconfig(self.circle, fill="#ff9f4a", outline="#ffffff", width=2)
        
    def _on_leave(self, event):
        if not self.active:
            self.itemconfig(self.circle, fill="#4a9eff", outline="#ffffff", width=1)
            
    def _on_click(self, event):
        self.active = True
        self.itemconfig(self.circle, fill="#ff9f4a", outline="#ffffff", width=2)
        self.node.start_connection(self)
        
    def _on_drag(self, event):
        if self.active:
            x = event.x_root - self.node.master.winfo_rootx()
            y = event.y_root - self.node.master.winfo_rooty()
            self.node.update_temp_connection(x, y)
            
    def _on_release(self, event):
        self.active = False
        self.itemconfig(self.circle, fill="#4a9eff", outline="#ffffff", width=1)
        self.node.end_connection()
        
    def highlight(self):
        """高亮显示吸附点"""
        self.itemconfig(
            self.circle,
            fill="#ff9f4a",
            outline="#ffffff",
            width=2.5
        )
        
    def unhighlight(self):
        """取消高亮"""
        self.itemconfig(
            self.circle,
            fill="#4a9eff",
            outline="#ffffff",
            width=1.5
        )
        
    def get_coords(self) -> Tuple[int, int]:
        """获取吸附点的全局坐标"""
        return (
            self.winfo_rootx() + self.size/2 - self.node.master.winfo_rootx(),
            self.winfo_rooty() + self.size/2 - self.node.master.winfo_rooty()
        ) 