# Encryption class
#
import logging
from simplecrypt import encrypt, decrypt

class Crypt():
  def __init__(self):
    self.passpharase = "VerySecurePassphrase"
    logging.info("Encryption initialised.")

  def encryptString(self, string):
    return encrypt(self.passpharase, string)

  def decryptString(self, encryptedString):
    return decrypt(self.passpharase, encryptedString).decode('utf-8')
