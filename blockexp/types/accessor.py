from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union, TypeVar

from ._base import Base
from .connectable import Connectable
from ..model import Block, Transaction, EstimateFee

T = TypeVar('T')


@dataclass(init=False)
class Accessor(Connectable, Base, ABC):
    @abstractmethod
    async def get_block(self, block_id: Union[str, int]) -> Block:
        raise NotImplementedError

    @abstractmethod
    async def get_transaction(self, tx_id: str) -> Transaction:
        raise NotImplementedError

    @abstractmethod
    async def get_fee(self, target: int) -> EstimateFee:
        raise NotImplementedError

    @abstractmethod
    async def get_local_tip(self) -> Block:
        raise NotImplementedError
