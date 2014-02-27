# must be executed from root
##### Settings ################################################################
USER=user
ADM_USER=admuser
###############################################################################

# install packages
apt-get update
apt-get install -y python-software-properties
apt-add-repository -y ppa:freerdp-team/freerdp
apt-get update
apt-get install -y freerdp-x11 python3 git xorg python3-tk vim cups puppet

# create user
useradd -m -U -c "RDP User" -s /bin/bash $USER

# create user for remote configuration
#useradd -m -U -G sudo -c "Remote configuration" commander

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
cd /home/$USER
git clone https://github.com/leonnnn/python3-simplepam.git
cd ./python3-simplepam
python3 setup.py install

# install YATC
cd /home/$USER
git clone https://github.com/nixargh/yatc.git

# make user autologin
# http://blog.shvetsov.com/2010/09/auto-login-ubuntu-user-from-cli.html
TTY_CONF=/etc/init/tty1.conf
sed -i {s/exec/#exec/} $TTY_CONF 
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
chown $USER:$USER /home/$USER

# set cupsd to listen on all interfaces
# and allow access from subnet
CUPSD_CONF=/etc/cups/cupsd.conf
mv $CUPSD_CONF $CUPSD_CONF.orig
awk '/\/Location/ {print "  Allow from 10.0.*"; print; next }1' $CUPSD_CONF.orig >> $CUPSD_CONF
sed -i {s/127.0.0.1/0.0.0.0/} $CUPSD_CONF
service cups restart
