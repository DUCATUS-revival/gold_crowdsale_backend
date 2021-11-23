"""
Contain contract ABIs in json format.

For each contract, the events of which the scanner must catch, you need to add ABI here.
"""
import json
import os


def _open_abi(name):
    with open(f"{os.getcwd()}/scanner/contracts/{name}.json") as f:
        result = json.load(f)
    return result


# token_abi = _open_abi('token_abi')
erc20_abi = _open_abi('erc20_abi')
