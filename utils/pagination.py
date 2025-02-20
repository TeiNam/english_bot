# utils/pagination.py
from dataclasses import dataclass
from typing import TypeVar, Generic, List

T = TypeVar('T')


@dataclass
class PageResponse(Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int

    @property
    def total_pages(self) -> int:
        return (self.total + self.size - 1) // self.size

    @property
    def has_next(self) -> bool:
        return self.page * self.size < self.total

    @property
    def has_prev(self) -> bool:
        return self.page > 1
