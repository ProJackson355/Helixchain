import hashlib
import unittest

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

import node.node as node_api
from node.transaction import Transaction


class CancellationProofTests(unittest.TestCase):
    def test_cancellation_requires_the_senders_signature(self):
        key = ec.generate_private_key(ec.SECP256K1())
        public = key.public_key()
        compressed = public.public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.CompressedPoint,
        )
        sender = hashlib.sha256(compressed).hexdigest()[:40]
        tx_id = "a" * 64
        signature = Transaction.canonical_signature_hex(key.sign(
            node_api._cancellation_payload(tx_id, sender),
            ec.ECDSA(hashes.SHA256()),
        ).hex())
        pem = public.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        verified = node_api._verify_cancellation(
            tx_id, {"sender": sender, "signature": signature, "public_key": pem}
        )
        self.assertEqual(verified[:2], (tx_id, sender))

        with self.assertRaisesRegex(ValueError, "does not belong"):
            node_api._verify_cancellation(
                tx_id,
                {"sender": "b" * 40, "signature": signature, "public_key": pem},
            )


if __name__ == "__main__":
    unittest.main()
