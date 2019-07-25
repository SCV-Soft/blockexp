from dataclasses import dataclass
from typing import Union, TypeVar

from ._base import Base
from ..model import Block, Transaction, EstimateFee

T = TypeVar('T')


@dataclass(init=False)
class Accessor(Base):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def get_block(self, block_id: Union[str, int]) -> Block:
        raise NotImplementedError

    async def get_transaction(self, tx_id: str) -> Transaction:
        raise NotImplementedError

    async def get_fee(self, target: int) -> EstimateFee:
        raise NotImplementedError

    async def get_local_tip(self) -> Block:
        raise NotImplementedError
