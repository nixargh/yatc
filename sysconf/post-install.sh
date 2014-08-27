#!/bin/bash
# script to deploy YATC on Ubuntu 12.04 - 14.04 (netinstall with only ssh server installed)
# (*w) author: nixargh <nixargh@gmail.com>
VERSION="0.8.1"
##### Settings ################################################################
# !!! must be executed from root !!!
RDPUSER="user"
TIMEZONE="Europe/Moscow"
FREERDP_BRANCH="stable-1.1"
YATC_BRANCH="saparation"
###############################################################################
set -u -e

# check that you are root
if [ $USER != "root" ]; then
  echo "You must be root."
  exit 1
fi

# set timezone
cp -f /usr/share/zoneinfo/$TIMEZONE /etc/localtime

# detect admuser
ADM_USER=`grep 1000 /etc/passwd |awk 'BEGIN{FS=":"} {print $1}'`

# install required packages
apt-get update
apt-get install -y python3 python3-tk python3-crypto git xorg vim cups puppet autofs libasound2 \
  libasound2-plugins alsa-utils alsa-oss pulseaudio pulseaudio-utils

# install FreeRDP from git
apt-get install -y build-essential git-core cmake libssl-dev libx11-dev libxext-dev libxinerama-dev \
  libxcursor-dev libxdamage-dev libxv-dev libxkbfile-dev libasound2-dev libcups2-dev libxml2 libxml2-dev \
  libxrandr-dev libgstreamer0.10-dev libgstreamer-plugins-base0.10-dev libxi-dev libavcodec-dev libpulse-dev

cd /tmp
git clone git://github.com/FreeRDP/FreeRDP.git
cd ./FreeRDP
git checkout $FREERDP_BRANCH

DATE1=`date +%s%N`

cmake -DCMAKE_BUILD_TYPE=Debug -DWITH_SSE2=ON -DWITH_CUPS=ON -DCHANNEL_PRINTER=ON -DWITH_PULSE=ON .

DATE2=`date +%s%N`

make
make install

echo "/usr/local/lib/freerdp" > /etc/ld.so.conf.d/freerdp.conf
ldconfig


# create user
useradd -m -U -c "RDP User" -G shadow,audio,pulse,pulse-access -s /bin/bash $RDPUSER

# create user config directory
CONF_DIR="/home/$RDPUSER/.yatc"
mkdir $CONF_DIR
chown $RDPUSER:$RDPUSER $CONF_DIR

# add group for ssh access
groupadd ssh_users

# give ssh access to Metrex User and Remote configuration user
usermod -a -G ssh_users $ADM_USER

# configure ssh
SSHD_CONF=/etc/ssh/sshd_config
sed -i "{s/PermitRootLogin yes/PermitRootLogin no/}" $SSHD_CONF 
echo -e "AllowGroups\tssh_users" >> $SSHD_CONF
service ssh restart

# Unmute alsa & pulseaudio
amixer set PCM unmute || echo "Can't unmute PCM. Skipping..."
amixer set Master unmute
sudo -i -u $RDPUSER pulseaudio -D
sleep 1
sudo -i -u $RDPUSER pactl set-sink-mute 0 0

# install python library for pam authentication
cd /tmp
git clone https://github.com/leonnnn/python3-simplepam.git
cd ./python3-simplepam
python3 setup.py install

# install python library for simple encryption and decryption
cd /tmp
git clone https://github.com/andrewcooke/simple-crypt.git
cd ./simple-crypt/
python3 setup.py install

# install YATC
YATCBIN=/usr/bin/yatc
YATCLIB=/usr/lib/yatc
cd /tmp
git clone https://github.com/nixargh/yatc.git
cd ./yatc
git checkout $YATC_BRANCH

python3 -mpy_compile ./yatc.py
mv ./__pycache__/yatc.*.pyc $YATCBIN
chmod 755 $YATCBIN

CRYPT_LIB="./lib/crypt.py"
sed -i "{s/VerySecurePassphrase/$RANDOM$DATE1$RANDOM$DATE2/}" $CRYPT_LIB
python3 -mpy_compile $CRYPT_LIB
mkdir -p $YATCLIB
mv ./lib/__pycache__/crypt.*.pyc $YATCLIB/crypt.pyc
chmod 755 -R $YATCLIB

# make user autologin
# http://blog.shvetsov.com/2010/09/auto-login-ubuntu-user-from-cli.html
TTY_CONF=/etc/init/tty1.conf
sed -i '{s/exec/#exec/}' $TTY_CONF 
echo "exec /bin/login -f $RDPUSER < /dev/tty1 > /dev/tty1 2>&1" >> $TTY_CONF

# add some rights to user
echo -e "$RDPUSER\tALL=(root) NOPASSWD:/sbin/reboot,/sbin/poweroff\n" >> /etc/sudoers

# setup X and application to start on boot at terminal
BASH_PROFILE=/home/$RDPUSER/.bash_profile
echo -e "pulseaudio -D\n. startx" > $BASH_PROFILE

# /home/user/.xinitrc
XINITRC=/home/$RDPUSER/.xinitrc
echo "python3 $YATCBIN -- -depth 32" > $XINITRC

# fix onership
chown $RDPUSER:$RDPUSER -R /home/$RDPUSER

# set cupsd to listen on all interfaces
# and allow access from subnet
CUPSD_CONF=/etc/cups/cupsd.conf
mv $CUPSD_CONF $CUPSD_CONF.orig
awk '/\/Location/ {print "  Allow from 10.*"; print; next }1' $CUPSD_CONF.orig >> $CUPSD_CONF
sed -i '{s/127.0.0.1/0.0.0.0/}' $CUPSD_CONF
sed -i '{s/localhost/0.0.0.0/}' $CUPSD_CONF
service cups restart

# setup autofs
echo -e "usbdisk\t-fstype=auto,async,nodev,nosuid,umask=000\t:/dev/sdb1" >> /etc/auto.misc
echo -e "/media\t/etc/auto.misc\t--timeout=20\n" >> /etc/auto.master

# enable puppet
puppet agent --enable

# Finaly reboot
reboot
