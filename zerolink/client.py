import requests
import json
import threading
import time
import ast
import rsa
import binascii

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

def bitcoinRPC(method, params=[]):
    headers = {
        'content-type': 'text/plain;',
    }

    data = '{"jsonrpc": "1.0", "id":"curltest", "method": "' + method + '", "params": ' + str(params).replace("'", '"') + '}'
    response = requests.post('http://lol:lol@localhost:18332/', headers=headers, data=data)

    return ast.literal_eval(response.text.replace("true", "True").replace("false", "False").replace("null", "None"))["result"]

class ZeroLink:
    def __init__(self):
        self.session = requests.session()
        self.session.proxies = { 'http':  'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050' }
        self.url = "http://wtgjmaol3io5ijii.onion/api/v1/btc/ChaumianCoinJoin/"
        self.reference = None
        self.inputs = {}

        self.keys = rsa.newkeys(512)

        self.random = 1234567890

        utxos = bitcoinRPC("listunspent")
        self.w = open('info.txt', "a+")
        self.r = open('info.txt', 'r')
        lines = list(map(ast.literal_eval, self.r.read().splitlines()))
        for utxo in utxos:
            if {"txid": utxo["txid"], "vout": utxo["vout"]} not in lines:
                self._input = utxo
                self.w.write(str({"txid": self._input["txid"], "vout": self._input["vout"]}) + "\n")
                break
        else:
            raise ValueError("No UTXO's available.")
        self.w.close()
        self.r.close()

        self.outputs = {
            bitcoinRPC("getnewaddress", params=["", "bech32"]): 0.1
        }
        tx = [[{"txid": self._input["txid"], "vout": self._input["vout"]}], self.outputs]
        tx_hex = bitcoinRPC("createrawtransaction", params=tx)

        outputScriptHex = bitcoinRPC("decoderawtransaction", params=[tx_hex])["vout"][0]["scriptPubKey"]["hex"]
        changeOutputAddress = bitcoinRPC("getnewaddress", params=["", "bech32"])

        blindedOutputScriptHex = str(format(self.keys[0].blind(int(outputScriptHex, 16), self.random), 'x'))
        blindedOutputScriptHex = "{0:0>128}".format(blindedOutputScriptHex)

        self.inputs["BlindedOutputScriptHex"] = blindedOutputScriptHex
        self.inputs["ChangeOutputAddress"] = changeOutputAddress

        self.txid = self._input["txid"]
        self.vout = self._input["vout"]

        input_address = self._input["address"]
        dumpprivkey = bitcoinRPC("dumpprivkey", params=[input_address])
        self.proof =  bitcoinRPC("signmessagewithprivkey", params=[dumpprivkey, blindedOutputScriptHex])

        self.inputs["Inputs"] = []
        self.addInput()


    def getStates(self):
        response = self.session.get(self.url + "states")
        self.states = json.loads(response.text)
        return self.states

    def addInput(self):
        self.inputs["Inputs"].append(
            {
              "Input": {
                "TransactionId": self.txid,
                "Index": self.vout
              },
              "Proof": self.proof
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

    # Untested
    def postOutput(self, output):
        response = self.session.post(
            self.url + "output?roundHash={}".format(
                self.reference.roundHash), json=ouput)
        log("Post Output", response)

    def getCoinJoin(self):
        response = self.session.get(self.url + "coinjoin")
        self.coinjoin = json.loads(response.text)
        return self.coinjoin
