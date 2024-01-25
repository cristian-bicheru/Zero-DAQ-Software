from plot import Plot


class PlotArray:
    def __init__(self, dpg, master, units, sensors):
        self.dpg = dpg
        self.master = master
        self.units = units
        self.id_mapping = {}

        self.plots = []
        with dpg.table(header_row=False):
            [dpg.add_table_column() for _ in range(len(sensors[0]))]

            for i in range(len(sensors)):
                self.plots.append([])
                num_plots = len(sensors[i])
                
                with dpg.table_row():
                    for j in range(num_plots):
                        sensor = sensors[i][j]
                        self.id_mapping[sensor.get_id()] = (i, j)
                        self.plots[-1].append(Plot(dpg, units, sensor))

    
    def add_datapoint(self, sensor_id, datapoint):
        i, j = self.id_mapping[sensor_id]
        self.plots[i][j].add_datapoint(datapoint)
    
    def update_plot_ranges(self):
        [[plot.update_range() for plot in row] for row in self.plots]