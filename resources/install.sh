# add our start script to the autostart of the LXDE desktop
# we don't want to start any earlier since we're a GUI component.
echo "@bash /opt/signage/start.sh" >> /home/pi/.config/lxsession/LXDE-pi/autostart

