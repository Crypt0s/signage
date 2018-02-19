# This is just for the installation on XFCE Raspi -- this startup script doesn't work elsewhere

# add our start script to the autostart of the LXDE desktop
# we don't want to start any earlier since we're a GUI component.
echo "@bash /opt/signage/start.sh" >> /home/pi/.config/lxsession/LXDE-pi/autostart

sudo apt-get install -y build-essential libconfig++-dev git

cd /opt/
git clone --recursive https://github.com/adafruit/rpi-fb-matrix.git
cd rpi-fb-matrix
make

#make install
