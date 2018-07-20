from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from random import SystemRandom

class RSAKey:
    def __init__(self):
        pass

    def generate(self):
        self.key = RSA.generate(2048)

    def construct(self):
        pass

    def blind(self):
        pass

    def sign(self):
        pass

    def verify(self):
        pass

key = RSAKey().generate()
