#!/bin/bash
# script to deploy YATC on Ubuntu 12.04 - 14.04 (netinstall with only ssh server installed)
# (*w) author: nixargh <nixargh@gmail.com>
VERSION="0.9.7"
##### Settings ################################################################
# !!! must be executed from root !!!
RDPUSER="user"
TIMEZONE="Europe/Moscow"
FREERDP_REPO="https://github.com/FreeRDP/FreeRDP.git"
FREERDP_BRANCH="c9bc88d5f0fed0de03ee697dd382ba8f8a434a82"
YATC_REPO="https://github.com/nixargh/yatc.git"
YATC_BRANCH="dev"
TWOXCLIENT="http://www.2x.com/downloads/rdp-clients/2xclient.deb"
TWOXCLIENT_VER="12.0.2270"
TWOXCLIENT_CHANGELOG="http://www.2x.com/downloads/rdp-clients/Linux-ChangeLog.txt"
###############################################################################
set -u -e

# check that you are root
check_user() {
  if [ $USER != "root" ]; then
    echo "You must be root."
    exit 1
  fi
}

common() {
  echo -e "\tCommon configuration starting.\n"

  # set timezone
  cp -f /usr/share/zoneinfo/$TIMEZONE /etc/localtime

  DATE1=`date +%s%N`

  # detect admuser
  ADM_USER=`grep 1000 /etc/passwd |awk 'BEGIN{FS=":"} {print $1}'`

  # install required packages
  apt-get update
  apt-get install -y python3 python3-tk python3-crypto git xorg vim cups puppet autofs libasound2 \
    libasound2-plugins libasound2-plugins:i386 alsa-utils alsa-oss pulseaudio pulseaudio-utils dbus-x11 curl

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
  amixer set PCM 100 unmute || echo "Can't unmute PCM. Skipping..."
  amixer set Master 100 unmute
  sudo -i -u $RDPUSER dbus-launch --exit-with-session pulseaudio --daemon
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
  git clone $YATC_REPO
  cd ./yatc
  git checkout $YATC_BRANCH

  DATE2=`date +%s%N`

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
  echo -e "dbus-launch --exit-with-session pulseaudio --daemon\n. startx" > $BASH_PROFILE

  # /home/user/.xinitrc
  XINITRC=/home/$RDPUSER/.xinitrc
  echo "python3 $YATCBIN $BACKEND -- -depth 32" > $XINITRC

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

  echo -e "\tCommon configuration finished."
  return 0
}

freerdp() {
  echo -e "\tFreeRDP installation starting.\n"

  # install FreeRDP from git
  apt-get install -y build-essential git-core cmake libssl-dev libx11-dev libxext-dev libxinerama-dev \
    libxcursor-dev libxdamage-dev libxv-dev libxkbfile-dev libasound2-dev libcups2-dev libxml2 libxml2-dev \
    libxrandr-dev libgstreamer0.10-dev libgstreamer-plugins-base0.10-dev libxi-dev libavcodec-dev libpulse-dev

  cd /tmp
  git clone $FREERDP_REPO
  cd ./FreeRDP
  git checkout $FREERDP_BRANCH

  cmake -DCMAKE_BUILD_TYPE=Debug -DWITH_SSE2=ON -DWITH_CUPS=ON -DCHANNEL_PRINTER=ON -DWITH_PULSE=ON .

  make
  make install

  echo "/usr/local/lib/freerdp" > /etc/ld.so.conf.d/freerdp.conf
  ldconfig

  echo -e "\tFreeRDP installation finished."
  return 0
}


twoxclient() {
  echo -e "\t2X RDP client installation starting.\n"

  dpkg --add-architecture i386

  apt-get install -y pcscd:i386 libccid:i386 libpcsclite1:i386 libxpm4:i386 libxml2:i386 libstdc++6:i386

  cd /tmp
  wget $TWOXCLIENT -O ./2xclient.deb
  dpkg -i ./2xclient.deb
  sleep 1

  local VER=`dpkg -s 2xclient |grep Version |awk '{ print $2 }'`
  if [ $VER != $TWOXCLIENT_VER ]; then
    echo -e "\tWARNING!\n\t2xclient version changed from tested. Current: $VER. Tested: $TWOXCLIENT_VER."

    echo -e "\tChangelog:"
    curl -s $TWOXCLIENT_CHANGELOG |head -20 2>/dev/null

    echo -e "\n\tAutomatic restart cancelled. Read changelog attentively and reboot manually."

    exit 2
  fi

  echo -e "\t2X RDP client installation finished."
  return 0
}

##### BEGIN ###################################################################

if [[ $# -eq 0 ]]; then
  echo -e "\tYou must specify RDP backend [freerdp|2xclient]."
  exit 2
else
  BACKEND=$1

  echo -e "\tStarting to install YATC with $BACKEND RDP backend."
  case $BACKEND in
    freerdp)
      check_user
      common
      freerdp
    ;;
    2xclient)
      check_user
      common
      twoxclient
    ;;
    *)
      echo -e "\tUnknown backend: $BACKEND."
      exit 2
    ;;
  esac

  echo -e "\tYATC installation finished. Rebooting in 3 seconds."
  sleep 3
  reboot
fi
