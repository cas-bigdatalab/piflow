from __future__ import annotations

from collections.abc import Iterable

from database.postgres import get_connection

from .node_repository import change_running_bindings


class ChemicalResourceTracker:
    """Persist execution-time software occupancy for Chemical nodes."""

    def reserve(self, *, bindings: Iterable[tuple[str, str]]) -> None:
        self._change(bindings=bindings, delta=1)

    def release(self, *, bindings: Iterable[tuple[str, str]]) -> None:
        self._change(bindings=bindings, delta=-1)

    @staticmethod
    def _change(
        *,
        bindings: Iterable[tuple[str, str]],
        delta: int,
    ) -> None:
        with get_connection() as connection:
            change_running_bindings(
                connection,
                bindings=bindings,
                delta=delta,
            )
