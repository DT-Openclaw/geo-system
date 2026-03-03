from dataclasses import dataclass, asdict
from typing import List


@dataclass
class Prompt:
    id: str
    prompt: str
    bucket: str
    intent_type: str
    stage: str
    priority: str
    owner_page: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class ScanResult:
    scan_id: str
    model: str
    prompt_id: str
    mentioned: bool
    cited: bool
    recommended: bool
    position: int
    sentiment: str
    competitors: List[str]
    excerpt: str
    ts: str
    run_id: str = ""

    def to_dict(self):
        return asdict(self)
