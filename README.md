# Zerolink Utility

I'm still wrapping my head around the protocol and API so this may not be entirely correct but its not giving any errors so ¯\\\_(ツ)\_/¯

## Setup

1) Make sure you have Bitcoin Core running.

2) Make sure you have a native segwit output in Bitcoin Core.

## Usage

```
from zerolink import client

zl = client.ZeroLink()

zl.postInputs()

zl.postConfirmation(loop=True)
```
