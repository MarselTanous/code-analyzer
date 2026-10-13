import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from services.analytics import AnalyticsService
from services.exporter import CsvExporter
from services.worker import AnalyzerWorker
from ui.logo import logo_pixmap
from ui.theme import DARK, LIGHT, build_stylesheet, system_theme
from ui.widgets.data_table import Column, DataTablePage
from ui.widgets.overview_page import OverviewPage, folder_name


PAGES = [
    ("Overview", "Key figures and charts for the analyzed project"),
    ("Files", "Every analyzed source file — search, filter and sort"),
    ("Folders", "Line counts aggregated per folder"),
]


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.thread = None
        self.worker = None
        self.started_at = 0.0

        self.last_result = None
        self.exporter = CsvExporter()

        self.analytics = AnalyticsService()

        self.theme = system_theme()

        self.setup_window()
        self.create_ui()
        self.apply_theme()

    def setup_window(self):
        """
        Configure main window properties.
        """

        self.setWindowTitle(
            "Code Analyzer"
        )

        self.resize(
            1440,
            900
        )

        self.setMinimumSize(1100, 700)
        self.setAcceptDrops(True)

    def create_ui(self):
        """
        Create all UI components.
        """

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self.create_sidebar())

        content = QWidget()
        content.setObjectName("Content")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        content_layout.addWidget(self.create_header())

        # Thin indeterminate progress bar shown while analyzing
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(3)
        self.progress.setVisible(False)
        content_layout.addWidget(self.progress)

        body = QWidget()
        body.setObjectName("PageBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(28, 12, 20, 20)

        # Empty state until the first analysis, then the page stack
        self.main_stack = QStackedWidget()
        self.main_stack.addWidget(self.create_empty_state())

        self.pages = QStackedWidget()
        self.overview_page = OverviewPage()
        self.files_page = self.create_files_page()
        self.folders_page = self.create_folders_page()

        self.pages.addWidget(self.overview_page)
        self.pages.addWidget(self.files_page)
        self.pages.addWidget(self.folders_page)

        self.main_stack.addWidget(self.pages)

        body_layout.addWidget(self.main_stack)
        content_layout.addWidget(body, 1)

        root_layout.addWidget(content, 1)

        # Status bar

        self.status_label = QLabel("Ready")
        self.summary_label = QLabel()

        self.statusBar().addWidget(self.status_label, 1)
        self.statusBar().addPermanentWidget(self.summary_label)
        self.statusBar().setSizeGripEnabled(False)

        self.select_page(0)

    def create_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 16)
        layout.setSpacing(4)

        logo = QLabel()
        logo.setPixmap(logo_pixmap(36, self.devicePixelRatioF()))
        logo.setFixedSize(36, 36)

        app_name = QLabel("Code Analyzer")
        app_name.setObjectName("AppName")

        tagline = QLabel("Source line statistics")
        tagline.setObjectName("AppTagline")

        names = QVBoxLayout()
        names.setSpacing(0)
        names.addWidget(app_name)
        names.addWidget(tagline)

        brand = QHBoxLayout()
        brand.setSpacing(10)
        brand.addWidget(logo)
        brand.addLayout(names, 1)

        layout.addLayout(brand)
        layout.addSpacing(24)

        section = QLabel("VIEWS")
        section.setObjectName("SidebarSection")
        layout.addWidget(section)
        layout.addSpacing(4)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        for index, (name, _) in enumerate(PAGES):
            button = QPushButton(name)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            self.nav_group.addButton(button, index)
            layout.addWidget(button)

        self.nav_group.idClicked.connect(self.select_page)

        layout.addStretch()

        self.theme_button = QPushButton()
        self.theme_button.setObjectName("GhostButton")
        self.theme_button.setCursor(Qt.PointingHandCursor)
        self.theme_button.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_button)

        return sidebar

    def create_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("Header")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 22, 20, 14)
        layout.setSpacing(10)

        titles = QVBoxLayout()
        titles.setSpacing(2)

        self.page_title = QLabel()
        self.page_title.setObjectName("PageTitle")

        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName("PageSubtitle")

        titles.addWidget(self.page_title)
        titles.addWidget(self.page_subtitle)

        layout.addLayout(titles, 1)

        # Project path section

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Project folder…")
        self.path_input.setMinimumWidth(320)
        self.path_input.setClearButtonEnabled(True)
        self.path_input.returnPressed.connect(self.analyze_project)

        browse_button = QPushButton("Browse")
        browse_button.setShortcut(QKeySequence.Open)
        browse_button.setToolTip("Select project folder (Ctrl+O)")
        browse_button.clicked.connect(self.select_folder)

        self.export_button = QPushButton("Export CSV")
        self.export_button.setShortcut(QKeySequence("Ctrl+E"))
        self.export_button.setToolTip("Export file statistics (Ctrl+E)")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_csv)

        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.setObjectName("PrimaryButton")
        self.analyze_button.setShortcut(QKeySequence.Refresh)
        self.analyze_button.setToolTip("Analyze project (F5)")
        self.analyze_button.clicked.connect(self.analyze_project)

        for button in (browse_button, self.export_button, self.analyze_button):
            button.setCursor(Qt.PointingHandCursor)

        layout.addWidget(self.path_input)
        layout.addWidget(browse_button)
        layout.addWidget(self.export_button)
        layout.addWidget(self.analyze_button)

        return header

    def create_empty_state(self) -> QWidget:
        widget = QFrame()
        widget.setObjectName("Card")

        icon = QLabel()
        icon.setPixmap(logo_pixmap(72, self.devicePixelRatioF()))

        title = QLabel("No project analyzed yet")
        title.setObjectName("EmptyTitle")

        text = QLabel(
            "Choose a project folder with Browse, paste a path or drop a "
            "folder onto this window,\nthen press Analyze to see line "
            "statistics, charts and the largest files."
        )
        text.setObjectName("EmptyText")

        layout = QVBoxLayout(widget)
        layout.addStretch()
        for label in (icon, title, text):
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            layout.addSpacing(6)
        layout.addStretch()

        return widget

    def create_files_page(self) -> DataTablePage:
        columns = [
            Column("File", lambda f: f.file_path),
            Column("Language", lambda f: f.language),
            Column("Lines", lambda f: f.lines, "bar"),
            Column("Code", lambda f: f.non_empty_lines, "int"),
            Column("Blank", lambda f: f.empty_lines, "int"),
            Column(
                "Code density",
                lambda f: f.non_empty_lines / f.lines if f.lines else 0,
                "percent"
            ),
        ]

        return DataTablePage(
            columns,
            self.theme,
            "Search files…",
            choice_column=1,
            choice_label="All languages",
            sort_column=2,
        )

    def create_folders_page(self) -> DataTablePage:
        columns = [
            Column("Folder", lambda r: r["folder"]),
            Column("Files", lambda r: r["files"], "int"),
            Column("Lines", lambda r: r["lines"], "bar"),
            Column("Code", lambda r: r["non_empty_lines"], "int"),
            Column("Blank", lambda r: r["lines"] - r["non_empty_lines"], "int"),
            Column("Share of lines", lambda r: r["share"], "percent"),
        ]

        return DataTablePage(
            columns,
            self.theme,
            "Search folders…",
            sort_column=2,
        )

    # Navigation & theme

    def select_page(self, index: int):
        self.nav_group.button(index).setChecked(True)
        self.pages.setCurrentIndex(index)

        title, subtitle = PAGES[index]
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)

    def toggle_theme(self):
        self.theme = LIGHT if self.theme.is_dark else DARK
        self.apply_theme()

    def apply_theme(self):
        QApplication.instance().setStyleSheet(
            build_stylesheet(self.theme)
        )

        self.theme_button.setText(
            "☀  Light mode" if self.theme.is_dark else "☾  Dark mode"
        )

        self.files_page.set_theme(self.theme)
        self.folders_page.set_theme(self.theme)

        # Charts carry their colors, so rebuild them.
        if self.last_result:
            self.overview_page.set_data(self.last_result, self.theme)

    # Drag & drop a folder

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls()
        if urls and Path(urls[0].toLocalFile()).is_dir():
            event.acceptProposedAction()

    def dropEvent(self, event):
        folder = event.mimeData().urls()[0].toLocalFile()
        self.path_input.setText(folder)
        self.analyze_project()

    # Actions

    def select_folder(self):
        """
        Open folder selection dialog.
        """

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            self.path_input.text()
        )

        if folder:
            self.path_input.setText(
                folder
            )
            self.analyze_project()

    def set_busy(self, busy: bool):
        self.progress.setVisible(busy)
        self.analyze_button.setEnabled(not busy)
        self.analyze_button.setText("Analyzing…" if busy else "Analyze")

    def analyze_project(self):
        """
        Start analysis in background thread.
        """

        path = self.path_input.text().strip()

        if not path:
            self.status_label.setText(
                "Please select a folder first."
            )
            return

        if not Path(path).is_dir():
            self.status_label.setText(
                f"Folder not found: {path}"
            )
            return

        if self.thread is not None:
            return

        self.set_busy(True)
        self.status_label.setText(
            f"Analyzing {path}…"
        )
        self.started_at = time.perf_counter()

        self.thread = QThread()

        self.worker = AnalyzerWorker(
            path
        )

        self.worker.moveToThread(
            self.thread
        )

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.finished.connect(
            self.analysis_finished
        )

        self.worker.error.connect(
            self.analysis_error
        )

        for signal in (self.worker.finished, self.worker.error):
            signal.connect(self.thread.quit)
            signal.connect(self.worker.deleteLater)

        self.thread.finished.connect(
            self.thread.deleteLater
        )

        self.thread.finished.connect(
            self.thread_finished
        )

        self.thread.start()

    def thread_finished(self):
        self.thread = None
        self.worker = None

    def analysis_finished(self, result):
        """
        Update UI after analysis is completed.
        """

        elapsed = time.perf_counter() - self.started_at

        self.last_result = result
        self.set_busy(False)

        self.overview_page.set_data(result, self.theme)
        self.files_page.set_rows(list(result.files))
        self.folders_page.set_rows(self.folder_rows(result))

        self.main_stack.setCurrentWidget(self.pages)
        self.export_button.setEnabled(bool(result.files))

        if result.files:
            self.status_label.setText(
                f"Analysis completed in {elapsed:.2f}s — "
                f"{self.path_input.text().strip()}"
            )
        else:
            self.status_label.setText(
                "No supported source files found in this folder."
            )

        self.summary_label.setText(
            f"{result.total_files:,} files  ·  {result.total_lines:,} lines"
        )

    def folder_rows(self, result):
        total = result.total_lines or 1

        return [
            {
                "folder": folder_name(folder),
                **data,
                "share": data["lines"] / total,
            }
            for folder, data in self.analytics.get_folder_statistics(
                result
            ).items()
        ]

    def analysis_error(self, message):
        """
        Handle analysis errors.
        """

        self.set_busy(False)

        self.status_label.setText(
            f"Error: {message}"
        )

    def export_csv(self):
        if not self.last_result:
            self.status_label.setText(
                "No analysis data available."
            )
            return

        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            "typescript_report.csv",
            "CSV files (*.csv)"
        )

        if not output_file:
            return

        try:
            self.exporter.export(
                self.last_result,
                output_file
            )
        except OSError as ex:
            self.status_label.setText(
                f"Export failed: {ex}"
            )
            return

        self.status_label.setText(
            f"CSV exported to {output_file}"
        )
