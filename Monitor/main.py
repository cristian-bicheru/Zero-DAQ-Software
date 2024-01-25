### ADD IMPORT DIRECTORY
import sys
sys.path.append('../')

import os
import signal
import dearpygui.dearpygui as dpg
from pint import UnitRegistry

from sensorgrid import SensorGrid
from plotarray import PlotArray
from menu import Menu
from action_dispatcher import ActionDispatcher, ACTION_BUTTONS
from message_handler import MessageHandler

from zerolib.communications import MessageServer, DEFAULT_CONTROLLER_PORT, DEFAULT_MONITOR_PORT
from zerolib.sensorcfg import SensorConfiguration
from zerolib.standard import logging_config, sensor_cfg_location
from zerolib.message import EngineProgramSettingsMessage

### LOGGING SETUP
import logging
logging.basicConfig(**logging_config)

### SETUP
units = UnitRegistry()

dpg.create_context()
with dpg.font_registry():
    font = dpg.add_font("UbuntuMono-Regular.ttf", 12.5)
    small_font = dpg.add_font("UbuntuMono-Regular.ttf", 11.5)
dpg.bind_font(font)
dpg.create_viewport(
    title='Zero Monitor', small_icon="icon.ico", large_icon="icon.ico"
)

### GUI CREATION
sens_cfg = SensorConfiguration(sensor_cfg_location)
sens_cfg.read_config()

sn_grid = SensorGrid(sens_cfg)
sn_grid.create_grid()

tab_labels = [
    "Primary Sensors",
    "Secondary Sensors",
    "Tertiary Sensors"
]
plt_arrs = []

with dpg.window() as w:
    bg_window = w

    with dpg.group(parent=bg_window):
        with dpg.tab_bar() as tb:
            for i in range(sens_cfg.get_tab_count()):
                with dpg.tab(label=tab_labels[i]) as tab:
                    plt_arrs.append(
                        PlotArray(
                            dpg, tab, units, sn_grid.get_grid(i)
                        )
                    )

    menu = Menu(dpg, bg_window, small_font=small_font,
        indicators = [
            "Connection"
        ],
        buttons = ACTION_BUTTONS
    )

logging.getLogger().addHandler(menu.get_log_handler())

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window(bg_window, True)

### SETUP SERVER
server = MessageServer(host="0.0.0.0", port=DEFAULT_MONITOR_PORT)

# Register the button callbacks
dispatcher = ActionDispatcher(server, port=DEFAULT_CONTROLLER_PORT)
for button in ACTION_BUTTONS:
    menu.set_button_callback(button, dispatcher.get_callback(button))

msg_handler = MessageHandler(units, sens_cfg, menu, plt_arrs)
server.register_request_hook(msg_handler.handle)

menu_indicator_cb = menu.get_indicator_callback("Connection")
def connection_hook(status):
    # Called when the connection status is changed. Update the GUI and register
    # the new ip with the dispatcher if available.
    menu_indicator_cb(status)
    msg_handler.update_offset()

def program_callback(selected_program):
    # Called when a program is selected by the user.
    msg = EngineProgramSettingsMessage(True, selected_program)
    server.dispatch(msg)
menu.set_program_dropdown_callback(program_callback)

server.register_connection_hook(connection_hook)
server.run()

dpg.set_viewport_title(f"Zero Monitor")
dpg.maximize_viewport()

# Join the server threads on exit
dpg.set_exit_callback(server.stop)

### RENDER LOOP
while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()

    [arr.update_plot_ranges() for arr in plt_arrs]

    menu.tick()

### TEARDOWN
os.kill(os.getpid(), signal.SIGTERM)