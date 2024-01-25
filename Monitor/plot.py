import numpy as np
import bisect

class Plot:
    def __init__(self, dpg, units, sensor):
        self.dpg = dpg
        self.u = units

        self.retain = 10

        self.desc = sensor.get_name()
        self.id = sensor.get_id()

        self.data_range = np.array(sensor.get_range())
        self.xdata = []
        self.ydata = []

        self.fixed_range = True
        self.paused = False

        self.x_axis = None
        self.y_axis = None

        self.available_units = sensor.get_units()
        self.y_units = self.u(self.available_units[0])
        self.update_units(None, self.available_units[0])

        # create GUI
        with dpg.group(label=self.desc) as window:
            self.window = window

            with dpg.plot(anti_aliased=True, width=-1, height=270) as plot:
                self.plot = plot
                self.x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                self.y_axis = dpg.add_plot_axis(dpg.mvYAxis, label=self.y_label)
                self.series = dpg.add_line_series(self.xdata, self.ydata, parent=self.y_axis)
            
            with dpg.group(horizontal=True):
                if len(self.available_units) > 1:
                    dpg.add_text("Units")
                    dpg.add_combo(
                        items = self.available_units, callback = self.update_units,
                        default_value = self.available_units[0], width=50
                    )
                    dpg.add_text(" Window")
                else:
                    dpg.add_text("Window")
                
                dpg.add_combo(
                    items = [5, 10, 20, 60, 120, 240],
                    callback = self.update_x_window, default_value=10, width=45
                )

                dpg.add_text(" Auto Range")
                dpg.add_checkbox(default_value = False, callback = self.toggle_fixed)

                dpg.add_text(" Pause")
                dpg.add_checkbox(default_value = False, callback = self.pause)
        
        self.update_range()
    
    def update_x_window(self, _, xwin):
        self.retain = int(xwin)
    
    def get_xlim_idx(self, xlim):
        xmin, xmax = xlim

        return bisect.bisect_right(self.xdata, xmin), bisect.bisect_left(self.xdata, xmax)
    
    def update_units(self, _, new_units):
        new_units = self.u(new_units)
    
        self.data_range = self.u.Quantity(self.data_range, self.y_units ).to(new_units).m
        self.ydata = list(self.u.Quantity(np.array(self.ydata), self.y_units).to(new_units).m)

        self.y_units = new_units
        u_label = f"{new_units.units:~P}"
        if u_label != "":
            self.y_label = f"{self.desc} [{u_label}]"
        else:
            self.y_label = f"{self.desc}"

        if self.y_axis:
            self.dpg.set_item_label(self.y_axis, self.y_label)
    
    def update_range(self):
        if not self.y_axis or not self.x_axis or not self.xdata or not self.ydata:
            return

        li, ri = self.get_xlim_idx(self.dpg.get_axis_limits(self.x_axis))

        if self.fixed_range:
            padding = abs(self.data_range[1]) * 0.025
            self.dpg.set_axis_limits(
                self.y_axis,
                self.data_range[0] - padding,
                self.data_range[1] + padding
            )
        else:
            ymin = min(self.ydata[li:ri])
            ymax = max(self.ydata[li:ri])

            padding = 0.01 * max(abs(ymin), abs(ymax))
            if padding == 0:
                padding = abs(self.data_range[1]) * 0.025

            self.dpg.set_axis_limits(self.y_axis, ymin-padding, ymax+padding)

        self.update_series(li, ri)

        if self.paused:
            self.dpg.set_axis_limits_auto(self.x_axis)
        else:
            if len(self.xdata) > 1:
                latest_x = self.xdata[-1]
                self.dpg.set_axis_limits(
                    self.x_axis,
                    max(latest_x-self.retain, self.xdata[0]),
                    latest_x
                )
        
    def toggle_fixed(self, _, val):
        self.fixed_range = not val
        if val:
            self.dpg.set_axis_limits_auto(self.y_axis)

    def pause(self, _, val):
        self.paused = val

        if not self.paused:
            self.update_range()

    def add_datapoint(self, dp):
        x, y = dp
        self.xdata.append(x)
        self.ydata.append(y.to(self.y_units).m)

    def update_series(self, li, ri):
        self.dpg.set_value(self.series, [self.xdata[li:ri], self.ydata[li:ri]])