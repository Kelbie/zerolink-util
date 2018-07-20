import sys
sys.path.append('..')

import ast
import requests

def bitcoinRPC(method, params=[]):
    headers = {
        'content-type': 'text/plain;',
    }

    data = '{"jsonrpc": "1.0", "id":"curltest", "method": "' + method + '", "params": ' + str(params).replace("'", '"') + '}'
    response = requests.post('http://lol:lol@localhost:18332/', headers=headers, data=data)

    return ast.literal_eval(response.text.replace("true", "True").replace("false", "False").replace("null", "None"))["result"]

def toSatoshi(amount):
    return int(amount * 100000000)

def toBitcoin(amount):
    return float(amount / 100000000)

txs = bitcoinRPC("listunspent")

total_amount_input = 0
inputs = []
print(len(txs))
for i in range(len(txs)):
    total_amount_input += txs[i]["amount"]
    inputs.append({"txid": txs[i]["txid"], "vout": txs[i]["vout"]})

outputs = {}
for i in range(int(total_amount_input / 0.15) - 1):
    outputs[bitcoinRPC("getnewaddress", params=["", "bech32"])] = 0.15

outputs["2N8hwP1WmJrFF5QWABn38y63uYLhnJYJYTF"] = toBitcoin(toSatoshi(total_amount_input) - (toSatoshi(0.15) * (int(total_amount_input / 0.15) - 1)) - toSatoshi(0.05))

tx = [inputs, outputs]
tx_hex = bitcoinRPC("createrawtransaction", params=tx)
signed_tx = bitcoinRPC("signrawtransaction", params=[tx_hex])
print(bitcoinRPC("sendrawtransaction", params=[signed_tx["hex"]]))
