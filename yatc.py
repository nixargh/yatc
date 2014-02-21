#!/usr/bin/python3
#### INFO ####################################################################
# Yet Another Thin Client - small gui application to start freerdp session
# to MS Terminal Server
# (*w) author: nixargh <nixargh@gmail.com>
version = "0.1.2"
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
import os
import time
from tkinter import *
from subprocess import call
##############################################################################
config_dir = "./yatc"
config = "config"
##############################################################################
def createLog():
  import logging
  logging.basicConfig(filename = 'yatc.log', level = logging.DEBUG) 
  return logging
  
def readConf():
  if os.path.isdir(config_dir):
    os.chdir(config_dir)
  file = open(config, "r")
  user = file.readline().rstrip('\r\n')
  domain = file.readline().rstrip('\r\n')
  password = file.readline().rstrip('\r\n')
  server = file.readline().rstrip('\r\n')
  return user, domain, password, server

def createRoot():
  root = Tk()
  rootW = 500
  rootH = 300
  SW = (root.winfo_screenwidth() - rootW) / 2
  SH = (root.winfo_screenheight() - rootH) / 2
  root.geometry("%dx%d+%d+%d" % (rootW, rootH, SW, SH))
  return root

def connectButton(parent):
  connectButton = Button(parent, text = "Connect", anchor = "s", pady = 20, font = "bold", command = connectRDP)
  connectButton.place(x = 75, y = 50, width = 350, height = 130)

  credFrame = Frame(connectButton)
  credFrame.place(x = 25, y = 10)

  loginLabel = Label(credFrame, width = 7, text = "Логин:", anchor = "w")
  loginLabel.grid(row = 1, column = 1)

  loginEntry = Entry(credFrame, bd = 2, width = 28)
  loginEntry.grid(row = 1, column = 2)

  passwordLabel = Label(credFrame, width = 7, text = "Пароль:", anchor = "w")
  passwordLabel.grid(row = 2, column = 1)

  passwordEntry = Entry(credFrame, bd = 2, width = 28, show = '*')
  passwordEntry.grid(row = 2, column = 2)
  return connectButton

def systemFrame(parent):
  systemFrame = Frame(parent)
  systemFrame.place(x = 75, y = 250, width = 350 )

  rebootButton = Button(systemFrame, width = 10, text = "Reboot", command = reboot)
  rebootButton.pack(side = 'right')

  shutdownButton = Button(systemFrame, width = 10, text = "Shutdown", command = shutdown)
  shutdownButton.pack(side = 'right')

  settingsButton = Button(systemFrame, width = 5, text = "Settings", command = settings)
  settingsButton.pack(side = 'left')
  return systemFrame

def createSettings(parent):
  settings = Toplevel(parent)
  settingsW = 250
  settingsH = 150
  SW = (settings.winfo_screenwidth() - settingsW) / 2
  SH = (settings.winfo_screenheight() - settingsH) / 2
  settings.geometry("%dx%d+%d+%d" % (settingsW, settingsH, SW, SH))
  settings.tkraise(parent)
  settings.grab_set()

  closeButton = Button(settings, text = "Close", width = 5, command = settings.destroy())
  closeButton.pack(side = "bottom")

  return settings

def connectRDP():
  log.debug("Starting RDP...")
  root.withdraw()
  result = call(["xfreerdp", "/cert-ignore", "/bpp:16", "/rfx", "/d:" + domain, "/u:" + user, "/p:" + password, "/v:" + server])
  log.info(call)
  root.deiconify()

def reboot():
  call(["sudo", "reboot"])

def shutdown():
  call(["sudo", "poweroff"])

def settings():
  createSettings(root)

def quitSettings(parent):
  parent.destroy()

##############################################################################
global log
log = createLog()
log.info("%s\tStarting yatc..." % time.asctime())

user, domain, password, server = readConf()
log.debug("user = %s; domain = %s; password = %s; server = %s;", user, domain, password, server) 

root = createRoot()
connectButton(root)
systemFrame(root)

root.mainloop()
