from math import floor

class SensorGrid:
    def __init__(self, sensor_config):
        self.sens_cfg = sensor_config
        self.grids = []
    
    def tile(self, sensors, arr):
        num_rows = floor( len(sensors)**0.5 )
        num_cols = len(sensors) // num_rows

        for i in range(num_rows - 1):
            arr.append([])
            for j in range(num_cols):
                arr[-1].append(
                    sensors[i*num_cols+j]
                )
        
        rem = len(sensors) - ( num_rows - 1 ) * num_cols
        if rem > 0:
            arr.append([])
            for i in range(len(sensors)-rem, len(sensors)):
                arr[-1].append(
                    sensors[i]
                )

    def create_grid(self):
        for i in range(self.sens_cfg.get_tab_count()):
            self.grids.append([])
            self.tile([
                sensor for sensor in self.sens_cfg.get_sensors()
                if sensor.get_tab() == i
            ], self.grids[-1])

    def get_grid(self, i):
        return self.grids[i]