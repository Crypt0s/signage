cp /home/pi/.Xauthority /root/.Xauthority
export DISPLAY=:0.0
cd /opt/signage/
nice -20 rpi-fb-matrix --led-brightness=75 --led-daemon --led-slowdown-gpio 4  --led-scan-mode 1 --led-pwm-lsb-nanoseconds 50 resources/matrix.cfg
python sign.py
