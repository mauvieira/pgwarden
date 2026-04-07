from dataclasses import dataclass


@dataclass
class SyncResult:
    inserted: int = 0
    updated: int = 0
    deleted: int = 0

    def __str__(self) -> str:
        return f"inserted={self.inserted} updated={self.updated} deleted={self.deleted}"