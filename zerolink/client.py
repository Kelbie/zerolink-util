import requests
import json
import threading
import time
import ast
import rsa
import binascii
import base64

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from random import SystemRandom

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

def printResponse(response):
    if response.reason == "OK":
        return response.reason
    else:
        return "ERROR: " + response.text

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

        # Works with 1024 bit RSA key
        # self.pub = RSA.generate(2048).publickey()
        # Doesn't work with 2048 bit RSA key
        # self.pub = RSA.construct((19473594448380717274202325076521698699373476167359253614775896809797414915031772455344343455269320444157176520539924715307970060890094127521516100754263825112231545354422893125394219335109864514907655429499954825469485252969706079992227103439161156022844535556626007277544637236136559868400854764962522288139619969507311597914908752685925185380735570791798593290356424409633800092336087046668579610273133131498947353719917407262847070395909920415822288443947309434039008038907229064999576278651443575362470457496666718250346530518268694562965606704838796709743032825816642704620776596590683042135764246115456630753521, 65537))

        self.pub = RSA.construct((1947359444838071727420232507652169869937347616735925361477589434039008038907229064999576278651443575362470457496666718250346530518268694562965606704838796709743032825816642704620776596590683042135764246115456630753521, 65537))

        self.random = SystemRandom().randrange(self.pub.n >> 10, self.pub.n)

        self.inputs = []
        self.outputs = {}

    def getStates(self):
        response = self.session.get(self.url + "states")

        log("Get States", response)

        if response.status_code == 200:
            # List of CcjRunningRoundStatus (Phase, Denomination, RegisteredPeerCount, RequiredPeerCount, MaximumInputCountPerPeer, FeePerInputs, FeePerOutputs, CoordinatorFeePercent)
            self.states = json.loads(response.text)
            return self.states
        else:
            raise("Unexpected status code.")

    def addInput(self, txid, vout, privkey):
        self.inputs.append({"txid": txid, "vout": vout, "privkey": privkey})

    def addOutput(self, address, amount):
        if amount != 0.1:
            self.changeOutputAddress = address
        self.outputs[address] = amount

    def createTransaction(self):
        tx = [[{"txid": self.inputs[0]["txid"], "vout": self.inputs[0]["vout"]}], self.outputs]
        tx_hex = bitcoinRPC("createrawtransaction", params=tx)
        raw_tx = bitcoinRPC("decoderawtransaction", params=[tx_hex])
        import codecs
        self.outputScriptHex = raw_tx["vout"][1]["scriptPubKey"]["asm"]
        self.blindedOutputScriptHex = self.pub.blind(bytes(self.outputScriptHex, "utf-8"), self.random).hex()

        print(len(bytes.fromhex(self.blindedOutputScriptHex)))
        self.proof = bitcoinRPC("signmessagewithprivkey", params=[self.inputs[0]["privkey"], self.blindedOutputScriptHex])

    def start(self):
        self.createTransaction()
        self.postInputs()
        self.postConfirmation(loop=True)

    def postInputs(self):
        data = {
            "inputs": [],
            "blindedOutputScriptHex": self.blindedOutputScriptHex,
            "changeOutputAddress": self.changeOutputAddress
        }
        for _input in self.inputs:
            data["inputs"].append({
                "input": {
                    "transactionId": _input["txid"],
                    "index": _input["vout"]
                },
                "proof": self.proof
            })

        response = self.session.post(self.url + "inputs", json=data)

        log("Post Input(s)", printResponse(response))

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
            if loop:
                time.sleep(55)
            else:
                break

            response = self.session.post(
                self.url + "confirmation?uniqueId={}&roundId={}".format(
                    self.reference["uniqueId"],
                    self.reference["roundId"]))

            log("Post Confirmation", response)

            if response.status_code == 200:
                # RoundHash if the phase is already ConnectionConfirmation.
                self.roundHash = json.loads(response.text)
                print(self.roundHash)
            elif response.status_code == 204:
                # If the phase is InputRegistration and Alice is found.
                pass
            elif response.status_code == 400:
                # The provided uniqueId or roundId was malformed.
                pass
            elif response.status_code == 404:
                # If Alice or the round is not found.
                self.postInputs() # Repost inputs
            elif response.status_code == 410:
                self.postOutput()
                return
                # Participation can be only confirmed from a Running round’s InputRegistration or ConnectionConfirmation phase.
            else:
                raise("Unexpected status code.")

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
        blindedOutputSignature = self.reference["blindedOutputSignature"]
        outputAddress = list(self.outputs)[1]
        signatureHex = self.pub.unblind(base64.b64decode(blindedOutputSignature), self.random).hex()

        response = self.session.post(
            self.url + "output?roundHash={}".format(
                self.roundHash), json={
                  "outputAddress": outputAddress,
                  "signatureHex": signatureHex
                })
        print(self.outputScriptHex)
        print(signatureHex)
        print(self.pub.verify(self.outputScriptHex, (int(signatureHex, 16),)))

        log("Post Output", response)
        print(response.text)

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
