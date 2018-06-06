import requests
import json
import threading
import time

def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

def log(message, response):
    print("{:02}-{:02}-{:02} {:02}:{:02}:{:02} - {} - {}".format(
            *list(time.gmtime())[0:6],
            message,
            response
        )
    )

class ZeroLink:
    def __init__(self, blindedOutputScriptHex, changeOutputAddress):
        self.session = requests.session()
        self.session.proxies = {
            'http':  'socks5h://localhost:9050',
            'https': 'socks5h://localhost:9050'
        }
        self.url = "http://wtgjmaol3io5ijii.onion/api/v1/btc/ChaumianCoinJoin/"
        self.inputs = {
          "Inputs": [],
          "BlindedOutputScriptHex": blindedOutputScriptHex,
          "ChangeOutputAddress": changeOutputAddress
        }

        self.states = None
        self.reference = None

    def getStates(self):
        response = self.session.get(self.url + "states")
        self.states = json.loads(response.text)
        return self.states

    def addInput(self, txid, vout, proof):
        self.inputs["Inputs"].append(
            {
              "Input": {
                "TransactionId": txid,
                "Index": vout
              },
              "Proof": proof
            }
        )

    def postInputs(self):
        response = self.session.post(self.url + "inputs", json=self.inputs)
        self.reference = json.loads(response.text)
        log("Post Input(s)", response)
        return self.reference

    @threaded
    def postConfirmation(self, loop=False):
        while True:
            response = self.session.post(
                self.url + "confirmation?uniqueId={}&roundId={}".format(
                    self.reference["uniqueId"],
                    self.reference["roundId"]))
            log("Post Confirmation", response)

            if loop:
                time.sleep(55)
            else:
                break

    def postUnconfirmation(self):
        response = self.session.post(
            self.url + "unconfirmation?uniqueId={}&roundId={}".format(
                self.reference["uniqueId"],
                self.reference["roundId"]))
        log("Post Unconfirmation", response)
