import csv

from models.statistics import Statistics



class CsvExporter:


    def export(
        self,
        statistics: Statistics,
        output_file: str
    ):
        """
        Export file statistics to CSV.
        """


        with open(
            output_file,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:


            writer = csv.writer(file)

            writer.writerow([
                "File",
                "Folder",
                "Extension",
                "Language",
                "Lines",
                "Non Empty Lines",
                "Empty Lines"
            ])


            for item in statistics.files:
                writer.writerow([
                    item.file_path,
                    item.folder,
                    item.extension,
                    item.language,
                    item.lines,
                    item.non_empty_lines,
                    item.empty_lines
                ])