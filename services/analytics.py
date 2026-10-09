from collections import defaultdict

from models.statistics import Statistics



class AnalyticsService:


    def get_top_files(
        self,
        statistics: Statistics,
        limit: int = 10
    ):
        """
        Return biggest files by line count.
        """

        files = sorted(
            statistics.files,
            key=lambda item: item.lines,
            reverse=True
        )

        return files[:limit]



    def get_folder_statistics(
        self,
        statistics: Statistics
    ):
        """
        Group files by folder.
        """

        folders = defaultdict(
            lambda: {
                "files": 0,
                "lines": 0,
                "non_empty_lines": 0
            }
        )


        for file in statistics.files:

            folder = file.folder


            folders[folder]["files"] += 1

            folders[folder]["lines"] += (
                file.lines
            )

            folders[folder]["non_empty_lines"] += (
                file.non_empty_lines
            )


        return folders



    def get_line_distribution(
        self,
        statistics: Statistics
    ):
        """
        Categorize files by size.
        """

        distribution = {
            "0-100": 0,
            "100-300": 0,
            "300-500": 0,
            "500-1000": 0,
            "1000+": 0,
        }


        for file in statistics.files:

            lines = file.lines


            if lines <= 100:
                distribution["0-100"] += 1

            elif lines <= 300:
                distribution["100-300"] += 1

            elif lines <= 500:
                distribution["300-500"] += 1

            elif lines <= 1000:
                distribution["500-1000"] += 1

            else:
                distribution["1000+"] += 1


        return distribution



    def get_code_ratio(
        self,
        statistics: Statistics
    ):
        """
        Calculate code versus empty line ratio.
        """

        total = statistics.total_lines


        if total == 0:
            return {
                "code": 0,
                "empty": 0
            }


        return {
            "code":
                statistics.total_non_empty_lines,

            "empty":
                statistics.total_empty_lines
        }


    def get_language_statistics(
        self,
        statistics: Statistics
    ):
        """
        Group files by language.
        """

        languages = defaultdict(
            lambda: {
                "files": 0,
                "lines": 0,
                "non_empty_lines": 0
            }
        )


        for file in statistics.files:

            language = file.language


            languages[language]["files"] += 1

            languages[language]["lines"] += (
                file.lines
            )

            languages[language]["non_empty_lines"] += (
                file.non_empty_lines
            )


        return languages
