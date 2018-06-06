import sys
sys.path.append('..')

from zerolink import client

blindedOutputScriptHex = "0014d4246b7315b5f8083c45dd250ef8dd9c69efb6ff"
changeOutputAddress = "tb1q6sjxkuc4khuqs0z9m5jsa7xan357ldhln6perd"

zl = client.ZeroLink(blindedOutputScriptHex, changeOutputAddress)


txid = "16bcb1754380b532646d12fe4d8ad644cfc6ea1d6b7fae06d6c1fa997e00c559"
vout = 0
proof = "IMOOxctik90fuXLlhge5OTDkQVXzZmwYfyXzZTv9ZUBAaPWYIRG2NBvY8V/T5EWHlMtGZLl8ddYcSzQoWoLYCFI="

zl.addInput(txid, vout, proof)

status = zl.postInputs()

zl.postConfirmation(loop=True)
