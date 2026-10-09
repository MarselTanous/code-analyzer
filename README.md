# Code Analyzer

A desktop application (PySide6 / Qt) that scans a project folder and shows line statistics for its source files: totals, charts, the largest files and per-folder breakdowns. Results can be exported to CSV.

## Features

- **Overview** – key figures (files, lines, code vs. blank lines) with bar and donut charts
- **Files** – every analyzed file with language, line count, code/blank lines and code density; searchable, filterable by language and sortable
- **Folders** – line counts aggregated per folder with share of total lines
- **CSV export** of the per-file statistics
- Light and dark theme (follows the system theme by default)
- Drag & drop a folder onto the window to analyze it
- Analysis runs in a background thread, so the UI stays responsive

### Supported languages

| Extension | Language   |
|-----------|------------|
| `.ts`     | TypeScript |
| `.tcl`    | Tcl        |
| `.c`      | C          |
| `.py`     | Python     |
| `.java`   | Java       |

The following directories are skipped: `node_modules`, `.git`, `dist`, `coverage`, `.angular`, `.idea`, `venv`.

Languages and excluded directories can be changed in `services/analyzer.py` (`SUPPORTED_LANGUAGES`, `EXCLUDED_DIRS`).

## Requirements

- Python 3.10+ (developed with Python 3.13)
- PySide6

## Installation

```bash
git clone <repository-url>
cd code-analyzer

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

1. Select a project folder with **Browse**, paste a path, or drop a folder onto the window.
2. Press **Analyze**.
3. Switch between **Overview**, **Files** and **Folders** in the sidebar.
4. Use **Export CSV** to save the file statistics.

### Keyboard shortcuts

| Shortcut | Action                 |
|----------|------------------------|
| `Ctrl+O` | Select project folder  |
| `F5`     | Analyze project        |
| `Ctrl+E` | Export CSV             |

### CSV format

```
File,Folder,Extension,Language,Lines,Non Empty Lines,Empty Lines
```

## Project structure

```
code-analyzer/
├── main.py                  # Application entry point
├── models/
│   └── statistics.py        # FileStatistic / Statistics data classes
├── services/
│   ├── analyzer.py          # Walks the folder and counts lines
│   ├── analytics.py         # Aggregations (top files, folders, languages, distribution)
│   ├── exporter.py          # CSV export
│   └── worker.py            # Runs the analyzer in a background QThread
└── ui/
    ├── main_window.py       # Main window, sidebar, header, navigation
    ├── theme.py             # Light/dark theme and stylesheet
    └── widgets/
        ├── overview_page.py # Overview page with summary cards and charts
        ├── charts_widget.py # Bar and donut chart cards (QtCharts)
        ├── data_table.py    # Searchable, sortable table page
        └── summary_card.py  # Key-figure card
```
