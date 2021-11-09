from bip32utils import BIP32Key
from eth_keys import keys

from django.db import models

from gold_sale.settings import ROOT_KEYS


class BlockchainAccount(models.Model):

    class Network(models.TextChoices):
        ETHEREUM = 'ethereum'
        BITCOIN = 'bitcoin'

    class Status(models.TextChoices):
        AVAILABLE = 'available'
        RECEIVING = 'receiving'

    address = models.CharField(max_length=50, unique=True)
    network = models.CharField(choices=Network, null=True, default=Network.ETHEREUM)

    status = models.CharField(choices=Status, default=Status.AVAILABLE)

    def generate_keys(self):
        root_public_key = ROOT_KEYS.get('public')
        bip32_key = BIP32Key.fromExtendedKey(root_public_key, public=True)

        child_key = bip32_key.ChildKey(self.id)

        if self.network == self.Network.BITCOIN:
            self.address = child_key.Address()
        elif self.network == self.Network.ETHEREUM:
            self.address = keys.PublicKey(child_key.K.to_string()).to_checksum_address().lower()

        self.save()


