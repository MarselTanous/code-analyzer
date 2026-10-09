from dataclasses import dataclass, field
from typing import List


from dataclasses import dataclass, field
from typing import List


@dataclass
class FileStatistic:

    file_path: str

    folder: str

    extension: str

    language: str

    lines: int

    non_empty_lines: int


    @property
    def empty_lines(self) -> int:
        return (
            self.lines -
            self.non_empty_lines
        )

@dataclass
class Statistics:
    total_files: int = 0
    total_lines: int = 0
    total_non_empty_lines: int = 0

    files: List[FileStatistic] = field(
        default_factory=list
    )


    @property
    def total_empty_lines(self) -> int:
        return (
            self.total_lines -
            self.total_non_empty_lines
        )