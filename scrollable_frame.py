import tkinter as tk
from tkinter import ttk
import platform
from typing import Any, List, Tuple

class ScrollableFrame(tk.Frame):
    """支持垂直和水平滚动的通用滚动容器，修复鼠标滚动不响应问题"""
    # 类属性类型注解
    width: int
    height: int
    scroll_x_enabled: bool
    scroll_y_enabled: bool
    content_canvas: tk.Canvas
    content_frame: tk.Frame
    scrollbar_y: ttk.Scrollbar | None
    scrollbar_x: ttk.Scrollbar | None
    os_type: str  # 操作系统类型
    debug: bool = False  # 调试模式开关
    
    def __init__(self,
                 parent: tk.Tk | tk.Toplevel | tk.Frame,
                 width: int = 400,
                 height: int = 300,
                 scroll_x: bool = True,
                 scroll_y: bool = True,
                 debug: bool = False,** kwargs: Any) -> None:
        super().__init__(parent, width=width, height=height, **kwargs)
        
        self.debug = debug
        self.os_type = platform.system()
        
        # 配置主框架
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.width = width
        self.height = height
        self.scroll_x_enabled = scroll_x
        self.scroll_y_enabled = scroll_y
        
        # 创建内容容器
        content_container = ttk.Frame(self)
        content_container.grid(row=0, column=0, sticky="nsew")
        content_container.grid_rowconfigure(0, weight=1)
        content_container.grid_columnconfigure(0, weight=1)
        
        # 创建画布
        self.content_canvas = tk.Canvas(content_container, 
                                       highlightthickness=1, 
                                       highlightbackground="#ccc")
        self.content_canvas.grid(row=0, column=0, sticky="nsew")
        
        # 垂直滚动条
        self.scrollbar_y = ttk.Scrollbar(content_container, orient=tk.VERTICAL,
                                       command=self.content_canvas.yview)
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.scrollbar_y.grid_remove()
        self.content_canvas.configure(yscrollcommand=self.scrollbar_y.set)
        
        # 水平滚动条
        self.scrollbar_x = ttk.Scrollbar(content_container, orient=tk.HORIZONTAL,
                                       command=self.content_canvas.xview)
        self.scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.scrollbar_x.grid_remove()
        self.content_canvas.configure(xscrollcommand=self.scrollbar_x.set)
        
        # 内容框架
        self.content_frame = tk.Frame(self.content_canvas)
        self.content_window = self.content_canvas.create_window(
            (0, 0), window=self.content_frame, anchor="nw")
        
        # 绑定配置事件
        self.content_frame.bind("<Configure>", self._on_content_configure)
        self.content_canvas.bind("<Configure>", self._on_canvas_configure)
        
        # 绑定滚动事件 - 优化事件捕获
        self._bind_scroll_events()
        
        # 强化焦点管理 - 确保画布能接收事件
        self.content_canvas.focus_set()
        self.content_canvas.bind("<Enter>", self._on_enter)
        self.content_canvas.bind("<Leave>", self._on_leave)
        self.content_canvas.bind("<Button-1>", self._on_click)
        
        self.update_idletasks()
        self._debug(f"初始化完成 - 操作系统: {self.os_type}")

    def _on_enter(self, event: tk.Event) -> None:
        """鼠标进入时获取焦点"""
        self.content_canvas.focus_set()
        self._debug("鼠标进入，获取焦点")

    def _on_leave(self, event: tk.Event) -> None:
        """鼠标离开时释放焦点"""
        self._debug("鼠标离开，释放焦点")

    def _on_click(self, event: tk.Event) -> None:
        """点击画布时获取焦点"""
        self.content_canvas.focus_set()
        self._debug("画布被点击，获取焦点")

    def _bind_scroll_events(self) -> None:
        """绑定所有滚动事件，确保跨平台兼容性"""
        # 垂直滚动事件
        if self.os_type == "Linux":
            self.content_canvas.bind("<Button-4>", self._on_vertical_scroll)
            self.content_canvas.bind("<Button-5>", self._on_vertical_scroll)
        else:  # Windows 和 macOS
            self.content_canvas.bind("<MouseWheel>", self._on_vertical_scroll)
        
        # 水平滚动事件
        if self.os_type == "Linux":
            self.content_canvas.bind("<Shift-Button-4>", self._on_horizontal_scroll)
            self.content_canvas.bind("<Shift-Button-5>", self._on_horizontal_scroll)
        else:  # Windows 和 macOS
            self.content_canvas.bind("<Shift-MouseWheel>", self._on_horizontal_scroll)
        
        # macOS 特定水平滚动
        if self.os_type == "Darwin":
            self.content_canvas.bind("<Command-MouseWheel>", self._on_horizontal_scroll)
        
        self._debug("滚动事件绑定完成")

    def get_content_frame(self) -> tk.Frame:
        """获取内容框架，供外部添加内容"""
        return self.content_frame

    def update_layout(self) -> None:
        """强制更新布局"""
        self.update_idletasks()
        # 当内容为空时，手动设置滚动区域为(0,0,0,0)
        if not any(self.content_frame.winfo_children()):
            self.content_canvas.configure(scrollregion=(0, 0, 0, 0))
        else:
            self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
        self._adjust_scrollbars_visibility()

    def _debug(self, message: str) -> None:
        """调试信息输出"""
        if self.debug:
            print(f"[{self.winfo_parent()}] 滚动调试: {message}")

    def _on_content_configure(self, event: tk.Event | None) -> None:
        """内容变化时更新滚动区域"""
        if not any(self.content_frame.winfo_children()):
            self.content_canvas.configure(scrollregion=(0, 0, 0, 0))
        else:
            self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
        self._adjust_scrollbars_visibility()

    def _on_canvas_configure(self, event: tk.Event) -> None:
        """画布大小变化时调整"""
        self.content_canvas.itemconfig(self.content_window, width=event.width)
        self._adjust_scrollbars_visibility()

    def _adjust_scrollbars_visibility(self) -> None:
        """调整滚动条可见性"""
        has_content = any(self.content_frame.winfo_children())
        
        # 垂直滚动条逻辑
        if self.scrollbar_y:
            if not has_content:
                self.scrollbar_y.grid_remove()
                self.content_canvas.yview_moveto(0)
            else:
                content_height = self.content_frame.winfo_reqheight()
                canvas_height = self.content_canvas.winfo_height()
                if content_height > canvas_height:
                    self.scrollbar_y.grid()
                else:
                    self.scrollbar_y.grid_remove()
                    self.content_canvas.yview_moveto(0)
                
        # 水平滚动条逻辑
        if self.scrollbar_x:
            if not has_content:
                self.scrollbar_x.grid_remove()
                self.content_canvas.xview_moveto(0)
            else:
                content_width = self.content_frame.winfo_reqwidth()
                canvas_width = self.content_canvas.winfo_width()
                if content_width > canvas_width:
                    self.scrollbar_x.grid()
                else:
                    self.scrollbar_x.grid_remove()
                    self.content_canvas.xview_moveto(0)

    def _is_shift_pressed(self, event: tk.Event) -> bool:
        """检查Shift键是否被按下"""
        return (event.state & 0x10) != 0

    def _is_mouse_inside(self, event: tk.Event) -> bool:
        """检查鼠标是否在当前画布内"""
        x, y = event.x, event.y
        width = self.content_canvas.winfo_width()
        height = self.content_canvas.winfo_height()
        is_inside = 0 <= x <= width and 0 <= y <= height
        self._debug(f"鼠标位置: ({x},{y})，画布大小: ({width},{height})，是否在内部: {is_inside}")
        return is_inside

    def _on_vertical_scroll(self, event: tk.Event) -> None:
        """垂直滚动处理"""
        # 检查鼠标是否在画布内
        if not self._is_mouse_inside(event):
            self._debug("垂直滚动 - 鼠标不在画布内，忽略")
            return
            
        # 如果按下Shift键，切换到水平滚动
        if self._is_shift_pressed(event):
            self._debug("垂直滚动 - 检测到Shift键，切换到水平滚动")
            self._on_horizontal_scroll(event)
            return
            
        if not self.scroll_y_enabled:
            self._debug("垂直滚动 - 垂直滚动已禁用")
            return
            
        # 检查内容是否需要滚动
        content_height = self.content_frame.winfo_reqheight()
        canvas_height = self.content_canvas.winfo_height()
        if content_height <= canvas_height:
            self._debug(f"垂直滚动 - 内容高度({content_height}) <= 画布高度({canvas_height})，无需滚动")
            return
            
        # 计算滚动单位
        scroll_units = self._calculate_vertical_scroll_units(event)
        self._debug(f"垂直滚动 - 滚动单位: {scroll_units}")
        
        # 执行滚动
        self.content_canvas.yview_scroll(scroll_units, "units")
        
        # 阻止事件传播
        return "break"

    def _on_horizontal_scroll(self, event: tk.Event) -> None:
        """水平滚动处理"""
        # 检查鼠标是否在画布内
        if not self._is_mouse_inside(event):
            self._debug("水平滚动 - 鼠标不在画布内，忽略")
            return
            
        if not self.scroll_x_enabled:
            self._debug("水平滚动 - 水平滚动已禁用")
            return
            
        # 检查内容是否需要滚动
        content_width = self.content_frame.winfo_reqwidth()
        canvas_width = self.content_canvas.winfo_width()
        if content_width <= canvas_width:
            self._debug(f"水平滚动 - 内容宽度({content_width}) <= 画布宽度({canvas_width})，无需滚动")
            return
            
        # 计算滚动单位
        scroll_units = self._calculate_horizontal_scroll_units(event)
        self._debug(f"水平滚动 - 滚动单位: {scroll_units}")
        
        # 执行滚动
        self.content_canvas.xview_scroll(scroll_units, "units")
        
        # 阻止事件传播
        return "break"

    def _calculate_vertical_scroll_units(self, event: tk.Event) -> int:
        """计算垂直滚动单位，确保跨平台一致性"""
        if self.os_type == "Linux":
            if event.num == 4:  # 上滚
                return -1
            elif event.num == 5:  # 下滚
                return 1
        else:  # Windows 和 macOS
            delta = event.delta
            # 标准化滚动单位，确保不同平台滚动速度一致
            if self.os_type == "Darwin":  # macOS
                return int(delta / 12)
            else:  # Windows
                return -int(delta / 120)
        return 0

    def _calculate_horizontal_scroll_units(self, event: tk.Event) -> int:
        """计算水平滚动单位，确保跨平台一致性"""
        if self.os_type == "Linux":
            if event.num == 4:  # 左滚
                return -1
            elif event.num == 5:  # 右滚
                return 1
        else:  # Windows 和 macOS
            delta = event.delta
            if self.os_type == "Darwin":  # macOS
                return int(delta / 12)
            else:  # Windows
                return -int(delta / 120)
        return 0


class ScrollTestArea:
    """滚动测试区域封装，包含一个ScrollableFrame和独立的控制按钮"""
    
    def __init__(self, parent: tk.Frame, title: str, debug: bool = False):
        self.parent = parent
        self.title = title
        self.debug = debug
        self.vertical_items: List[Tuple[ttk.Label, ttk.Button, int]] = []
        self.horizontal_items: List[Tuple[ttk.Label, ttk.Button, int]] = []
        self.vertical_counter = 0
        self.horizontal_counter = 0
        
        # 创建测试区主框架
        self.main_frame = ttk.LabelFrame(parent, text=title)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # 创建滚动容器
        self.scroll_frame = ScrollableFrame(
            self.main_frame, 
            width=400, 
            height=300,
            scroll_x=True,
            scroll_y=True,
            debug=debug,
            relief=tk.RAISED,
            bd=2
        )
        self.scroll_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # 获取内容框架
        self.content_frame = self.scroll_frame.get_content_frame()
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # 创建控制区
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_columnconfigure(1, weight=1)
        
        # 垂直内容控制按钮
        ttk.Button(self.control_frame, text="添加垂直内容", 
                  command=self.add_vertical_item).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(self.control_frame, text="删除垂直内容", 
                  command=self.delete_vertical_item).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        
        # 水平内容控制按钮
        ttk.Button(self.control_frame, text="添加水平内容", 
                  command=self.add_horizontal_item).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(self.control_frame, text="删除水平内容", 
                  command=self.delete_horizontal_item).grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        
        # 清空所有内容按钮
        ttk.Button(self.control_frame, text="清空所有内容", 
                  command=self.clear_all_items).grid(row=2, column=0, columnspan=2, padx=2, pady=2, sticky="ew")
        
        # 初始添加一些内容（确保有足够内容触发滚动）
        for _ in range(5):
            self.add_vertical_item()
        for _ in range(2):
            self.add_horizontal_item()
    
    def add_vertical_item(self) -> None:
        """添加垂直滚动测试内容"""
        self.vertical_counter += 1
        row = len(self.vertical_items) + len(self.horizontal_items)
        
        delete_btn = ttk.Button(
            self.content_frame, 
            text="删", 
            command=lambda id=self.vertical_counter: self.remove_vertical_item(id)
        )
        
        item = ttk.Label(
            self.content_frame, 
            text=f"垂直内容项 {self.vertical_counter} - 这是用于测试垂直滚动的内容，会增加高度...",
            wraplength=350
        )
        
        item.grid(row=row, column=0, padx=10, pady=10, sticky="w")
        delete_btn.grid(row=row, column=1, padx=5, pady=10)
        
        self.vertical_items.append((item, delete_btn, self.vertical_counter))
        self.scroll_frame.update_layout()
    
    def remove_vertical_item(self, item_id: int) -> None:
        for i, (label, btn, idx) in enumerate(self.vertical_items):
            if idx == item_id:
                label.destroy()
                btn.destroy()
                self.vertical_items.pop(i)
                self._rearrange_items()
                self.scroll_frame.update_layout()
                break
    
    def delete_vertical_item(self) -> None:
        if self.vertical_items:
            _, _, item_id = self.vertical_items[-1]
            self.remove_vertical_item(item_id)
    
    def add_horizontal_item(self) -> None:
        """添加水平滚动测试内容（超宽内容）"""
        self.horizontal_counter += 1
        row = len(self.vertical_items) + len(self.horizontal_items)
        
        delete_btn = ttk.Button(
            self.content_frame, 
            text="删", 
            command=lambda id=self.horizontal_counter: self.remove_horizontal_item(id)
        )
        
        long_text = f"水平内容项 {self.horizontal_counter} - " + "这是超宽的水平滚动测试内容，会增加宽度 " * 10
        item = ttk.Label(
            self.content_frame, 
            text=long_text,
            wraplength=0
        )
        
        item.grid(row=row, column=0, padx=10, pady=10, sticky="w")
        delete_btn.grid(row=row, column=1, padx=5, pady=10)
        
        self.horizontal_items.append((item, delete_btn, self.horizontal_counter))
        self.scroll_frame.update_layout()
    
    def remove_horizontal_item(self, item_id: int) -> None:
        for i, (label, btn, idx) in enumerate(self.horizontal_items):
            if idx == item_id:
                label.destroy()
                btn.destroy()
                self.horizontal_items.pop(i)
                self._rearrange_items()
                self.scroll_frame.update_layout()
                break
    
    def delete_horizontal_item(self) -> None:
        if self.horizontal_items:
            _, _, item_id = self.horizontal_items[-1]
            self.remove_horizontal_item(item_id)
    
    def clear_all_items(self) -> None:
        for label, btn, _ in self.vertical_items:
            label.destroy()
            btn.destroy()
        self.vertical_items.clear()
        
        for label, btn, _ in self.horizontal_items:
            label.destroy()
            btn.destroy()
        self.horizontal_items.clear()
        
        self.scroll_frame.update_layout()
        if self.debug:
            print(f"[{self.title}] 已清空所有内容项")
    
    def _rearrange_items(self) -> None:
        all_items = self.vertical_items + self.horizontal_items
        all_items.sort(key=lambda x: x[2])
        
        for row, (label, btn, _) in enumerate(all_items):
            label.grid(row=row, column=0, padx=10, pady=10, sticky="w")
            btn.grid(row=row, column=1, padx=5, pady=10)


# 主程序
if __name__ == "__main__":
    root = tk.Tk()
    root.title("滚动容器测试 - 修复滚动不响应问题")
    root.geometry("1000x600")
    
    # 显示当前操作系统
    os_name = platform.system()
    os_display_name = "Windows" if os_name == "Windows" else \
                      "macOS" if os_name == "Darwin" else \
                      "Linux" if os_name == "Linux" else os_name
    
    # 主容器
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)
    main_frame.grid_rowconfigure(1, weight=1)
    
    # 顶部说明区
    info_frame = ttk.LabelFrame(main_frame, text="使用说明")
    info_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
    
    ttk.Label(info_frame, text=f"滚动功能测试 ({os_display_name})", 
             font=("Arial", 12, "bold")).pack(anchor="w", padx=5, pady=5)
    ttk.Label(info_frame, text="• 确保鼠标在测试区内再滚动", 
             font=("Arial", 10)).pack(anchor="w", padx=10)
    ttk.Label(info_frame, text="• 鼠标滚轮：垂直滚动当前区域", 
             font=("Arial", 10)).pack(anchor="w", padx=10)
    ttk.Label(info_frame, text="• Shift+鼠标滚轮：水平滚动当前区域", 
             font=("Arial", 10)).pack(anchor="w", padx=10)
    
    # 创建测试区
    left_test_area = ScrollTestArea(main_frame, "左侧测试区", debug=True)
    left_test_area.main_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
    
    right_test_area = ScrollTestArea(main_frame, "右侧测试区", debug=True)
    right_test_area.main_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
    
    root.mainloop()
