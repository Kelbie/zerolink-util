import sys
sys.path.append('..')

from zerolink import client

zl = client.ZeroLink()

zl.addInput(txid, vout, proof)

status = zl.postInputs()

zl.postConfirmation(loop=True)


zl.addInput(txid, vout, proof)

status = zl.postInputs()

zl.postConfirmation(loop=True)
