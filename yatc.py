#!/usr/bin/python3
#### INFO ####################################################################
# Yet Another Thin Client - small gui application to start freerdp session
# to MS Terminal Server
# (*w) author: nixargh <nixargh@gmail.com>
version = "0.1.0"
#### LICENSE #################################################################
# YATC
# Copyright (C) 2014  nixargh <nixargh@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/gpl.html.
##############################################################################
import sys
from tkinter import *
from subprocess import call
##############################################################################
def readConf():
  file = open("./yatc/config", "r")
  user = file.readline().rstrip('\r\n')
  domain = file.readline().rstrip('\r\n')
  password = file.readline().rstrip('\r\n')
  return user, domain, password

def connectRDP():
  print("connecting...")
  call(["xfreerdp", "/f", "/bpp:16", "/rfx", "/d:" + domain, "/u:" + user, "/p:" + password, "/v:localhost"])

def reboot():
  print("rebooting...")
  call(["sudo", "reboot"])

def shutdown():
  print("shutting down...")
  call(["sudo", "poweroff"])
##############################################################################
user, domain, password = readConf()
root = Tk()

SW = root.winfo_screenwidth() / 3.2
SH = root.winfo_screenheight() / 3.2
root.geometry("500x300+%d+%d" % (SW, SH))

connectButton = Button(root, text = "Connect", command = connectRDP)
connectButton.place(x = 100, y = 50, width = 300, height = 100)

systemFrame = Frame(root)
systemFrame.place(x = 100, y = 250, width = 300 )

rebootButton = Button(systemFrame, text = "Reboot", command = reboot)
rebootButton.pack(side = 'right')

shutdownButton = Button(systemFrame, text = "Shutdown", command = shutdown)
shutdownButton.pack(side = 'right')

root.mainloop()
