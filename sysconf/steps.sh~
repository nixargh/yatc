# execute from root

# install packages
apt-get update
apt-get install -y python-software-properties
apt-add-repository -y ppa:freerdp-team/freerdp
apt-get update
apt-get install -y freerdp-x11 python3.2 git xorg python3-tk vim

# create user
useradd -m -U -c "RDP User" user

# make user autologin
# http://blog.shvetsov.com/2010/09/auto-login-ubuntu-user-from-cli.html
# comment last line at /etc/init/tty1.conf
# add "exec /bin/login -f user < /dev/tty1 > /dev/tty1 2>&1"

# add some rights to user
echo -e "user\tALL=(root) NOPASSWD:reboot,shutdown\n" >> /etc/sudoers

# add something to users xinitrc and bash_profile
