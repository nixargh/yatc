# execute from root

# install packages
apt-get update
apt-get install -y python-software-properties
apt-add-repository -y ppa:freerdp-team/freerdp
apt-get update
apt-get install -y freerdp-x11 python3 git xorg python3-tk vim cups

# create user
useradd -m -U -c "RDP User" user

# create user for remote configuration
useradd -m -U -G sudo -c "Remote configuration" commander

# add group for ssh access
groupadd ssh_users

# give ssh access to Metrex User and Remote configuration user
usermod -a -G ssh_users mec_user
usermod -a -G ssh_users commander

# configure ssh
SSHD_CONF=/etc/ssh/sshd_config
sed -i {s/PermitRootLogin yes/PermitRootLogin no/} $SSHD_CONF 
echo -e "AllowGroups\tssh_users" >> $SSHD_CONF
service ssh restart

# copy public key to commander home
#cp $id_rsa.public /home/commander/.shh/authorized_keys

# install YATC
cd /home/user
git clone https://github.com/nixargh/yatc.git

# make user autologin
# http://blog.shvetsov.com/2010/09/auto-login-ubuntu-user-from-cli.html
TTY_CONF=/etc/init/tty1.conf
sed -i {s/exec/#exec/} $TTY_CONF 
echo "exec /bin/login -f user < /dev/tty1 > /dev/tty1 2>&1" >> $TTY_CONF

# add some rights to user
echo -e "user\tALL=(root) NOPASSWD:/sbin/reboot,/sbin/poweroff\n" >> /etc/sudoers

# add something to users xinitrc and bash_profile

# /home/user/.bash_profile
BASH_PROFILE=/home/user/.bash_profile
cat << EOF > $BASH_PROFILE 
#Startx Automatically
if [[ -z "$DISPLAY" ]] && [[ $(tty) = /dev/tty1 ]]; then
 . startx
fi
EOF
chown user:user $BASH_PROFILE 

# /home/user/.xinitrc
XINITRC=/home/user/.xinitrc
echo "./yatc/yatc.py  -- -depth 16" > $XINITRC
chown user:user $XINITRC

# set cupsd to listen on all interfaces
# and allow access from subnet
CUPSD_CONF=/etc/cups/cupsd.conf
mv $CUPSD_CONF $CUPSD_CONF.orig
awk '/\/Location/ {print "  Allow from 192.168.1.*"; print; next }1' $CUPSD_CONF.orig >> $CUPSD_CONF
sed -i {s/127.0.0.1/0.0.0.0/} $CUPSD_CONF
service cups restart
