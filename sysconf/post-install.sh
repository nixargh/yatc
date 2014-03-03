#!/bin/bash
# must be executed from root
##### Settings ################################################################
USER=user
ADM_USER=admuser
###############################################################################

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

cmake -DCMAKE_BUILD_TYPE=Debug -DWITH_SSE2=ON -DWITH_CUPS=ON -DCHANNEL_PRINTER=ON .

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

# install python module for pam authentication
cd /tmp
git clone https://github.com/leonnnn/python3-simplepam.git
cd ./python3-simplepam
python3 setup.py install

# install YATC
cd /home/$USER
git clone https://github.com/nixargh/yatc.git

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
echo "./yatc/yatc.py  -- -depth 16" > $XINITRC

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
