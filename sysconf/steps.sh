# execute from root

# install packages
apt-get update
apt-get install -y python-software-properties
apt-add-repository -y ppa:freerdp-team/freerdp
apt-get update
apt-get install -y freerdp-x11 python3 git xorg python3-tk vim cups

# create user
useradd -m -U -c "RDP User" user

# make user autologin
# http://blog.shvetsov.com/2010/09/auto-login-ubuntu-user-from-cli.html
# comment last line at /etc/init/tty1.conf
# add "exec /bin/login -f user < /dev/tty1 > /dev/tty1 2>&1"

# add some rights to user
echo -e "user\tALL=(root) NOPASSWD:/sbin/reboot,/sbin/poweroff\n" >> /etc/sudoers

# add something to users xinitrc and bash_profile

# /home/user/.bash_profile
#Startx Automatically
#if [[ -z "$DISPLAY" ]] && [[ $(tty) = /dev/tty1 ]]; then
# . startx
#fi

# /home/user/.xinitrc
echo "./yatc/yatc.py  -- -depth 16" > /home/user/.xinitrc

# set cupsd to listen on all interfaces
sed -i {s/127.0.0.1/0.0.0.0/} /etc/cups/cupsd.conf
