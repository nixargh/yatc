#!/usr/bin/python3
#### INFO ####################################################################
# Yet Another Thin Client - small gui application to start freerdp session
# to MS Terminal Server
# (*w) author: nixargh <nixargh@gmail.com>
__version__ = "0.4.3"
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
from simplecrypt import encrypt, decrypt
##############################################################################
logFile = os.path.expanduser("~/yatc.log")
#mediaMountDir = "/media"
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
    logging.info("%s authenticated." % user)
    return True
  else:
    logging.info("%s failed to authenticate: %s" % (user, auth))
    return False

# check if TCP port 3389 at host is opened
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

# get user with uid = 1000
#
def getAdmuser():
  file = open("/etc/passwd", "r")
  for line in file:
    line = line.rsplit(":")
    user = line[0]
    uid = int(line[2])
    if uid == 1000:
      return user
  return False

## get list of USB storage devices mounted inside /media
##
#def getUSBList():
#  USBList = []
#  for entry in os.listdir(mediaMountDir):
#    dir = os.path.join(mediaMountDir, entry)
#    if os.path.isdir(dir):
#      USBList.append(dir)
#  return USBList
#
#
## create xfreerdp formated list of disks to redirect
##
#def diskList():
#  disksString = ''
#  USBList = getUSBList()
#  for usbd in USBList:
#    disksString = disksString + ',' + os.path.basename(usbd) + ',' + usbd
#  return disksString

# Logging
#
def createLog():
  logging.basicConfig(filename = logFile, level = logging.INFO, format = '%(levelname)-8s [%(asctime)s] %(message)s') 
##############################################################################
# Encryption class
#
class Crypt():
  def __init__(self):
    self.passpharase = "VerySecurePassphrase"
    logging.info("Encryption initialised.")

  def encryptString(self, string):
    return encrypt(self.passpharase, string)

  def decryptString(self, encryptedString):
    return decrypt(self.passpharase, encryptedString).decode('utf-8')

# Operations with configuration
#
class Config():
  def __init__(self):
    self.configFile = os.path.expanduser("~/.config/yatc")
    self.config = {}
    self.crypt = Crypt()
    logging.info("Config initialized.")

  def createConfig(self):
    file = open(self.configFile, "wb")
    string = self.crypt.encryptString("admuser=%s\n" % getAdmuser())
    file.write(string)
    file.close()

  # read config from file
  #
  def read(self):
    if not os.path.isfile(self.configFile):
      self.createConfig()
    file = open(self.configFile, "rb")
    conf = {} 
    cryptedInfo = file.read()
    info = self.crypt.decryptString(cryptedInfo)
    settings = info.rsplit("\n")
    for line in settings:
      if len(line) > 0:
        attr, value = line.rsplit("=")
        conf[attr] = value
    file.close()
    logging.info("Configuration read.")
    logging.debug(conf)
    self.config = conf

  # write config to file
  #
  def write(self):
    # don't save user if this option unchecked
    if self.config.get("login"):
      if self.config["saveUser"] == 0:
        del self.config["login"]

    # create settings string
    string = ""
    for attr, value in self.config.items():
      string = string + ("%s=%s\n" % (attr, value))
    cryptedLine = self.crypt.encryptString(string)
    # write settings to file
    file = open(self.configFile, "wb")
    file.write(cryptedLine)
    file.close() 
    logging.info("Configuration wrote.")

  # get current configuration
  #
  def get(self):
    logging.debug("Configuration is obtained.")
    return self.config

  # put changed configuration
  #
  def put(self, config):
    logging.debug("Configuration is updated.")
    self.config = config

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

    # version Label
    versionLabel = Label(self.mainFrame, text = __version__, font = ("Helvetica", 6))
    versionLabel.pack(side = "bottom", anchor = "e")

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

    # Button to start RDP connection
    self.connectButton = Button(connectFrame, text = "Подключиться", anchor = "s", pady = 20, font = "bold", state = "disabled", command = self.connectRDP)
    self.connectButton.place(x = 50, y = 70, width = 300, height = 65)

    # Frame to place login and password things
    credFrame = Frame(connectFrame)
    credFrame.place(x = 50, y = 10, width = 300, height = 50)

    # login things
    loginLabel = Label(credFrame, width = 10, text = "Логин:", anchor = "w")
    loginLabel.grid(row = 1, column = 1)

    self.loginVar = StringVar()
    self.loginEntry = Entry(credFrame, width = 28, textvariable = self.loginVar)
    self.loginEntry.grid(row = 1, column = 2)
    if self.conf.get("login"):
      self.loginEntry.insert(0, self.conf["login"])
    self.loginEntry.focus_set()

    self.loginVar.trace("w", self.enableConnect)

    # password things
    passwordLabel = Label(credFrame, width = 10, text = "Пароль:", anchor = "w")
    passwordLabel.grid(row = 2, column = 1)

    self.passwordVar = StringVar()
    self.passwordEntry = Entry(credFrame, width = 28, show = '*', textvariable = self.passwordVar)
    self.passwordEntry.grid(row = 2, column = 2)

    self.passwordVar.trace("w", self.enableConnect)

  # make connection Button active or disabled
  #
  def enableConnect(self, *args):
    login = self.loginVar.get()
    password = self.passwordVar.get()
    if len(login) > 0 and len(password) > 0:
      self.connectButton.config(state = "active")
    else:
      self.connectButton.config(state = "disabled")


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

    # get user password and clear Entry
    password = self.passwordEntry.get()
    self.passwordEntry.delete(0, END)

    # create List of arguments for system call
    xfreerdp = ["xfreerdp", "/printer:", "/kbd:US", "/cert-ignore", "/bpp:32", "+aero", "+fonts", "/size:" + self.conf["screenRes"], "/u:" + self.conf["login"], "/p:" + password]

    # remove login information from conf dictionary if required
    if self.conf["saveUser"] == 0:
      self.loginEntry.delete(0, END)
      if self.conf.get("login"):
        del self.conf["login"]
    else:
      # return and write config
      self.config.put(self.conf)
      self.config.write()

    # check if we need to use RemoteFX
    if self.conf.get("rfx"):
      if int(self.conf["rfx"]) == 1:
        logging.debug("RemoteFX enabled.")
        xfreerdp.append("/rfx")

    # check if we need to redirect USB storage device
    if self.conf.get("usb"):
      if int(self.conf["usb"]) == 1:
        logging.debug("USB storage device redirection enabled.")
        xfreerdp.append("/drive:usbdisk,/media/usb")

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

    xfreerdp.append("/v:%s" % host)
    xfreerdp.append("/d:%s" % domain)

    if hostOnline:
      # start RDP session by freerdp
      logging.debug("Config before rdp start: %s" % self.conf)
      # hide root window
      self.root.withdraw()
      try:
        # start freerdp
        call(xfreerdp)
      except BaseException as err:
        logging.error("freerdp connection failed with: " % err)

      # show root window
      self.root.deiconify()
    else:
      logging.error("All RDP destinations are offline.")


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
        settings = Settings(self.root, self.config)
        
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
    self.askPassEntry.focus_set()
    
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
  def __init__(self, parent, config):
    self.conf = config.get()
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

    host1Entry = Entry(settingsFrame, width = 25)
    host1Entry.grid(row = 1, column = 2, columnspan = 2)
    if self.conf.get("host1"):
      host1Entry.insert(0, self.conf["host1"])
    self.host1 = host1Entry.get

    # Second terminal server
    host2Label = Label(settingsFrame, text = "Сервер 2:", anchor = "w", width = 10)
    host2Label.grid(row = 2, column = 1)

    host2Entry = Entry(settingsFrame, width = 25)
    host2Entry.grid(row = 2, column = 2, columnspan = 2)
    if self.conf.get("host2"):
      host2Entry.insert(0, self.conf["host2"])
    self.host2 = host2Entry.get

    # First domain 
    domain1Label = Label(settingsFrame, text = "Домен 1:", anchor = "w", width = 10)
    domain1Label.grid(row = 3, column = 1)

    domain1Entry = Entry(settingsFrame, width = 25)
    domain1Entry.grid(row = 3, column = 2, columnspan = 2)
    if self.conf.get("domain1"):
      domain1Entry.insert(0, self.conf["domain1"])
    self.domain1 = domain1Entry.get

    # Second domain 
    domain2Label = Label(settingsFrame, text = "Домен 2:", anchor = "w", width = 10)
    domain2Label.grid(row = 4, column = 1)

    domain2Entry = Entry(settingsFrame, width = 25)
    domain2Entry.grid(row = 4, column = 2, columnspan = 2)
    if self.conf.get("domain2"):
      domain2Entry.insert(0, self.conf["domain2"])
    self.domain2 = domain2Entry.get

    # Check box to save login for future sessions
    saveUserLabel = Label(settingsFrame, text = "Запоминать логин:", anchor = "w", width = 25)
    saveUserLabel.grid(row = 5, column = 1, columnspan = 2)

    self.saveUser = IntVar()
    saveUserCheckbutton = Checkbutton(settingsFrame, variable = self.saveUser)
    saveUserCheckbutton.grid(row = 5, column = 3)
    if self.conf.get("saveUser"):
      if int(self.conf.get("saveUser")) == 1:
        saveUserCheckbutton.select()
    
    # Check box to enable/disable RemoteFX 
    rfxLabel = Label(settingsFrame, text = "Использовать RemoteFX:", anchor = "w", width = 25)
    rfxLabel.grid(row = 6, column = 1, columnspan = 2)

    self.rfx = IntVar()
    rfxCheckbutton = Checkbutton(settingsFrame, variable = self.rfx)
    rfxCheckbutton.grid(row = 6, column = 3)
    if self.conf.get("rfx"):
      if int(self.conf.get("rfx")) == 1:
        rfxCheckbutton.select()

    # Check box to enable/disable USB storage redirect 
    usbLabel = Label(settingsFrame, text = "Пробросить USB накопитель:", anchor = "w", width = 25)
    usbLabel.grid(row = 7, column = 1, columnspan = 2)

    self.usb = IntVar()
    usbCheckbutton = Checkbutton(settingsFrame, variable = self.usb)
    usbCheckbutton.grid(row = 7, column = 3)
    if self.conf.get("usb"):
      if int(self.conf.get("usb")) == 1:
        usbCheckbutton.select()

    # show screen resolution at settings screen
    screenResLabel = Label(settingsFrame, text = "Разрешение экрана:", anchor = "w", width = 25)
    screenResLabel.grid(row = 8, column = 1, columnspan = 2)

    screenResEntry = Entry(settingsFrame, width = 10)
    screenResEntry.grid(row = 8, column = 3, columnspan = 1)
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
    self.conf["rfx"] = self.rfx.get()
    self.conf["usb"] = self.usb.get()
    config.put(self.conf)
    config.write()
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
