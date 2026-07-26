"""ERC-721-style NFT consensus: unique id + explicit owner, mint by creator,
transfer only by the current owner."""
import os

from node.blockchain import Blockchain
from node.transaction import Transaction

IMG = "https://example.com/image.png"
URI = "https://example.com/metadata.json"


def _chain(tmp_path):
    bc = Blockchain({}, database_path=os.path.join(tmp_path, "db.json"))
    bc.nft_activation_height = 0
    return bc


def _mint(creator, nonce, name="My NFT", desc="A one-of-a-kind test NFT",
          attributes=None, royalty=500):
    attributes = attributes if attributes is not None else [{"trait_type": "Color", "value": "Blue"}]
    return Transaction(
        creator, creator, 0, tx_type="nft_mint",
        nft_id=Transaction.nft_address(creator, nonce), nonce=nonce,
        name=name, description=desc, image=IMG, uri=URI,
        metadata_hash=Transaction.nft_metadata_hash(name, desc, IMG, attributes),
        attributes=attributes, royalty_bps=royalty,
    )


def test_mint_sets_creator_as_owner(tmp_path):
    bc = _chain(tmp_path)
    creator = "a" * 40
    nfts = {}
    tx = _mint(creator, "0" * 32)
    assert bc._apply_nft_transaction(tx, nfts, block_index=1) is None
    nft = nfts[tx.nft_id]
    assert nft["owner"] == creator and nft["creator"] == creator
    assert nft["royalty_bps"] == 500
    assert nft["attributes"] == [{"trait_type": "Color", "value": "Blue"}]


def test_only_owner_can_transfer(tmp_path):
    bc = _chain(tmp_path)
    creator, buyer, third = "a" * 40, "b" * 40, "c" * 40
    nfts = {}
    tx = _mint(creator, "0" * 32)
    bc._apply_nft_transaction(tx, nfts, block_index=1)

    move = Transaction(creator, buyer, 0, tx_type="nft_transfer", nft_id=tx.nft_id, nonce="1" * 32)
    assert bc._apply_nft_transaction(move, nfts, block_index=2) is None
    assert nfts[tx.nft_id]["owner"] == buyer

    # The creator no longer owns it, so cannot transfer it again.
    steal = Transaction(creator, third, 0, tx_type="nft_transfer", nft_id=tx.nft_id, nonce="2" * 32)
    assert bc._apply_nft_transaction(steal, nfts, block_index=3) == "only the current NFT owner can transfer it"
    assert nfts[tx.nft_id]["owner"] == buyer


def test_duplicate_and_forged_mints_rejected(tmp_path):
    bc = _chain(tmp_path)
    creator = "a" * 40
    nfts = {}
    tx = _mint(creator, "0" * 32)
    bc._apply_nft_transaction(tx, nfts, block_index=1)

    assert bc._apply_nft_transaction(_mint(creator, "0" * 32), nfts, block_index=2) == "NFT id already exists"

    forged = _mint(creator, "3" * 32)
    forged.nft_id = Transaction.nft_address(creator, "9" * 32)  # id doesn't match nonce
    assert bc._apply_nft_transaction(forged, {}, block_index=2) == "NFT id does not match its creator and nonce"

    tampered = _mint(creator, "4" * 32)
    tampered.metadata_hash = "0" * 64
    assert bc._apply_nft_transaction(tampered, {}, block_index=2) == "NFT metadata hash does not match its on-chain fields"


def test_transfer_of_missing_nft_rejected(tmp_path):
    bc = _chain(tmp_path)
    move = Transaction("a" * 40, "b" * 40, 0, tx_type="nft_transfer", nft_id="d" * 40, nonce="1" * 32)
    reason = bc._apply_nft_transaction(move, {}, block_index=1)
    assert reason == "NFT does not exist on the confirmed chain or earlier in this block"


def test_serialized_metadata_hash_is_deterministic(tmp_path):
    # The client and node must derive the same hash for the same fields+attributes.
    attrs = [{"trait_type": "Rarity", "value": "Legendary"}, {"trait_type": "Power", "value": "9000"}]
    a = Transaction.nft_metadata_hash("Sword", "A blade", IMG, attrs)
    b = Transaction.nft_metadata_hash("Sword", "A blade", IMG, attrs)
    assert a == b and len(a) == 64


def test_full_mint_and_transfer_through_mining(tmp_path):
    """End to end: sign an nft_mint, accept it into the mempool, mine it, and
    verify ownership; then transfer it to another wallet and re-check."""
    from wallet.wallet import Wallet
    bc = Blockchain({}, database_path=os.path.join(tmp_path, "db.json"))  # legacy difficulty 3 = fast to mine
    creator, buyer = Wallet(), Wallet()

    attrs = [{"trait_type": "Rarity", "value": "Rare"}]
    name, desc = "Genesis NFT", "The first Helix NFT"
    nid = Transaction.nft_address(creator.address, "0" * 32)
    mint = Transaction(
        creator.address, creator.address, 0, tx_type="nft_mint", nft_id=nid, nonce="0" * 32,
        name=name, description=desc, image=IMG, uri=URI,
        metadata_hash=Transaction.nft_metadata_hash(name, desc, IMG, attrs),
        attributes=attrs, royalty_bps=250,
    )
    mint.public_key = creator.public_key
    mint.sign(creator.private_key)
    assert bc.add_transaction(mint)
    assert bc.mine_pending_transactions(creator.address) is not None

    owned = bc.get_nfts_by_owner(creator.address)
    assert len(owned) == 1 and owned[0]["nft_id"] == nid
    assert bc.get_nft(nid)["royalty_bps"] == 250

    move = Transaction(creator.address, buyer.address, 0, tx_type="nft_transfer", nft_id=nid, nonce="1" * 32)
    move.public_key = creator.public_key
    move.sign(creator.private_key)
    assert bc.add_transaction(move)
    assert bc.mine_pending_transactions(creator.address) is not None

    assert bc.get_nfts_by_owner(creator.address) == []
    assert [n["nft_id"] for n in bc.get_nfts_by_owner(buyer.address)] == [nid]
