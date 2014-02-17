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
##############################################################################
def connectRDP():
  print("connecting...")

def reboot():
  print("rebooting...")
##############################################################################
root = Tk()
SW = root.winfo_screenwidth() / 3.2
SH = root.winfo_screenheight() / 3.2
root.geometry("500x300+%d+%d" % (SW, SH))
connectButton = Button(root, text="Connect", command=connectRDP)
connectButton.pack()

rebootButton = Button(root, text="Reboot", command=reboot)
rebootButton.pack()

root.mainloop()
