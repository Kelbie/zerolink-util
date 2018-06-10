import sys
sys.path.append('..')

import ast
import rsa
import binascii
import requests
from zerolink import client

def bitcoinRPC(method, params=[]):
    headers = {
        'content-type': 'text/plain;',
    }

    data = '{"jsonrpc": "1.0", "id":"curltest", "method": "' + method + '", "params": ' + str(params).replace("'", '"') + '}'
    response = requests.post('http://lol:lol@localhost:18332/', headers=headers, data=data)

    return response.text.replace("true", "True").replace("false", "False").replace("null", "None")

keys = (rsa.key.PublicKey(92091189085804565643648259020907050963541685219663339896747641013482093929493276068564912886312959910871152158592445460101555914656566401819447692525519556854214682541229604537189606147159043635273741817303568419145782968789006476387432598586464388509784883331797242321035425684507310396413791118662080133161, 65537), rsa.key.PrivateKey(92091189085804565643648259020907050963541685219663339896747641013482093929493276068564912886312959910871152158592445460101555914656566401819447692525519556854214682541229604537189606147159043635273741817303568419145782968789006476387432598586464388509784883331797242321035425684507310396413791118662080133161, 65537, 58406247987418813357008100556998360823650916980565279503308294531720756735575141062146582909190200630107564268610021751821431734633873727690088682134689556767302961944057501470934924787147854631072077941635348689088509074025899737373159409528388129286237426077934882039092481839038171288595893466510328564853, 33171227496662737855106561317600774174404630045384918809725512219610698919493310713461547776299609867572161369631865378951851309812843296138660575975520727473177419, 2776236999220773373140933690925524647668335175416487435611062669507364021793448821697160826121360088003829619658738359141620579567790532047033819))

r = 1234567890

# Setup
unspent = ast.literal_eval(bitcoinRPC("listunspent"))["result"]
_input = unspent[0]
outputs = {
    ast.literal_eval(bitcoinRPC("getnewaddress", params=["", "bech32"]))["result"]: 0.1
    }
tx_template = [[{"txid": _input["txid"], "vout": _input["vout"]}], outputs]
tx_hex = ast.literal_eval(bitcoinRPC("createrawtransaction", params=tx_template))["result"]

outputScriptHex = ast.literal_eval(bitcoinRPC("decoderawtransaction", params=[tx_hex]))["result"]["vout"][0]["scriptPubKey"]["hex"]
changeOutputAddress = ast.literal_eval(bitcoinRPC("getnewaddress", params=["", "bech32"]))["result"]

blindedOutputScriptHex = keys[0].blind(int(outputScriptHex, 16), r)
blindedOutputScriptHex = str(format(blindedOutputScriptHex, 'x'))

zl = client.ZeroLink(blindedOutputScriptHex, changeOutputAddress)

txid = _input["txid"]
vout = _input["vout"]

# Proof
input_address = _input["address"]
dumpprivkey = ast.literal_eval(bitcoinRPC("dumpprivkey", params=[_input["address"]]))["result"]
proof =  ast.literal_eval(bitcoinRPC("signmessagewithprivkey", params=[dumpprivkey, blindedOutputScriptHex]))["result"]

zl.addInput(txid, vout, proof)

status = zl.postInputs()

zl.postConfirmation(loop=True)
