# !/usr/bin/python3
# -*- coding: UTF-8 -*-
import tkinter as tk
from typing import Callable, cast, override
try:
    from logit import pv, pe, po
    from winbasic import Dialog
    from tkcontrol import tkControl
except ImportError:
    from pyutilities.logit import pv, pe, po
    from pyutilities.winbasic import Dialog
    from pyutilities.tkcontrol import tkControl


class SlideSwitch(tkControl):
    """iOS-style toggle switch widget implemented with Tkinter Canvas.

    This widget replicates the behavior and appearance of the native iOS toggle switch,
    supporting both click-to-toggle and drag-to-toggle interactions. The switch state
    is visually synchronized with its logical state, and smooth animation is provided
    for state transitions.

    Key Features:
        - Click anywhere on the switch to toggle state instantly
        - Drag the slider to adjust position and release to confirm state
        - Smooth animation for state transitions
        - Customizable colors for on/off states, slider, and slider shadow
        - Callback function triggered on state change

    """

    def __init__(
        self,
        parent: tk.Misc,
        owner: Dialog,
        idself: str,
        width: int = 80,
        height: int = 40,
        default_state: bool = False,
        on_color: str = "#007AFF",
        off_color: str = "#E5E5E5",
        slider_color: str = "white",
        slider_shadow: str = "#CCCCCC",
        callback: Callable[[bool], None] | None = None
    ) -> None:
        """Initialize the SlideSwitch widget.

        Args:
            parent: Parent Tkinter widget (e.g., Tk, Frame, Canvas) that contains this switch
            owner: message to deliver
            idself: id of control self
            width: Width of the switch in pixels (default: 80)
            height: Height of the switch in pixels (default: 40)
            default_state: Initial state of the switch (False = off, True = on; default: False)
            on_color: Background color when switch is in on state (default: iOS blue "#007AFF")
            off_color: Background color when switch is in off state (default: iOS gray "#E5E5E5")
            slider_color: Color of the slider button (default: white)
            slider_shadow: Color of the slider's drop shadow (default: light gray "#CCCCCC")
            callback: Optional function to call when switch state changes. The function
                should accept a single boolean parameter representing the new state.

        Returns:
            None
        """
        ctrl = tk.Canvas(parent, width=width, height=height, highlightthickness=0)
        super().__init__(parent, "", idself, ctrl)
        self._master: Dialog = owner

        self._width: int = width
        self._height: int = height
        self._state: bool = default_state
        self._on_color: str = on_color
        self._off_color: str = off_color
        self._slider_color: str = slider_color
        self._slider_shadow: str = slider_shadow
        self._callback: Callable[[bool], None] | None = callback

        self._radius: int = height // 2  # Radius for rounded switch corners
        self._slider_padding: int = 2    # Padding between slider and switch border
        self._drag_threshold: int = 3    # Pixel threshold to distinguish click vs drag
        self._is_dragging: bool = False  # Flag to track drag state
        self._start_x: int = 0           # Starting X coordinate of mouse press
        self._current_slider_x: float = 0.0  # Current X position of slider (supports animation)
        self._original_slider_x: float = 0.0 # Original slider position before drag

        # Private instance variables (core implementation details, not accessible externally)
        self.__slider_size: int = self._height - 2 * self._slider_padding  # Diameter of slider
        self.__slider_off_x: int = self._slider_padding  # X position of slider in off state
        self.__slider_on_x: int = self._width - self.__slider_size - self._slider_padding  # X position in on state

        # Initialize slider position based on default state
        self._current_slider_x = float(self.__slider_off_x) if not default_state else float(self.__slider_on_x)

        # Initial render and event binding
        self._redraw_all()
        self._bind_events()

    def _redraw_all(self) -> None:
        """Redraw the entire switch widget (background + slider).

        Clears the canvas and redraws all elements to ensure visual consistency
        with the current state. Called on every state change or drag movement.

        Returns:
            None
        """
        canvas = cast(tk.Canvas, self._tkctrl)
        canvas.delete("all")

        # Draw switch background (rounded rectangle)
        bg_color: str = self._on_color if self._state else self._off_color
        self._draw_rounded_rect(0, 0, self._width, self._height, self._radius, bg_color)

        # Draw slider shadow (slightly offset for depth effect)
        shadow_x: float = self._current_slider_x - 1
        shadow_y: int = self._slider_padding - 1
        _ = canvas.create_oval(
            shadow_x, shadow_y,
            shadow_x + self.__slider_size + 2,
            shadow_y + self.__slider_size + 2,
            fill=self._slider_shadow,
            outline=""
        )

        # Draw main slider button
        _ = canvas.create_oval(
            self._current_slider_x, self._slider_padding,
            self._current_slider_x + self.__slider_size,
            self._slider_padding + self.__slider_size,
            fill=self._slider_color,
            outline=""
        )

    def _draw_rounded_rect(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        radius: int,
        fill: str
    ) -> None:
        """Draw a rounded rectangle on the canvas.

        Creates a rectangle with fully rounded corners (pill shape) by combining
        arc segments and rectangles. This matches the native iOS switch appearance.

        Args:
            x1: Top-left X coordinate of the rectangle
            y1: Top-left Y coordinate of the rectangle
            x2: Bottom-right X coordinate of the rectangle
            y2: Bottom-right Y coordinate of the rectangle
            radius: Radius of the rounded corners (should be half the height for pill shape)
            fill: Background color of the rounded rectangle

        Returns:
            None
        """
        canvas = cast(tk.Canvas, self._tkctrl)

        # Draw four rounded corners (arcs)
        _ = canvas.create_arc(
            x1, y1, x1 + 2 * radius, y1 + 2 * radius,
            start=90, extent=90, fill=fill, outline=fill, width=0
        )
        _ = canvas.create_arc(
            x2 - 2 * radius, y1, x2, y1 + 2 * radius,
            start=0, extent=90, fill=fill, outline=fill, width=0
        )
        _ = canvas.create_arc(
            x1, y2 - 2 * radius, x1 + 2 * radius, y2,
            start=180, extent=90, fill=fill, outline=fill, width=0
        )
        _ = canvas.create_arc(
            x2 - 2 * radius, y2 - 2 * radius, x2, y2,
            start=270, extent=90, fill=fill, outline=fill, width=0
        )

        # Fill the middle areas between arcs
        _ = canvas.create_rectangle(
            x1 + radius, y1, x2 - radius, y2,
            fill=fill, outline=fill, width=0
        )
        _ = canvas.create_rectangle(
            x1, y1 + radius, x2, y2 - radius,
            fill=fill, outline=fill, width=0
        )

    def _bind_events(self) -> None:
        """Bind mouse events to handle user interactions.

        Binds press, drag, and release events to their respective handlers
        to manage click and drag interactions with the switch.

        Returns:
            None
        """
        _ = self._tkctrl.bind("<ButtonPress-1>", self._on_press)
        _ = self._tkctrl.bind("<B1-Motion>", self._on_drag)
        _ = self._tkctrl.bind("<ButtonRelease-1>", self._on_release)

    def _on_press(self, event: tk.Event) -> None:
        """Handle mouse press event on the switch.

        Initializes drag state tracking and records the starting position
        of the mouse press and slider.

        Args:
            event: Tkinter mouse event object containing press coordinates

        Returns:
            None
        """
        self._is_dragging = False
        self._start_x = event.x
        self._original_slider_x = self._current_slider_x

    def _on_drag(self, event: tk.Event) -> None:
        """Handle mouse drag event on the switch.

        Updates the slider position in real-time during drag operations,
        limits movement to valid bounds, and updates the visual state
        to reflect the current slider position.

        Args:
            event: Tkinter mouse event object containing drag coordinates

        Returns:
            None
        """
        delta_x: int = event.x - self._start_x

        # Determine if movement exceeds drag threshold (distinguish click vs drag)
        if abs(delta_x) > self._drag_threshold:
            self._is_dragging = True

        if self._is_dragging:
            # Calculate new slider position with boundary limits
            new_x: float = self._original_slider_x + delta_x
            self._current_slider_x = max(
                float(self.__slider_off_x),
                min(new_x, float(self.__slider_on_x))
            )

            # Update logical state based on slider position (50% threshold)
            ratio: float = (self._current_slider_x - self.__slider_off_x) / (self.__slider_on_x - self.__slider_off_x)
            self._state = ratio > 0.5

            # Redraw to reflect new position/state
            self._redraw_all()

    def _on_release(self, event: tk.Event) -> None:
        """Handle mouse release event on the switch.

        Determines the final state based on whether the interaction was a click
        or drag, then animates the slider to the final position and triggers
        the callback if the state changed.

        Args:
            event: Tkinter mouse event object containing release coordinates

        Returns:
            None
        """
        new_state: bool = False
        if self._is_dragging:
            # For drag interactions: determine state from final slider position
            ratio: float = (self._current_slider_x - self.__slider_off_x) / (self.__slider_on_x - self.__slider_off_x)
            new_state = ratio > 0.5
        else:
            # For click interactions: toggle state directly
            new_state = not self._state

        # Animate to final state and trigger callback if needed
        self._animate_to_state(new_state)

    def _animate_to_state(self, target_state: bool) -> None:
        """Animate the slider to the target state position.

        Provides smooth linear animation from current position to the target
        position (on/off). Triggers the callback function if the state changes.

        Args:
            target_state: Desired final state (False = off, True = on)

        Returns:
            None
        """
        # Calculate target position based on desired state
        target_x: float = float(self.__slider_on_x) if target_state else float(self.__slider_off_x)
        distance: float = target_x - self._current_slider_x

        # If already at target position (within 1px tolerance), finalize state
        if abs(distance) < 1:
            self._current_slider_x = target_x
            self._redraw_all()

            self._on_state_changed(target_state)
            return

        # Calculate animation step (smooth movement over 10 frames)
        step = distance / 10 if abs(distance) > 10 else (1.0 if distance > 0 else -1.0)

        # Recursive animation function (executes every 8ms for ~60fps)
        def animate_step() -> None:
            nonlocal step, target_x
            self._current_slider_x += step

            # Check if animation has reached target position
            if ((step > 0 and self._current_slider_x >= target_x) or
                (step < 0 and self._current_slider_x <= target_x)):
                self._current_slider_x = target_x

                self._on_state_changed(target_state)
                self._redraw_all()
                return

            # Continue animation loop
            self._redraw_all()
            _ = self._tkctrl.after(8, animate_step)

        # Start animation sequence
        animate_step()

    def get_state(self) -> bool:
        """Get the current logical state of the switch.

        This is the public API method to retrieve the switch state, preferred
        over direct access to the state attribute for API consistency.

        Returns:
            bool: Current state (True = on, False = off)
        """
        return self._state

    def set_state(self, state: bool, animate: bool = True) -> None:
        """Set the switch to a specific state programmatically.

        set the switch state with optional animation.
        Triggers the callback function if the state changes.

        Args:
            state: Desired state (True = on, False = off)
            animate: Whether to animate the transition (default: True)

        Returns:
            None
        """
        # Exit if no state change needed
        if state == self._state:
            return

        # Animate to new state or set directly
        if animate:
            self._animate_to_state(state)
        else:
            # Set position directly without animation
            self._current_slider_x = float(self.__slider_on_x) if state else float(self.__slider_off_x)
            self._redraw_all()

            self._on_state_changed(state)

    def _on_state_changed(self, state: bool):
        self._state = state
        # Trigger callback if state changed
        if self._callback:
            self._callback(state)
        _ = self._master.process_message(self._idself, event="Changed", val=state)


if __name__ == "__main__":
    class tkBasic(Dialog):
        """Demonstration application for the SlideSwitch widget.

        Creates a simple Tkinter window with the SlideSwitch widget,
        status display, and test button to verify functionality.

        """
        def __init__(self, title: str, w: int, h: int):
            super().__init__(title, w, h)
            self._root: tk.Tk = tk.Tk()
            self._root.title(title)
            self._root.geometry(f"{w}x{h}")
            _ = self._root.configure(bg="#F5F5F7")  # iOS system background color

            # create ui

            # Title label
            title_label: tk.Label = tk.Label(
                self._root,
                text=title,
                bg="#F5F5F7",
                font=("SF Pro Text", 18, "bold")
            )
            title_label.pack(pady=30)

            # Create SlideSwitch widget
            self._switch: SlideSwitch = SlideSwitch(
                self._root,
                self,
                "",
                width=80,
                height=40,
                default_state=False,
                slider_color="white",
                slider_shadow="#CCCCCC",
                callback=self.on_switch_change
            )
            self._switch.control.pack(pady=20)

            # Status color block (visual state indicator)
            self._status_block: tk.Label = tk.Label(
                self._root,
                text="",
                bg="#E5E5E5",
                width=10,
                height=2,
                bd=0,
                relief="flat"
            )
            self._status_block.pack(pady=10)

            # Status text label
            self._status_label: tk.Label = tk.Label(
                self._root,
                text="Current State: ❌ Off",
                bg="#F5F5F7",
                font=("SF Pro Text", 14)
            )
            self._status_label.pack(pady=10)

        def on_switch_change(self, state: bool) -> None:
            """Callback function to update status display on state change.

            Args:
                state: New state of the switch (True = on, False = off)

            Returns:
                None
            """
            _ = self._status_label.config(text=f"Current State: {'✅ On' if state else '❌ Off'}")
            _ = self._status_block.config(bg="#007AFF" if state else "#E5E5E5")

        def go(self):
            # Start main event loop
            self._root.mainloop()

        @override
        def destroy(self, **kwargs: object):
            super().destroy(**kwargs)

    gui = tkBasic("iOS Style Toggle Switch", 400, 350)
    gui.go()
