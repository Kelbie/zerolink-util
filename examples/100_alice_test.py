import sys
sys.path.append('..')

import time
from zerolink import client

states = client.ZeroLink().getStates()

anonimitySet = states[0]["requiredPeerCount"]

for i in range(anonimitySet):
    zl = client.ZeroLink()

    zl.postInputs()

    zl.postConfirmation(loop=True)

    time.sleep(3)
