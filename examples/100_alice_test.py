import sys
sys.path.append('..')

import requests
import json
import threading
import time
import ast
import rsa
import binascii
from zerolink import client

def bitcoinRPC(method, params=[]):
    headers = {
        'content-type': 'text/plain;',
    }

    data = '{"jsonrpc": "1.0", "id":"curltest", "method": "' + method + '", "params": ' + str(params).replace("'", '"') + '}'
    response = requests.post('http://lol:lol@localhost:18332/', headers=headers, data=data)

    return ast.literal_eval(response.text.replace("true", "True").replace("false", "False").replace("null", "None"))["result"]

utxos = bitcoinRPC("listunspent")

for i in range(100):
    utxo = utxos[i]

    zl = client.ZeroLink()

    # Gets the requirements for the current round.
    # states = zl.getStates()

    # Add Inputs.
    privkey = bitcoinRPC("dumpprivkey", params=[utxo["address"]])
    zl.addInput(utxo["txid"], utxo["vout"], privkey)

    # Add Outputs.
    zl.addOutput(bitcoinRPC("getnewaddress", params=["", "bech32"]), 0.1)
    zl.addOutput(bitcoinRPC("getnewaddress", params=["", "bech32"]), 0.05) # change

    zl.start()
    time.sleep(2)
