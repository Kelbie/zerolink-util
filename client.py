import requests
import json
import time
import ast

class ZeroLink:
    def __init__(self, inputs):
        self.session = requests.session()
        self.session.proxies = {
            'http':  'socks5h://localhost:9050',
            'https': 'socks5h://localhost:9050'
        }

        self.inputs = inputs

        self.states = None
        self.reference = None

    def getStates(self):
        response = self.session.get('http://wtgjmaol3io5ijii.onion/api/v1/btc/ChaumianCoinJoin/states')
        response = json.dumps(json.loads(response.text), sort_keys=True, indent=4)
        self.states = ast.literal_eval(response)
        return self.states

    def postInputs(self):
        response = self.session.post('http://wtgjmaol3io5ijii.onion/api/v1/btc/ChaumianCoinJoin/inputs', json=self.inputs)
        response = json.dumps(json.loads(response.text), sort_keys=True, indent=4)
        self.reference = ast.literal_eval(response)
        print("{}-{}-{} {}:{}:{} - Post Input(s)".format(*list(time.gmtime())[0:6]))
        return self.reference

    def postConfirmation(self, loop=False):
        while True:
            response = self.session.post('http://wtgjmaol3io5ijii.onion/api/v1/btc/ChaumianCoinJoin/confirmation?uniqueId={}&roundId={}'.format(self.reference["uniqueId"], self.reference["roundId"]))
            print("{}-{}-{} {}:{}:{} - Post Confirmation".format(*list(time.gmtime())[0:6]))

            if loop:
                time.sleep(55)
            else:
                break

