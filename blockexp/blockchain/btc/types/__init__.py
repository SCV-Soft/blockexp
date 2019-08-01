from dataclasses import dataclass, field
from typing import List, Union, Optional


@dataclass
class BtcVInCoinbase:
    coinbase: str
    sequence: int


@dataclass
class BtcScriptSig:
    asm: str
    hex: str


@dataclass
class BtcVIn:
    txid: str
    vout: int
    scriptSig: BtcScriptSig
    sequence: int
    txinwitness: List[str] = None


@dataclass
class BtcScriptPubKey:
    type: str
    asm: str
    hex: str
    reqSigs: int = None
    addresses: List[str] = None


@dataclass
class BtcVOut:
    value: float
    n: int
    scriptPubKey: Union[dict, BtcScriptPubKey]

    def __post_init__(self):
        if not isinstance(self.scriptPubKey, BtcScriptPubKey):
            self.scriptPubKey = BtcScriptPubKey(**self.scriptPubKey)


@dataclass
class BtcTransaction:
    txid: str
    hash: str
    version: int
    size: int
    vsize: int
    weight: int
    locktime: int
    vin: List[Union[dict, BtcVIn, BtcVInCoinbase]]
    vout: List[Union[dict, BtcVOut]]
    hex: str
    blockhash: str = None
    confirmations: int = None
    time: int = None
    blocktime: int = None
    address: str = None
    addresses: List[str] = field(default_factory=list)
    wallets: List[str] = field(default_factory=list)

    def is_coinbase(self) -> bool:
        return isinstance(self.vin[0], BtcVInCoinbase) if self.vin else False

    def __post_init__(self):
        if self.vin and not isinstance(self.vin[0], (BtcVIn, BtcVInCoinbase)):
            item = self.vin[0]
            if 'coinbase' in item:
                assert len(self.vin) == 1
                self.vin = [BtcVInCoinbase(**item) for item in self.vin]
            else:
                self.vin = [BtcVIn(**item) for item in self.vin]

        if self.vout and not isinstance(self.vout[0], BtcVOut):
            self.vout = [BtcVOut(**item) for item in self.vout]

    @classmethod
    def load(cls, raw_tx: dict):
        cls.fix_tx(raw_tx)
        return cls(**raw_tx)

    @classmethod
    def fix_tx(cls, raw_tx):
        pass


@dataclass
class BtcBlock:
    TRANSACTION_CLASS = BtcTransaction

    hash: str  # (string) the block hash (same as provided)
    confirmations: int  # (numeric) The number of confirmations, or -1 if the block is not on the main chain
    size: int  # (numeric) The block size
    strippedsize: int  # (numeric) The block size excluding witness data
    weight: int  # (numeric) The block weight as defined in BIP 141
    height: int  # (numeric) The block height or index
    version: int  # (numeric) The block version
    versionHex: str  # (string) The block version formatted in hexadecimal
    merkleroot: str  # (string) The merkle root
    tx: List[Union[str, dict, BtcTransaction]]  # (array of string) The transaction ids
    time: int  # (numeric) The block time in seconds since epoch (Jan 1 1970 GMT)
    mediantime: int  # (numeric) The median block time in seconds since epoch (Jan 1 1970 GMT)
    nonce: int  # (numeric) The nonce
    bits: str  # (string) The bits
    difficulty: float  # (numeric) The difficulty
    chainwork: str  # (string) Expected number of hashes required to produce the chain up to this block (in hex)
    nTx: int  # (numeric) The number of transactions in the block.
    previousblockhash: str = None  # (string) The hash of the previous block
    nextblockhash: Optional[str] = None  # (string) The hash of the next block

    def __post_init__(self):
        if self.tx and isinstance(self.tx[0], dict):
            self.tx = [self.parse_tx(item) for item in self.tx]

    @classmethod
    def parse_tx(cls, raw_tx):
        return cls.TRANSACTION_CLASS.load(raw_tx)

    @classmethod
    def load(cls, raw_block: dict):
        cls.fix_block(raw_block)
        return cls(**raw_block)

    @classmethod
    def fix_block(cls, raw_block):
        pass
