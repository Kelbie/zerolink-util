# Zerolink Utility

I'm still wrapping my head around the protocol and API so this may not be entirely correct but its not giving any errors so ¯\\\_(ツ)\_/¯

## Setup

Currently I am doing most of the setup work by hand and using the Bitcoin Core RPC.

Get some Bitcoins sent to a testnet address, I don't know of any that support bech32 so you will need to send it to another address format then send it to a bech32 yourself.

```
getnewaddress "" "bech32"
```

Use `listunspent` to find UTXOs and only pick one that has a bech32 address.

```
createrawtransaction "[{\"txid\":\"16bcb1754380b532646d12fe4d8ad644cfc6ea1d6b7fae06d6c1fa997e00c559\",\"vout\":0}]" "{\"tb1q6sjxkuc4khuqs0z9m5jsa7xan357ldhln6perd\":0.01}"
```

copy the hex output and run `decoderawtransaction`:

```
decoderawtransaction 020000000159c5007e99fac1d606ae7f6b1deac6cf44d68a4dfe126d6432b5804375b1bc160000000000ffffffff0140420f0000000000160014d4246b7315b5f8083c45dd250ef8dd9c69efb6ff00000000
```

We will be using the scriptPubKey.hex later

Now we need to generate our proof so copy the address associated with the UTXO you used.

```
dumpprivkey tb1q6sjxkuc4khuqs0z9m5jsa7xan357ldhln6perd
```

Use this output as the first argument in `signmessagewithprivkey`

```
signmessagewithprivkey "cNqgAh5Gu9AyqQ7bAe2NaC1pdL1xG1PbQi8wapcCN8JetTTH9Bi4" "0014d4246b7315b5f8083c45dd250ef8dd9c69efb6ff"
```

This output is now our proof: `IMOOxctik90fuXLlhge5OTDkQVXzZmwYfyXzZTv9ZUBAaPWYIRG2NBvY8V/T5EWHlMtGZLl8ddYcSzQoWoLYCFI=`

## Usage

```
blindedOutputScriptHex = "0014d4246b7315b5f8083c45dd250ef8dd9c69efb6ff"
changeOutputAddress = "tb1q6sjxkuc4khuqs0z9m5jsa7xan357ldhln6perd"

zl = ZeroLink(blindedOutputScriptHex, changeOutputAddress)


txid = "16bcb1754380b532646d12fe4d8ad644cfc6ea1d6b7fae06d6c1fa997e00c559"
vout = 0
proof = "IMOOxctik90fuXLlhge5OTDkQVXzZmwYfyXzZTv9ZUBAaPWYIRG2NBvY8V/T5EWHlMtGZLl8ddYcSzQoWoLYCFI="

zl.addInput(txid, vout, proof)


status = zl.postInputs()


zl.postConfirmation(loop=True)
```
