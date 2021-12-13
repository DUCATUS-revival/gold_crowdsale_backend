from bip32utils import BIP32Key
from eth_keys import keys


from django.db import models

from gold_crowdsale.settings import ROOT_KEYS


class TokenPurchase(models.Model):

    user_address = models.CharField(max_length=100)
    eth_address = models.CharField(max_length=50, unique=True)
    btc_address = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_keys(self):
        root_public_key = ROOT_KEYS.get('public')
        bip32_key = BIP32Key.fromExtendedKey(root_public_key, public=True)

        child_key = bip32_key.ChildKey(self.id)

        self.btc_address = child_key.Address()
        self.eth_address = keys.PublicKey(child_key.K.to_string()).to_checksum_address().lower()

        self.save()



