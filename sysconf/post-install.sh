#!/bin/bash
# script to deploy YATC on Ubuntu 12.04 (netinstall with only ssh installed)
# (*w) author: nixargh <nixargh@gmail.com>
# version 0.1
##### Settings ################################################################
# !!! must be executed from root !!!
USER=user
###############################################################################

# check that you are root
if [ $USER != "root" ]; then
  echo "You must be root."
  exit 1
fi

# detect admuser
ADM_USER=`grep 1000 /etc/passwd |awk 'BEGIN{FS=":"} {print $1}'`

# install packages
apt-get update
apt-get install -y python3 git xorg python3-tk vim cups puppet

# install FreeRDP from git
cd /tmp
git clone git://github.com/FreeRDP/FreeRDP.git
cd ./FreeRDP

apt-get install -y build-essential git-core cmake libssl-dev libx11-dev libxext-dev libxinerama-dev \
libxcursor-dev libxdamage-dev libxv-dev libxkbfile-dev libasound2-dev libcups2-dev libxml2 libxml2-dev \
libxrandr-dev libgstreamer0.10-dev libgstreamer-plugins-base0.10-dev

DATE1=`date +%s%N`

cmake -DCMAKE_BUILD_TYPE=Debug -DWITH_SSE2=ON -DWITH_CUPS=ON -DCHANNEL_PRINTER=ON .

DATE2=`date +%s%N`

make
make install

echo "/usr/local/lib/freerdp" > /etc/ld.so.conf.d/freerdp.conf
ldconfig

mkdir /home/$USER/.config

# create user
useradd -m -U -c "RDP User" -G shadow -s /bin/bash $USER

# add group for ssh access
groupadd ssh_users

# give ssh access to Metrex User and Remote configuration user
usermod -a -G ssh_users $ADM_USER

# configure ssh
SSHD_CONF=/etc/ssh/sshd_config
sed -i {s/PermitRootLogin yes/PermitRootLogin no/} $SSHD_CONF 
echo -e "AllowGroups\tssh_users" >> $SSHD_CONF
service ssh restart

# install python library for pam authentication
cd /tmp
git clone https://github.com/leonnnn/python3-simplepam.git
cd ./python3-simplepam
python3 setup.py install

# install python library for simple encryption and decryption
cd /tmp
git clone https://github.com/andrewcooke/simple-crypt.git
cd ./simple-crypt/
python3 ./setup.py install

# install YATC
cd /home/$USER
git clone https://github.com/nixargh/yatc.git
cd ./yatc
sed -i {s/VerySecurePassphrase/$RANDOM$DATE1$RANDOM$DATE2/} ./yatc.py
python3 -mpy_compile ./yatc.py
mv ./__pycache__/yatc.*.pyc /usr/local/bin/yatc
chmod 755 /usr/local/bin/yatc

# make user autologin
# http://blog.shvetsov.com/2010/09/auto-login-ubuntu-user-from-cli.html
TTY_CONF=/etc/init/tty1.conf
sed -i {s/exec/\#exec/} $TTY_CONF 
echo "exec /bin/login -f $USER < /dev/tty1 > /dev/tty1 2>&1" >> $TTY_CONF

# add some rights to user
echo -e "$USER\tALL=(root) NOPASSWD:/sbin/reboot,/sbin/poweroff\n" >> /etc/sudoers

# setup X and application to start on boot at terminal
#
# /home/user/.bash_profile
BASH_PROFILE=/home/$USER/.bash_profile
echo ". startx" > $BASH_PROFILE

# /home/user/.xinitrc
XINITRC=/home/$USER/.xinitrc
echo "yatc -- -depth 32" > $XINITRC

# fix onership
chown $USER:$USER -R /home/$USER

# set cupsd to listen on all interfaces
# and allow access from subnet
CUPSD_CONF=/etc/cups/cupsd.conf
mv $CUPSD_CONF $CUPSD_CONF.orig
awk '/\/Location/ {print "  Allow from 10.0.*"; print; next }1' $CUPSD_CONF.orig >> $CUPSD_CONF
sed -i {s/127.0.0.1/0.0.0.0/} $CUPSD_CONF
sed -i {s/localhost/0.0.0.0/} $CUPSD_CONF
service cups restart
