from .eth import EthMaker
from .btc import BTCMaker

scanner_makers = {
    'EthMaker': EthMaker,
    'BTCMaker': BTCMaker,
}
