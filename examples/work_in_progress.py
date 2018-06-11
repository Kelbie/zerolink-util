import sys
sys.path.append('..')

from zerolink import client

zl = client.ZeroLink()

status = zl.postInputs()

zl.postConfirmation(loop=True)




