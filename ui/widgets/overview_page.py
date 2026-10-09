from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from models.statistics import Statistics
from services.analytics import AnalyticsService
from ui.theme import Theme
from ui.widgets.charts_widget import create_bar_card, create_donut_card
from ui.widgets.summary_card import SummaryCard


def short_name(path: str, limit: int = 32) -> str:
    """
    File name only, shortened for axis labels.
    """

    name = path.replace("\\", "/").split("/")[-1]

    if len(name) > limit:
        name = name[:limit - 1] + "…"

    return name


def folder_name(folder: str) -> str:
    return "(project root)" if folder in ("", ".") else folder


def elide_left(text: str, limit: int = 28) -> str:
    """
    Keep the end of a path, which is the most specific part.
    """

    return text if len(text) <= limit else "…" + text[-(limit - 1):]


class OverviewPage(QScrollArea):
    """
    Dashboard: KPI row followed by a grid of chart cards.
    """

    def __init__(self):
        super().__init__()

        self.analytics = AnalyticsService()

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setObjectName("ScrollContent")
        self.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 8)
        layout.setSpacing(16)

        # KPI row

        self.files_card = SummaryCard("Source files")
        self.lines_card = SummaryCard("Total lines")
        self.code_card = SummaryCard("Code lines")
        self.empty_card = SummaryCard("Blank lines")
        self.average_card = SummaryCard("Avg. file size")
        self.largest_card = SummaryCard("Largest file")

        kpis = QGridLayout()
        kpis.setSpacing(16)

        for column, card in enumerate([
            self.files_card,
            self.lines_card,
            self.code_card,
            self.empty_card,
            self.average_card,
            self.largest_card,
        ]):
            kpis.addWidget(card, 0, column)
            kpis.setColumnStretch(column, 1)

        layout.addLayout(kpis)

        # Charts grid, rebuilt on every update

        self.charts = QGridLayout()
        self.charts.setSpacing(16)
        for column in range(3):
            self.charts.setColumnStretch(column, 1)

        layout.addLayout(self.charts)
        layout.addStretch()

    def clear_charts(self):
        while self.charts.count():
            widget = self.charts.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    def set_data(self, result: Statistics, theme: Theme):
        """
        Fill KPI tiles and rebuild all charts for the given result.
        """

        self.update_kpis(result)
        self.clear_charts()

        if not result.files:
            return

        self.charts.addWidget(self.composition_card(result, theme), 0, 0)
        self.charts.addWidget(self.top_files_card(result, theme), 0, 1, 1, 2)
        self.charts.addWidget(self.distribution_card(result, theme), 1, 0)
        self.charts.addWidget(self.languages_card(result, theme), 1, 1)
        self.charts.addWidget(self.folders_card(result, theme), 1, 2)

    def update_kpis(self, result: Statistics):
        total = result.total_lines or 1

        self.files_card.set_value(
            result.total_files,
            f"{len({f.folder for f in result.files}):,} folders"
        )

        self.lines_card.set_value(
            result.total_lines,
            "across all source files"
        )

        self.code_card.set_value(
            result.total_non_empty_lines,
            f"{result.total_non_empty_lines / total:.1%} of all lines"
        )

        self.empty_card.set_value(
            result.total_empty_lines,
            f"{result.total_empty_lines / total:.1%} of all lines"
        )

        if result.files:
            average = round(result.total_lines / result.total_files)
            median = sorted(f.lines for f in result.files)[len(result.files) // 2]
            largest = max(result.files, key=lambda f: f.lines)

            self.average_card.set_value(
                f"{average:,}",
                f"lines · median {median:,}"
            )
            self.largest_card.set_value(
                largest.lines,
                short_name(largest.file_path, 26)
            )
            self.largest_card.setToolTip(largest.file_path)
        else:
            self.average_card.set_value("—", "no files found")
            self.largest_card.set_value("—", "no files found")

    # Chart cards

    def composition_card(self, result: Statistics, theme: Theme):
        ratio = self.analytics.get_code_ratio(result)
        total = (ratio["code"] + ratio["empty"]) or 1

        return create_donut_card(
            "Line composition",
            "Code versus blank lines",
            [
                ("Code", ratio["code"], theme.series[0]),
                ("Blank", ratio["empty"], theme.neutral_mark),
            ],
            theme,
            f"{ratio['code'] / total:.0%}",
            "code density",
        )

    def top_files_card(self, result: Statistics, theme: Theme):
        files = self.analytics.get_top_files(result, 10)

        return create_bar_card(
            "Largest files",
            f"Top {len(files)} files by total line count",
            [short_name(f.file_path) for f in files],
            [f.lines for f in files],
            [
                f"<b>{f.file_path}</b><br>"
                f"{f.lines:,} lines · {f.non_empty_lines:,} code · "
                f"{f.empty_lines:,} blank"
                for f in files
            ],
            theme,
        )

    def distribution_card(self, result: Statistics, theme: Theme):
        distribution = self.analytics.get_line_distribution(result)
        total = result.total_files or 1

        return create_bar_card(
            "File size distribution",
            "Number of files per line-count bucket",
            list(distribution.keys()),
            list(distribution.values()),
            [
                f"<b>{bucket} lines</b><br>{count:,} files ({count / total:.1%})"
                for bucket, count in distribution.items()
            ],
            theme,
            horizontal=False,
            value_title="Files",
        )

    def languages_card(self, result: Statistics, theme: Theme):
        languages = sorted(
            self.analytics.get_language_statistics(result).items(),
            key=lambda item: item[1]["lines"],
            reverse=True
        )

        # Fixed slot order; anything past the palette folds into "Other".
        slots = len(theme.series) - 1
        items = [
            (name, data["lines"], theme.series[index])
            for index, (name, data) in enumerate(languages[:slots])
        ]

        rest = sum(data["lines"] for _, data in languages[slots:])
        if rest:
            items.append(("Other", rest, theme.neutral_mark))

        return create_donut_card(
            "Languages",
            "Share of total lines per language",
            items,
            theme,
            f"{len(languages)}",
            "language" if len(languages) == 1 else "languages",
        )

    def folders_card(self, result: Statistics, theme: Theme):
        folders = sorted(
            self.analytics.get_folder_statistics(result).items(),
            key=lambda item: item[1]["lines"],
            reverse=True
        )[:8]

        return create_bar_card(
            "Largest folders",
            f"Top {len(folders)} folders by total lines (direct files only)",
            [elide_left(folder_name(name), 20) for name, _ in folders],
            [data["lines"] for _, data in folders],
            [
                f"<b>{folder_name(name)}</b><br>"
                f"{data['lines']:,} lines in {data['files']:,} files"
                for name, data in folders
            ],
            theme,
        )
