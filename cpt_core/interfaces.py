"""Small integration contracts for an independently implemented orchestration layer."""
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class EvidenceReference:
    source_id: str
    page: int
    start: int
    end: int


@dataclass(frozen=True)
class EngineeringRequest:
    question: str
    measurement_file: str
    reference_file: str | None = None


class EvidenceRetriever(Protocol):
    def search_literature(self, question: str) -> Sequence[EvidenceReference]: ...

    def search_standards(self, question: str) -> Sequence[EvidenceReference]: ...
