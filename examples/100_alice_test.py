import sys
sys.path.append('..')

import time
from zerolink import client

for i in range(100):
    zl = client.ZeroLink()

    zl.postInputs()

    zl.postConfirmation(loop=True)
    
    time.sleep(3)
