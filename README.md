# Zerolink Utility

## Usage

```
blindedOutputScriptHex = "a9149607fb23d4a868594458d384fa4561b48ecf833c87"
changeOutputAddress = "tb1qzz3ng29fup5rf47v0ls79xl34rtpyvdpwn8c8j"

zl = ZeroLink(blindedOutputScriptHex, changeOutputAddress)
```
```
txid = "0104b1e3a56cb06c6ec90941e54ef7ebbea5a1a66fa15c0c04ec08694f239e47"
vout = 0
proof = "H0XYY38Y4bKM1DWUW9MNifH+LL/VNDGaHHmz1o5HjPmlG+kChF2EpfPRiHUTC98yJ4SoOXqEjCE4kL+ErXVRcyw="

zl.addInput(txid, vout, proof)
```
```
status = zl.postInputs()
```
```
zl.postConfirmation(loop=True)
```
