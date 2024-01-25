import logging
from logging import Handler, LogRecord, Formatter

from zerolib.standard import formatter_config

logger = logging.getLogger(__name__)

class LogHandler(Handler):
    def handle(self, record: LogRecord):
        msg = self.format(record)
        if hasattr(self, "callback_fn"):
            self.callback_fn(msg)

    def set_callback(self, fn):
        self.callback_fn = fn

RED = (255,0,0)
GREEN = (0,255,0)

class Indicator:
    def __init__(self, dpg, label):
        self.dpg = dpg
        self.enabled = False

        with dpg.group(horizontal=True, height=20):
            dpg.add_text(label)
            with dpg.drawlist(width=10, height=20):
                self.indicator = dpg.draw_circle((5, 10), 5, fill=RED)

    def set(self, status):
        self.dpg.configure_item(self.indicator, fill=GREEN if status else RED)


class Button:
    def __init__(self, dpg, label):
        self.callback = None
        self.label = label

        dpg.add_checkbox(label=label, callback=self.callback_fn)
    
    def callback_fn(self, _, value):
        if self.callback:
            self.callback(value)
        else:
            logger.warning(f"{self.label} button pressed but no callback configured!")
    
    def register_callback(self, fn):
        self.callback = fn


class ProgramDropdown:
    def __init__(self, dpg):
        self.dpg = dpg
        self.callback = None

        self.combo = dpg.add_combo(callback=self.callback_fn)

    def callback_fn(self, _, value):
        if self.callback:
            self.callback(value)
        else:
            logger.warning(f"Attempted to select program but no callback configured!")

    def register_callback(self, fn):
        self.callback = fn
    
    def set_programs(self, program_list):
        self.dpg.configure_item(self.combo, items=program_list)
        logger.info("Updated program list.")


class Menu:
    def __init__(self, dpg, master, small_font = None,
        indicators = [], buttons = []
    ):
        self.dpg = dpg
        self.master = master

        # button callbacks
        self.indicators = {}
        self.buttons = {}
        self.program_dropdown = None
        self.tank_heating_callback = None
        
        self.pause_scroll = False

        with dpg.group(label="Control Panel", parent=master, height=200) as window:
            self.window = window

            with dpg.group(horizontal=True):
                # Add logbox
                with dpg.child(width=1200):
                    with dpg.group(horizontal=True):
                        dpg.add_text("Logs")
                        dpg.add_checkbox(label="Freeze", default_value=False, callback=self.freeze)

                    with dpg.table(header_row=False, scrollY=True) as table:
                        self.logger_box = table
                        dpg.add_table_column()

                if small_font:
                    dpg.bind_item_font(self.logger_box, small_font)
                
                # Add control panel
                with dpg.child():
                    self.program_dropdown = ProgramDropdown(dpg)

                    for indicator in indicators:
                        self.indicators[indicator] = Indicator(dpg, indicator)

                    for button in buttons:
                        self.buttons[button] = Button(dpg, button)

    def freeze(self, _, val):
        self.pause_scroll = val

    def get_indicator_callback(self, indicator):
        return self.indicators[indicator].set
    
    def set_button_callback(self, button, fn):
        self.buttons[button].register_callback(fn)
    
    def set_program_dropdown_callback(self, fn):
        self.program_dropdown.register_callback(fn)

    def add_log(self, item):
        color = None

        ltext = item.lower()
        if "warning" in ltext:
            color = (255, 168, 82)
        elif "error" in ltext:
            color = (255, 80, 80)
        elif "critical" in ltext:
            color = (255, 82, 212)
        elif "controller" in ltext:
            color = (180, 180, 180)

        with self.dpg.table_row(parent=self.logger_box):
            self.dpg.add_text(item, color=color)
    
    def set_programs(self, program_list):
        self.program_dropdown.set_programs(program_list)

    def get_log_handler(self):
        handler = LogHandler()
        handler.set_callback(self.add_log)
        formatter = Formatter(**formatter_config)
        handler.setFormatter(formatter)
        return handler

    def tick(self):
        if not self.pause_scroll:
            self.dpg.set_y_scroll(self.logger_box, self.dpg.get_y_scroll_max(self.logger_box))