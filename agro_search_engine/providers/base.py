from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import SearchPage


class SearchProvider(ABC):
    mode: str

    @abstractmethod
    async def search(self, query: str, page: int = 1) -> SearchPage:
        raise NotImplementedError
