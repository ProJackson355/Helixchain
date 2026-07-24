from mnemonic import Mnemonic
import hashlib


mnemo = Mnemonic("english")


def generate_phrase():

    return mnemo.generate(
        strength=128
    )


def phrase_to_private_key(phrase):

    seed = mnemo.to_seed(
        phrase,
        passphrase=""
    )


    private_key_bytes = hashlib.sha256(
        seed
    ).digest()


    return private_key_bytes