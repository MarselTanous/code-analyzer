from pathlib import Path

from models.statistics import (
    Statistics,
    FileStatistic
)


class Analyzer:

    EXCLUDED_DIRS = {
        "node_modules",
        ".git",
        "dist",
        "coverage",
        ".angular",
        ".idea",
        "venv",
    }

    SUPPORTED_LANGUAGES = {
        ".ts": "TypeScript",
        ".tcl": "Tcl",
        ".c": "C",
        ".py": "Python",
        ".java": "Java",

    }


    def analyze(
        self,
        path: str
    ) -> Statistics:
        """
        Analyze all supported source files
        inside the selected directory.
        """

        root = Path(path)

        total_files = 0
        total_lines = 0
        total_non_empty_lines = 0

        file_statistics = []


        for file_path in root.rglob("*"):

            if not self.is_supported_file(
                file_path
            ):
                continue


            try:

                statistic = self.analyze_file(
                    file_path,
                    root
                )


                file_statistics.append(
                    statistic
                )


                total_files += 1

                total_lines += (
                    statistic.lines
                )

                total_non_empty_lines += (
                    statistic.non_empty_lines
                )


            except Exception as ex:

                print(
                    f"Could not analyze {file_path}: {ex}"
                )


        return Statistics(

            total_files=total_files,

            total_lines=total_lines,

            total_non_empty_lines=
            total_non_empty_lines,

            files=file_statistics
        )



    def is_supported_file(
        self,
        file_path: Path
    ) -> bool:
        """
        Check whether the path is a supported source file.
        """

        if not file_path.is_file():
            return False


        if any(
            folder in self.EXCLUDED_DIRS
            for folder in file_path.parts
        ):
            return False


        return (
            file_path.suffix.lower()
            in self.SUPPORTED_LANGUAGES
        )



    def analyze_file(
        self,
        file_path: Path,
        root: Path
    ) -> FileStatistic:
        """
        Analyze one source file.
        """

        with file_path.open(
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            lines = file.readlines()


        line_count = len(lines)


        non_empty_count = sum(
            1
            for line in lines
            if line.strip()
        )


        relative_path = (
            file_path.relative_to(root)
        )

        extension = (
            file_path.suffix.lower()
        )

        language = (
            self.SUPPORTED_LANGUAGES[
                extension
            ]
        )

        return FileStatistic(

            file_path=str(relative_path),

            folder=str(relative_path.parent),

            extension=extension,

            language=language,

            lines=line_count,

            non_empty_lines=non_empty_count
        )