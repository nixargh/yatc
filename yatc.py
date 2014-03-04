#!/usr/bin/python3
#### INFO ####################################################################
# Yet Another Thin Client - small gui application to start freerdp session
# to MS Terminal Server
# (*w) author: nixargh <nixargh@gmail.com>
version = "0.2.1"
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
from subprocess import call, check_call, check_output
##############################################################################
##############################################################################
# change current directory to script own directory
#
def chdirToHome():
  abspath = os.path.abspath(__file__)
  dname = os.path.dirname(abspath)
  os.chdir(dname)

# authenticate user using PAM
#
def checkUser(user, password):
  from simplepam import authenticate
  auth = authenticate(user, password)
  if auth:
    logging.info("%s authenticated" % user)
    return True
  else:
    logging.info("%s failed to authenticate: %s" % (user, auth))
    return False

# check if TCP port 3389 is opened at host
#
def checkRDPPort(host):
  try:
    check_call(["nc", "-z", "-w1", host, "3389"])
    return True
  except:
    return False

# get current screen resolution
#
def getScreenRes():
  output = str(check_output(["xrandr"]))
  screenRes = output.rsplit("\n")[0]
  screenRes = screenRes.rsplit(", ")[1]
  _, screenW, _, screeH = screenRes.rsplit(" ")
  return int(screenW), int(screeH)

# Logging
#
def createLog():
  logging.basicConfig(filename = "yatc.log", level = logging.DEBUG, format = '%(levelname)-8s [%(asctime)s] %(message)s') 
##############################################################################

# Operations with configuration
#
class Config():
  def __init__(self):
    self.configFile = "config"
    self.config = {}
    logging.info("Config initialized.")

  # read config from file
  #
  def read(self):
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

    # get X server screen width and height
    screenW, screenH = getScreenRes()
    self.conf["screenRes"] = "%dx%d" % (screenW, screenH)
    logging.info("screen resolution = %s" % self.conf["screenRes"])

    # create root window
    self.root = Tk()

    # set root window geometry
    rootW = 500
    rootH = 300
    SW = (self.root.winfo_screenwidth() - rootW) / 2
    SH = (self.root.winfo_screenheight() - rootH) / 2
    self.root.geometry("%dx%d+%d+%d" % (rootW, rootH, SW, SH))
    
    # create main Frame widget
    self.mainFrame = Frame(self.root, cursor = "left_ptr")
    self.mainFrame.pack(fill = "both", expand = TRUE)

    # start buttons creation
    self.connectFrame()
    self.systemFrame()
    
    # bind Enter to start connection
    self.root.bind("<Return>", self.connectRDP)

    # bind Ctrl+S to open Settings
    self.root.bind("<Control-s>", self.settings)

    self.root.mainloop()
  
  # Connection button
  #
  def connectFrame(self):
    connectFrame = Frame(self.mainFrame, bd = 2, relief = "groove")
    connectFrame.place(x = 50, y = 50, width = 400, height = 150)

    connectButton = Button(connectFrame, text = "Подключиться", anchor = "s", pady = 20, font = "bold", command = self.connectRDP)
    connectButton.place(x = 50, y = 70, width = 300, height = 65)

    credFrame = Frame(connectFrame)
    credFrame.place(x = 50, y = 10, width = 300, height = 50)

    loginLabel = Label(credFrame, width = 10, text = "Логин:", anchor = "w")
    loginLabel.grid(row = 1, column = 1)

    self.loginEntry = Entry(credFrame, width = 28)
    self.loginEntry.grid(row = 1, column = 2)
    if self.conf.get("login"):
      self.loginEntry.insert(0, self.conf["login"])
    self.loginEntry.focus_set()

    passwordLabel = Label(credFrame, width = 10, text = "Пароль:", anchor = "w")
    passwordLabel.grid(row = 2, column = 1)

    self.passwordEntry = Entry(credFrame, width = 28, show = '*')
    self.passwordEntry.grid(row = 2, column = 2)

  # Frame with other button at the bottom of window
  #
  def systemFrame(self):
    systemFrame = Frame(self.mainFrame)
    systemFrame.place(x = 50, y = 250, width = 400 )

    rebootButton = Button(systemFrame, width = 10, text = "Перезагрузить", command = self.reboot)
    rebootButton.pack(side = 'right')

    shutdownButton = Button(systemFrame, width = 10, text = "Выключить", command = self.shutdown)
    shutdownButton.pack(side = 'right')

    #settingsImage = PhotoImage(file = "./images/settings.gif")
    settingsButton = Button(systemFrame, width = 8, text = "Настройки", command = self.settings)
    #settingsButton = Button(systemFrame, image = settingsImage, command = self.settings, relief = "flat")
    #settingsButton.image = settingsImage
    settingsButton.pack(side = 'left')

  # command fro RDP connection
  #
  def connectRDP(self, event = None):
    logging.info("Starting RDP...")

    # get user login
    self.conf["login"] = self.loginEntry.get()

    # save config to save login if option enabled
    if int(self.conf["saveUser"]) == 1:
      self.config.write(self.conf)

    # get user password and clear Entry
    password = self.passwordEntry.get()
    self.passwordEntry.delete(0, END)

    # choose avaliable terminal server to connect
    host = self.conf["host1"]
    domain = self.conf["domain1"]
    hostOnline = True
    if not checkRDPPort(host):
      logging.info("RDP not listening at host1 (%s)" % host)
      host = self.conf["host2"]
      domain = self.conf["domain2"]
      if not checkRDPPort(host):
        logging.info("RDP not listening at host2 (%s)" % host)
        hostOnline = False
    if hostOnline:
      # start RDP session by freerdp
      logging.debug("Config before rdp start: %s" % self.conf)
      # hide root window
      self.root.withdraw()
      try:
        # start freerdp
        call(["xfreerdp", "/printer:", "/kbd:US", "/cert-ignore", "/bpp:16", "/rfx", "/size:" + self.conf["screenRes"], "/d:" + domain, "/u:" + self.conf["login"], "/p:" + password, "/v:" + host])
      except BaseException as err:
        logging.error("freerdp connection failed with: " % err)

      # show root window
      self.root.deiconify()
    else:
      logging.error("All RDP destinations are offline.")

    # remove login information from conf dictionary if required
    if self.conf["saveUser"] == 0:
      self.loginEntry.delete(0, END)
      if self.conf.get("login"):
        del self.conf["login"]


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
  def settings(self, event=None):
    self.password = None
    self.askPassword()
    self.root.wait_window(self.askPassTop)
    if self.password:
      if checkUser(self.conf["admuser"], self.password):
        self.password = None
        settings = Settings(self.root, self.conf)
        
  # password dialog
  #
  def askPassword(self):
    self.askPassTop = Toplevel(self.mainFrame, bd = 2, relief = "raised", cursor = "left_ptr")
    settingsW = 200
    settingsH = 90
    SW = (self.askPassTop.winfo_screenwidth() - settingsW) / 2
    SH = (self.askPassTop.winfo_screenheight() - settingsH) / 2
    self.askPassTop.geometry("%dx%d+%d+%d" % (settingsW, settingsH, SW, SH))
    self.askPassTop.tkraise(self.root)
    self.askPassTop.grab_set()

    askPassLabel = Label(self.askPassTop, text = "Введите пароль для %s:" % self.conf["admuser"])
    askPassLabel.grid(row = 1, column = 1, columnspan = 2)

    self.askPassEntry = Entry(self.askPassTop, width = 20, show = "*")
    self.askPassEntry.grid(row = 2, column = 1, columnspan = 2)
    
    askPassOKButton = Button(self.askPassTop, text = "OK", width = 6, command = self.enterpass, default=ACTIVE)
    askPassOKButton.grid(row = 4, column = 1)

    askPassCancelButton = Button(self.askPassTop, text = "Отменить", width = 6, command = self.askPassTop.destroy)
    askPassCancelButton.grid(row = 4, column = 2)

    self.askPassTop.bind("<Return>", self.enterpass)
  
  # password callback
  #
  def enterpass(self, event=None):
    self.password = self.askPassEntry.get()
    self.askPassTop.destroy()

# Settings window
#
class Settings():
  def __init__(self, parent, conf):
    self.conf = conf
    self.parent = parent

    # hide main window
    #self.parent.withdraw()

    self.window = Toplevel(parent, bd = 2, relief = "raised", cursor = "left_ptr")
    settingsW = 300
    settingsH = 200
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
    # Settings Frame view
    settingsFrame = Frame(self.window, bd = 2, relief = "sunken")
    settingsFrame.pack(side = "top", anchor = "w", fill = "both")

    # First terminal server
    host1Label = Label(settingsFrame, text = "Сервер 1:", anchor = "w", width = 10)
    host1Label.grid(row = 1, column = 1)

    host1Entry = Entry(settingsFrame, width = 20)
    host1Entry.grid(row = 1, column = 2, columnspan = 2)
    if self.conf.get("host1"):
      host1Entry.insert(0, self.conf["host1"])
    self.host1 = host1Entry.get

    # Second terminal server
    host2Label = Label(settingsFrame, text = "Сервер 2:", anchor = "w", width = 10)
    host2Label.grid(row = 2, column = 1)

    host2Entry = Entry(settingsFrame, width = 20)
    host2Entry.grid(row = 2, column = 2, columnspan = 2)
    if self.conf.get("host2"):
      host2Entry.insert(0, self.conf["host2"])
    self.host2 = host2Entry.get

    # First domain 
    domain1Label = Label(settingsFrame, text = "Домен 1:", anchor = "w", width = 10)
    domain1Label.grid(row = 3, column = 1)

    domain1Entry = Entry(settingsFrame, width = 20)
    domain1Entry.grid(row = 3, column = 2, columnspan = 2)
    if self.conf.get("domain1"):
      domain1Entry.insert(0, self.conf["domain1"])
    self.domain1 = domain1Entry.get

    # Second domain 
    domain2Label = Label(settingsFrame, text = "Домен 2:", anchor = "w", width = 10)
    domain2Label.grid(row = 4, column = 1)

    domain2Entry = Entry(settingsFrame, width = 20)
    domain2Entry.grid(row = 4, column = 2, columnspan = 2)
    if self.conf.get("domain2"):
      domain2Entry.insert(0, self.conf["domain2"])
    self.domain2 = domain2Entry.get

    # Check box to save login for future sessions
    saveUserLabel = Label(settingsFrame, text = "Запоминать логин:", anchor = "w", width = 20)
    saveUserLabel.grid(row = 5, column = 1, columnspan = 2)

    self.saveUser = IntVar()
    saveUserCheckbutton = Checkbutton(settingsFrame, variable = self.saveUser)
    saveUserCheckbutton.grid(row = 5, column = 3)
    if int(self.conf.get("saveUser")) == 1:
      saveUserCheckbutton.select()
    
    # show screen resolution at settings screen
    screenResLabel = Label(settingsFrame, text = "Разрешение экрана:", anchor = "w", width = 20)
    screenResLabel.grid(row = 6, column = 1, columnspan = 2)

    screenResEntry = Entry(settingsFrame, width = 10)
    screenResEntry.grid(row = 6, column = 3, columnspan = 1)
    screenResEntry.insert(0, self.conf["screenRes"])
    screenResEntry.config(state = "readonly")

  # command to close Settings window and save settings
  #
  def quitSettings(self):
    self.conf["host1"] = self.host1()
    self.conf["domain1"] = self.domain1()
    self.conf["host2"] = self.host2()
    self.conf["domain2"] = self.domain2()
    self.conf["saveUser"] = self.saveUser.get()
    config = Config()
    config.write(self.conf)
    self.window.destroy()
    #self.parent.deiconify()

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
