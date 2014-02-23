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
import logging
from tkinter import *
from subprocess import call
##############################################################################
##############################################################################
def chdirToHome():
  abspath = os.path.abspath(__file__)
  dname = os.path.dirname(abspath)
  os.chdir(dname)

# Logging
#
def createLog():
  logging.basicConfig(filename = "yatc.log", level = logging.DEBUG, format = u"%(levelname)-8s [%(asctime)s] %(message)s") 
##############################################################################

# Operations with configuration
#
class Config():
  def __init__(self):
  #  self.configDir = "./yatc"
    self.configFile = "config"
    self.config = {}
    logging.info("Config initialized.")

  # read config from file
  #
  def read(self):
  #  if os.path.isdir(self.configDir):
  #    os.chdir(self.configDir)
    file = open(self.configFile, "r")
    conf = {} 
    for line in file:
      line = line.rstrip("\r\n")
      attr, value = line.rsplit("=")
      conf[attr] = value
    file.close()
    logging.info("Configuration read.")
    logging.debug(conf)
    self.config = conf

  # write config to file
  #
  def write(self, config):
    # don't save user if this option unchecked
    if config["saveUser"] == 0:
      del config["login"]

    # write settings to file
#    if os.path.isdir(self.configDir):
#      os.chdir(self.configDir)
    file = open(self.configFile, "w")
    for attr, value in config.items():
      file.write("%s=%s\n" % (attr, value))
    file.close() 
    logging.info("Configuration wrote.")

  # return config value
  #
  def get(self):
    return self.config

# Main apllication window
#
class App():
  def __init__(self, config):
    logging.info("Starting GUI...")

    self.config = config
    self.conf = config.get()

    self.root = Tk()

    self.connectButton()
    self.systemFrame()
    
    rootW = 500
    rootH = 300
    SW = (self.root.winfo_screenwidth() - rootW) / 2
    SH = (self.root.winfo_screenheight() - rootH) / 2
    self.root.geometry("%dx%d+%d+%d" % (rootW, rootH, SW, SH))
    
    self.root.mainloop()
  
  # Connection button
  #
  def connectButton(self):
    connectButton = Button(self.root, text = "Connect", anchor = "s", pady = 20, font = "bold", command = self.connectRDP)
    connectButton.place(x = 75, y = 50, width = 350, height = 130)

    credFrame = Frame(connectButton)
    credFrame.place(x = 25, y = 10)

    loginLabel = Label(credFrame, width = 7, text = "Логин:", anchor = "w")
    loginLabel.grid(row = 1, column = 1)

    loginEntry = Entry(credFrame, width = 28)
    loginEntry.grid(row = 1, column = 2)
    if self.conf.get("login"):
      loginEntry.insert(0, self.conf["login"])
    self.login = loginEntry.get

    passwordLabel = Label(credFrame, width = 7, text = "Пароль:", anchor = "w")
    passwordLabel.grid(row = 2, column = 1)

    passwordEntry = Entry(credFrame, width = 28, show = '*')
    passwordEntry.grid(row = 2, column = 2)
    self.password = passwordEntry.get

  # Frame with other button at the bottom of window
  #
  def systemFrame(self):
    systemFrame = Frame(self.root)
    systemFrame.place(x = 75, y = 250, width = 350 )

    rebootButton = Button(systemFrame, width = 10, text = "Reboot", command = self.reboot)
    rebootButton.pack(side = 'right')

    shutdownButton = Button(systemFrame, width = 10, text = "Shutdown", command = self.shutdown)
    shutdownButton.pack(side = 'right')

    settingsButton = Button(systemFrame, width = 5, text = "Settings", command = self.settings)
    settingsButton.pack(side = 'left')

  # command fro RDP connection
  #
  def connectRDP(self):
    self.conf["login"] = self.login()

    # save config to save login if option enabled
    if int(self.conf["saveUser"]) == 1:
      self.config.write(self.conf)

    self.conf["password"] = self.password()
    logging.info("Starting RDP...")
    self.root.withdraw()
    logging.debug("Config before rdp start: %s" % self.conf)
    result = call(["xfreerdp", "/cert-ignore", "/bpp:16", "/rfx", "/d:" + self.conf["domain"], "/u:" + self.conf["login"], "/p:" + self.conf["password"], "/v:" + self.conf["host"]])
    logging.debug("Connection result: %s" % result)
    self.root.deiconify()

  # command for reboot
  #
  def reboot(self):
    call(["sudo", "reboot"])

  # command for shutdown
  # 
  def shutdown(self):
    call(["sudo", "poweroff"])

  # command to start Settings window
  #
  def settings(self):
    settings = Settings(self.root, self.conf)

# Settings window
#
class Settings():
  def __init__(self, parent, conf):
    self.conf = conf
    self.window = Toplevel(parent)
    settingsW = 250
    settingsH = 150
    SW = (self.window.winfo_screenwidth() - settingsW) / 2
    SH = (self.window.winfo_screenheight() - settingsH) / 2
    self.window.geometry("%dx%d+%d+%d" % (settingsW, settingsH, SW, SH))
    self.window.tkraise(parent)
    self.window.grab_set()

    self.createSettingsFrame()

    closeButton = Button(self.window, text = "Close", width = 5, command = self.quitSettings) 
    closeButton.pack(side = "bottom")

  # Frame with settings
  #
  def createSettingsFrame(self):
    settingsFrame = Frame(self.window)
    settingsFrame.pack(side = "top")

    hostLabel = Label(settingsFrame, text = "Сервер:", anchor = "w", width = 10)
    hostLabel.grid(row = 1, column = 1)

    hostEntry = Entry(settingsFrame, width = 20)
    hostEntry.grid(row = 1, column = 2, columnspan = 2)
    if self.conf.get("host"):
      hostEntry.insert(0, self.conf["host"])
    self.host = hostEntry.get

    domainLabel = Label(settingsFrame, text = "Домен:", anchor = "w", width = 10)
    domainLabel.grid(row = 2, column = 1)

    domainEntry = Entry(settingsFrame, width = 20)
    domainEntry.grid(row = 2, column = 2, columnspan = 2)
    if self.conf.get("domain"):
      domainEntry.insert(0, self.conf["domain"])
    self.domain = domainEntry.get

    saveUserLabel = Label(settingsFrame, text = "Запоминать логин:", anchor = "w", width = 20)
    saveUserLabel.grid(row = 3, column = 1, columnspan = 2)

    self.saveUser = IntVar()
    saveUserCheckbutton = Checkbutton(settingsFrame, variable = self.saveUser)
    saveUserCheckbutton.grid(row = 3, column = 3)
    if int(self.conf.get("saveUser")) == 1:
      saveUserCheckbutton.select()

  # command to close Settings window and save settings
  #
  def quitSettings(self):
    self.conf["host"] = self.host()
    self.conf["domain"] = self.domain()
    self.conf["saveUser"] = self.saveUser.get()
    config = Config()
    config.write(self.conf)
    self.window.destroy()

##############################################################################
# change directory to script home
chdirToHome()

# create log
createLog()
logging.info("Starting yatc...")

# read configuration
config = Config()
config.read()

# start application
app = App(config)
