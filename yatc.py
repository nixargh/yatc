#!/usr/bin/python3
#### INFO ####################################################################
# Yet Another Thin Client - small gui application to start freerdp session
# to MS Terminal Server
# (*w) author: nixargh <nixargh@gmail.com>
__version__ = "0.9.2"
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
from tkinter import messagebox
from subprocess import *
##############################################################################
logFile = os.path.expanduser("~/.yatc/yatc.log")
versionFile = os.path.expanduser("~/.yatc/version")
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
    check_output(["nc", "-z", "-w1", host, "3389"], stderr=STDOUT)
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

# write version
#
def writeVersion(v_file):
    file = open(v_file, "wb")
    file.write(bytes(__version__ + "\n", 'UTF-8'))
    file.close()


# Logging
#
def createLog():
  logging.basicConfig(filename = logFile, level = logging.INFO, format = '%(levelname)-8s [%(asctime)s] %(message)s') 
##############################################################################

# Operations with configuration
#
class Config():
  def __init__(self):
    from crypt import Crypt

    self.configFile = os.path.expanduser("~/.yatc/yatc.conf")
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
    logging.info("Configuration is obtained.")
    return self.config

  # put changed configuration
  #
  def put(self, config):
    logging.info("Configuration is updated.")
    self.config = config

# Main apllication window
#
class App():
  def __init__(self, rdpBackend, config):
    logging.info("Starting GUI...")

    self.rdpBackend = rdpBackend
    self.config = config
    self.conf = config.get()
    self.rdp = []

    self.rdpOptions = { \
      'backend' : { 'freerdp' : ['xfreerdp'], '2xclient' : ['/opt/2X/Client/bin/appserverclient'] }, \
      'printer' : { 'freerdp' : ['/printer:'], '2xclient' : ['-P', 'printcap'] }, \
      'sound' : { 'freerdp' : ['/sound:sys:pulse'], '2xclient' : ['-S', 'local'] }, \
      'remoteFX' : { 'freerdp' : ['/rfx'], '2xclient' : ['%unsupported%'] }, \
      'usbdisk' : { 'freerdp' : ['/drive:usbdisk,/media/usbdisk'], '2xclient' : ['-D', 'usbdisk=/media/usbdisk'] }, \
      'cdrom' : { 'freerdp' : ['/drive:cdrom,/media/cd'], '2xclient' : ['-D', 'cdrom=/media/cd'] }, \
      'user' : { 'freerdp' : ['/u:%variable%'], '2xclient' : ['-u', '%variable%'] }, \
      'domain' : { 'freerdp' : ['/d:%variable%'], '2xclient' : ['-d', '%variable%'] }, \
      'password' : { 'freerdp' : ['/p:%variable%'], '2xclient' : ['-p', '%variable%'] }, \
      'host' : { 'freerdp' : ['/v:%variable%'], '2xclient' : ['-s', '%variable%'] }, \
      'resolution' : { 'freerdp' : ['/size:%variable%'], '2xclient' : ['-g', '%variable%'] }, \
      'color_depth' : { 'freerdp' : ['/bpp:%variable%'], '2xclient' : ['-c', '%variable%'] }, \
      'extra' : { 'freerdp' : ['/kbd:US', '/cert-ignore', '+aero', '+fonts'], '2xclient' : ['-n', '-m', 'MF'] }
       }

    # get X server screen width and height
    screenW, screenH = getScreenRes()
    self.conf["screenRes"] = "%dx%d" % (screenW, screenH)
    logging.info("Screen resolution = %s" % self.conf["screenRes"])

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

  # Add RDP option from dictionary to list.
  #
  def setRdpOpt(self, opt, variable=None):
    for rdpOpt in self.rdpOptions[opt][self.rdpBackend]: 
      if rdpOpt == '%unsupported%':
        logging.info("%s currently not suported by %s." % (opt, self.rdpBackend))
      elif rdpOpt == '%variable%':
        self.rdp.append(variable)
      else:
        if variable:
          rdpOpt = rdpOpt.replace('%variable%', variable)
        self.rdp.append(rdpOpt)

  # Idiot's dialog.
  #
  def areYouSureDialog(self, question):
    logging.info("Show re-asking dialog")

    self.root.withdraw()

    if messagebox.askokcancel(message = question):
      return True
    else:
      self.root.deiconify()
      return False
  
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

    settingsButton = Button(systemFrame, width = 8, text = "Настройки", command = self.settings)
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
    self.setRdpOpt('backend')
    self.setRdpOpt('extra')
    self.setRdpOpt('printer')
    self.setRdpOpt('resolution', self.conf["screenRes"])
    self.setRdpOpt('user', self.conf["login"])
    self.setRdpOpt('password', password)

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
        self.setRdpOpt('remoteFX')

    # check if we need to redirect USB storage device
    if self.conf.get("usb"):
      if int(self.conf["usb"]) == 1:
        logging.debug("USB storage device redirection enabled.")
        self.setRdpOpt('usbdisk')

    # check if we need to redirect CDROM
    if self.conf.get("cdrom"):
      if int(self.conf["cdrom"]) == 1:
        logging.debug("CDROM redirection enabled.")
        self.setRdpOpt('cdrom')

    # check if we need to forward sound
    if self.conf.get("sound"):
      if int(self.conf["sound"]) == 1:
        logging.debug("Sound forwarding enabled.")
        self.setRdpOpt('sound')

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

    self.setRdpOpt('host', host)
    self.setRdpOpt('domain', domain)

    if hostOnline:
      # start RDP session
      logging.debug("Config before rdp start: %s" % self.conf)
      # hide root window
      self.root.withdraw()
      try:
        # start rdp
        logging.debug("RDP connection string: %s." % self.rdp)
        check_output(self.rdp, universal_newlines=True, stderr=STDOUT)
        logging.info("RDP session ended.")
      except CalledProcessError as err:
        if err.returncode == 255 and self.rdpBackend == 'freerdp':
          logging.info("%s exit code: %s. It's normal after session disconection." % (self.rdpBackend, err.returncode) )
        else:
          logging.error("%s exit code: %s." % (self.rdpBackend, err.returncode) )
          logging.error("%s output:\n%s." % (self.rdpBackend, err.output) )
      except BaseException as err:
        logging.error("Failed to connect: %s." % err)

      # show root window
      self.root.deiconify()
    else:
      logging.error("All RDP destinations are offline.")


  # command for reboot
  #
  def reboot(self):
    logging.info("Reboot requested")
    if self.areYouSureDialog("Перезагрузить компьютер?"):
      logging.info("Rebooting")
      call(["sudo", "reboot"])
    else:
      logging.info("Reboot canceled")

  # command for shutdown
  # 
  def shutdown(self):
    logging.info("Shutdown requested")
    if self.areYouSureDialog("Выключить компьютер?"):
      logging.info("Shutdowning")
      call(["sudo", "poweroff"])
    else:
      logging.info("Shutdown canceled")

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
    settingsH = 250
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

    # Check box to enable/disable CDROM redirect 
    cdromLabel = Label(settingsFrame, text = "Пробросить CDROM:", anchor = "w", width = 25)
    cdromLabel.grid(row = 8, column = 1, columnspan = 2)

    self.cdrom = IntVar()
    cdromCheckbutton = Checkbutton(settingsFrame, variable = self.cdrom)
    cdromCheckbutton.grid(row = 8, column = 3)
    if self.conf.get("cdrom"):
      if int(self.conf.get("cdrom")) == 1:
        cdromCheckbutton.select()

    # Check box to enable/disable sound forwarding
    soundLabel = Label(settingsFrame, text = "Перенаправлять звук:", anchor = "w", width = 25)
    soundLabel.grid(row = 9, column = 1, columnspan = 2)

    self.sound = IntVar()
    soundCheckbutton = Checkbutton(settingsFrame, variable = self.sound)
    soundCheckbutton.grid(row = 9, column = 3)
    if self.conf.get("sound"):
      if int(self.conf.get("sound")) == 1:
        soundCheckbutton.select()

    # show screen resolution at settings screen
    screenResLabel = Label(settingsFrame, text = "Разрешение экрана:", anchor = "w", width = 25)
    screenResLabel.grid(row = 10, column = 1, columnspan = 2)

    screenResEntry = Entry(settingsFrame, width = 10)
    screenResEntry.grid(row = 10, column = 3, columnspan = 1)
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
    self.conf["cdrom"] = self.cdrom.get()
    self.conf["sound"] = self.sound.get()
    config.put(self.conf)
    config.write()
    self.window.destroy()
    #self.parent.deiconify()

##############################################################################
# insert few more path to libraries
sys.path.insert(1,"./lib")
sys.path.insert(2,"/usr/lib/yatc")

# parse command line arguments
if len(sys.argv) > 1:
  if sys.argv[1] == '-v':
    print(__version__)
    exit(0)
  elif sys.argv[1] == 'freerdp':
    rdpBackend = sys.argv[1]
  elif sys.argv[1] == '2xclient':
    rdpBackend = sys.argv[1]
  else:
    print("\tUnknown argument: %s" % sys.argv[1])
    exit(2)
else:
  print("\tYou must specify RDP backend [freerdp|2xclient].")
  exit(2)

# change directory to script home
chdirToHome()

# write version
writeVersion(versionFile)

# create log
createLog()
logging.info("Starting YATC (%s)." % __version__)

# read configuration
config = Config()
config.read()

# start application
app = App(rdpBackend, config)

exit(0)
