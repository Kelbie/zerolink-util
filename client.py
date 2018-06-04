import requests
import json
import threading
import time

def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

def log(message):
    print("{:02}-{:02}-{:02} {:02}:{:02}:{:02} - {}".format(
            *list(time.gmtime())[0:6],
            message
        )
    )

class ZeroLink:
    def __init__(self, inputs):
        self.session = requests.session()
        self.session.proxies = {
            'http':  'socks5h://localhost:9050',
            'https': 'socks5h://localhost:9050'
        }
        self.url = "http://wtgjmaol3io5ijii.onion/api/v1/btc/ChaumianCoinJoin/"
        self.inputs = inputs

        self.states = None
        self.reference = None

    def getStates(self):
        response = self.session.get(self.url + "states")
        self.states = json.loads(response.text)
        return self.states

    def postInputs(self):
        response = self.session.post(self.url + "inputs", json=self.inputs)
        log("Post Input(s)")
        return self.reference

    @threaded
    def postConfirmation(self, loop=False):
        while True:
            response = self.session.post(
                self.url + "confirmation?uniqueId={}&roundId={}".format(
                    self.reference["uniqueId"],
                    self.reference["roundId"]))
            log("Post Confirmation")

            if loop:
                time.sleep(55)
            else:
                break

      "BlindedOutputScriptHex": "76a9149f9a7abd600c0caa03983a77c8c3df8e062cb2fa88ac",
      "ChangeOutputAddress": "tb1qzz3ng29fup5rf47v0ls79xl34rtpyvdpwn8c8j"
    }
)

print(zl.getStates())
zl.postInputs()
zl.postConfirmation(loop=True)
