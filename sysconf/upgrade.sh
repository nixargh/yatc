#!/bin/bash
# script to upgrade YATC on Ubuntu 12.04 - 14.04
# (*w) author: nixargh <nixargh@gmail.com>
VERSION="0.9.9"
##### Settings ################################################################
# !!! must be executed from root !!!
RDPUSER="user"
FREERDP_REPO="https://github.com/FreeRDP/FreeRDP.git"
FREERDP_BRANCH="c9bc88d5f0fed0de03ee697dd382ba8f8a434a82"
YATC_REPO="https://github.com/nixargh/yatc.git"
YATC_BRANCH="devel"
TMP_DIR="/tmp"
TWOXCLIENT_VER="14.0.3213"
TWOXCLIENT="http://www.2x.com/downloads/builds/applicationserver/${TWOXCLIENT_VER}/2XClient.deb"
###############################################################################
set -u -e

# Check that you are root.
#
check_root() {
  if [ $USER != "root" ]; then
    echo "You must be root."
    return 1
  fi
  return 0
}

# Upgrade FreeRDP.
#
upgrade_freerdp() {
  cd $TMP_DIR
  git clone $FREERDP_REPO
  cd ./FreeRDP
  git checkout $FREERDP_BRANCH

  cmake -DCMAKE_BUILD_TYPE=Debug -DWITH_SSE2=ON -DWITH_CUPS=ON -DCHANNEL_PRINTER=ON -DWITH_PULSE=ON .
  make
  make install

  return 0
}

# Upgrade YATC.
#
upgrade_yatc() {
  local YATCBIN=/usr/bin/yatc
  local YATCLIB=/usr/lib/yatc

  cd $TMP_DIR
  git clone $YATC_REPO
  cd ./yatc
  git checkout $YATC_BRANCH

  python3 -mpy_compile ./yatc.py
  mv ./__pycache__/yatc.*.pyc $YATCBIN
  chmod 755 $YATCBIN

  apt-get purge -y autofs

  # create directory to store mountpoints
  mkdir /media/usbdisk
  chown $RDPUSER /media/usbdisk

  return 0
}

# Upgrade 2xclient.
#
upgrade_twoxclient() {
	echo -e "\t2X RDP client upgrade starting.\n"

	dpkg --add-architecture i386

	apt-get install -y pcscd:i386 libccid:i386 libpcsclite1:i386 libxpm4:i386 libxml2:i386 libstdc++6:i386 cryptsetup-bin libcryptsetup4 liblvm2app2.2 udisks

	cd /tmp
	wget $TWOXCLIENT -O ./2xclient.deb
	dpkg -i ./2xclient.deb

	echo -e "\t2X RDP client upgrade finished."
	return 0
}

# Create user config directory.
#
create_config_dir() {
  local CONF_DIR="/home/$RDPUSER/.yatc"

  if [ ! -d $CONF_DIR ]; then
    mkdir $CONF_DIR
    chown $RDPUSER:$RDPUSER $CONF_DIR
  fi
  return 0
}

# Unmute alsa & pulseaudio.
#
unmute() {
  if [ `ps aux | grep -v grep |grep -c pulseaudio` -eq 0 ]; then
    for DEV in "PCM" "Master"; do
      amixer set $DEV 100 unmute || echo "Can't unmute $DEV. Skipping..."
    done
    sudo -i -u $RDPUSER pulseaudio -D
    sleep 1
    sudo -i -u $RDPUSER pactl set-sink-mute 0 0
  fi

  return 0
}
##### BEGIN ###################################################################

JOB=$1

echo "Starting upgrade of $1."

check_root || exit 0

case $JOB in
  freerdp)
    upgrade_freerdp
  ;;
  2xclient)
    upgrade_twoxclient
  ;;
  yatc)
    create_config_dir
    upgrade_yatc
  ;;
esac

# fix onership
chown $RDPUSER:$RDPUSER -R /home/$RDPUSER

echo "Upgraded."
