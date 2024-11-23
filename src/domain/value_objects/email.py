import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class Email:
    value: str

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, self.value):
            raise ValueError("Invalid email format")

    def __str__(self) -> str:
        return self.value