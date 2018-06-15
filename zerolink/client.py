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
            if {"txid": utxo["txid"], "vout": utxo["vout"]} not in lines and utxo["address"][0] == "t" and float(utxo["amount"]) > 0.1:
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

        log("Get States", response)

        if response.status_code == 200:
            # List of CcjRunningRoundStatus (Phase, Denomination, RegisteredPeerCount, RequiredPeerCount, MaximumInputCountPerPeer, FeePerInputs, FeePerOutputs, CoordinatorFeePercent)
            self.states = json.loads(response.text)
            return self.states
        else:
            raise("Unexpected status code.")

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

        log("Post Input(s)", response)

        if response.status_code == 200:
            # BlindedOutputSignature, UniqueId, RoundId
            self.reference = json.loads(response.text)
            return self.reference
        elif response.status_code == 400:
            # If request is invalid.
            raise(response.text)
        elif response.status_code == 503:
            # If the round status changed while fulfilling the request.
            raise(response.text)
        else:
            raise("Unexpected status code.")

    @threaded
    def postConfirmation(self, loop=False):
        while True:
            response = self.session.post(
                self.url + "confirmation?uniqueId={}&roundId={}".format(
                    self.reference["uniqueId"],
                    self.reference["roundId"]))

            log("Post Confirmation", response)

            if response.status_code == 200:
                # RoundHash if the phase is already ConnectionConfirmation.
                self.roundHash = json.loads(response.text)
                print(self.roundHash)
                # self.postOutput()
                # time.sleep(5)
                # self.getCoinJoin()
            elif response.status_code == 204:
                # If the phase is InputRegistration and Alice is found.
                pass
            elif response.status_code == 400:
                # The provided uniqueId or roundId was malformed.
                pass
            elif response.status_code == 404:
                # If Alice or the round is not found.
                pass
            elif response.status_code == 410:
                # Participation can be only confirmed from a Running round’s InputRegistration or ConnectionConfirmation phase.
                self.postOutput()
            else:
                raise("Unexpected status code.")

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

        if response.status_code == 200:
            # Alice or the round was not found.
            pass
        elif response.status_code == 204:
            # Alice sucessfully uncofirmed her participation.
            pass
        elif response.status_code == 400:
            # The provided uniqueId or roundId was malformed.
            pass
        elif response.status_code == 410:
            # Participation can be only unconfirmed from a Running round’s InputRegistration phase.
            pass
        else:
            raise("Unexpected status code.")

    # Not working
    def postOutput(self):
        sig = self.reference["blindedOutputSignature"]
        outputSignature = self.keys[0].unblind(int(binascii.hexlify(bytes(sig.encode('utf-8'))).decode(), 16), self.random)
        outputAddress = list(self.outputs)[0]
        signatureHex = format(outputSignature, 'x')

        response = self.session.post(
            self.url + "output?roundHash={}".format(
                self.roundHash), json={
                  "outputAddress": outputAddress,
                  "signatureHex": signatureHex
                })

        log("Post Output", response)

        if response.status_code == 204:
            # Output is successfully registered.
            pass
        elif response.status_code == 400:
            # The provided roundHash or outpurRequest was malformed.
            pass
        elif response.status_code == 404:
            # If round not found.
            pass
        elif response.status_code == 409:
            # Output registration can only be done from OutputRegistration phase.
            pass
        elif response.status_code == 410:
            # Output registration can only be done from a Running round.
            pass

        return response.text

    # Not working
    def getCoinJoin(self):
        response = self.session.get(self.url + "coinjoin?uniqueId={}&roundId={}".format(
            self.reference["uniqueId"],
            self.reference["roundId"]))

        log("Get CoinJoin", response)

        if response.status_code == 200:
            # Returns the coinjoin transaction.
            self.coinjoin = json.loads(response.text)
            return self.coinjoin
        elif response.status_code == 400:
            # The provided uniqueId or roundId was malformed.
            pass
        elif response.status_code == 404:
            # If Alice or the round is not found.
            pass
        elif response.status_code == 409:
            # CoinJoin can only be requested from Signing phase.
            pass
        elif response.status_code == 410:
            # CoinJoin can only be requested from a Running round.
            pass
