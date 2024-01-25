# Zero Test Bench Software Stack
Author: Cristian Bicheru

For questions, feel free to reach out to `c.bicheru0@gmail.com`.

## Introduction
The hardware stack consists of a laptop and a Raspberry Pi 4B. Each device has
its own software located in the appropriate directories. ZeroMQ is used to link
the monitor software on the laptop to the controller software on the Pi. Onboard
sensors and their settings are defined in `sensors.cfg`.

`zerolib` is a library containing code used by both the monitor and the
controller.

The `Engine Test Programs` directory contains valve throttle profiles to be
executed during a cold flow or static fire test. The format is a 4 column
csv file. The first column is the time (in seconds) since the test begins, the
second column holds the desired fuel valve throttle position and the third column
holds the desired oxidizer valve throttle position at this timestep. The last
column controls the torch ignitor state. A 1 turns the ignitor on at this
timestep and a 0 turns it off. Between timesteps, the throttles are linearly
interpolated based on the current time.

## Testing Procedure
Once the all of the hardware is setup, an ethernet link should be established
between the laptop and the Raspberry Pi. Then, the battery pack is connected to
the electrical box.

At this point, an SSH link is established to the Pi. The `pigpiod` service is
started using `./start_pigpiod.sh`. Then, the controller is started with
`./start_controller.sh`. Once the controller software is finished initializing,
the monitor should begin to show live data collected from the controller. Any
warnings/errors from the Pi are shown either in the SSH console or the monitor
software.

## Pi Setup
To improve the reliability and performance of the Pi, it is running a custom
compiled kernel with `PREEMPT_RT` enabled. The Pi is also overlocked to 2 GHz.

## Video Feed
To establish a live camera feed, connect an android phone to the Pi via USB and
run the `./start_camera.sh` command. This will forward the 8080 port on the
phone to 8081 on the Pi. A camera server (e.g. IP Webcam) can then be run on the
phone (broadcasting on port 8080) and accessed on the laptop.
