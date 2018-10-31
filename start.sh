#!/bin/bash
cp /home/pi/.Xauthority /root/.Xauthority
export DISPLAY=:0.0
cd /opt/signage/
nice -20 /opt/rpi-fb-matrix/rpi-fb-matrix --led-brightness=75 --led-daemon --led-slowdown-gpio 4  --led-scan-mode 1 resources/matrix.cfg
python sign.py
