from dataclasses import dataclass
from typing import Iterable


@dataclass(slots=True)
class SafetyPolicy:
    blocked_terms: tuple[str, ...] = ('self-harm', 'malware', 'credential theft')

    def check(self, text: str) -> str | None:
        lowered = text.lower()
        for term in self.blocked_terms:
            if term in lowered:
                return f'Request blocked by values core due to restricted topic: {term}.'
        return None

    def summarize(self) -> Iterable[str]:
        return self.blocked_terms
