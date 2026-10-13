from dataclasses import dataclass
from typing import Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication


@dataclass(frozen=True)
class Theme:
    """
    Color tokens shared by the stylesheet, charts and table delegates.
    """

    name: str

    page: str
    surface: str
    sidebar: str
    border: str
    hover: str
    selection: str

    text_primary: str
    text_secondary: str
    text_muted: str

    gridline: str
    baseline: str

    accent: str
    accent_hover: str
    accent_text: str

    neutral_mark: str

    # Categorical slots, assigned in fixed order (never cycled).
    series: Tuple[str, ...]

    @property
    def is_dark(self) -> bool:
        return self.name == "dark"


LIGHT = Theme(
    name="light",
    page="#f1f1ee",
    surface="#fcfcfb",
    sidebar="#fcfcfb",
    border="#e1e0d9",
    hover="#efeeea",
    selection="#cde2fb",
    text_primary="#0b0b0b",
    text_secondary="#52514e",
    text_muted="#898781",
    gridline="#e1e0d9",
    baseline="#c3c2b7",
    accent="#2a78d6",
    accent_hover="#256abf",
    accent_text="#ffffff",
    neutral_mark="#c3c2b7",
    series=(
        "#2a78d6", "#eb6834", "#1baf7a", "#eda100",
        "#e87ba4", "#008300", "#4a3aa7", "#e34948",
    ),
)

DARK = Theme(
    name="dark",
    page="#0d0d0d",
    surface="#1a1a19",
    sidebar="#141413",
    border="#2c2c2a",
    hover="#252523",
    selection="#184f95",
    text_primary="#ffffff",
    text_secondary="#c3c2b7",
    text_muted="#898781",
    gridline="#2c2c2a",
    baseline="#383835",
    accent="#2a78d6",
    accent_hover="#3987e5",
    accent_text="#ffffff",
    neutral_mark="#52514e",
    series=(
        "#3987e5", "#d95926", "#199e70", "#c98500",
        "#d55181", "#008300", "#9085e9", "#e66767",
    ),
)


def system_theme() -> Theme:
    """
    Pick the theme matching the OS color scheme (Qt 6.5+), light otherwise.
    """

    try:
        scheme = QGuiApplication.styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return DARK
    except AttributeError:
        pass

    return LIGHT


def build_stylesheet(t: Theme) -> str:
    """
    Application-wide Qt stylesheet for the given theme.
    """

    return f"""
    QWidget {{
        color: {t.text_primary};
        font-size: 13px;
    }}

    QMainWindow, #Content, #PageBody, QScrollArea, #ScrollContent {{
        background: {t.page};
        border: none;
    }}

    /* Sidebar */

    #Sidebar {{
        background: {t.sidebar};
        border-right: 1px solid {t.border};
    }}

    #AppName {{
        font-size: 16px;
        font-weight: 700;
    }}

    #AppTagline, #SidebarSection {{
        color: {t.text_muted};
        font-size: 11px;
    }}

    #SidebarSection {{
        font-weight: 600;
        letter-spacing: 1px;
    }}

    #NavButton {{
        text-align: left;
        padding: 9px 12px;
        border: none;
        border-radius: 8px;
        background: transparent;
        color: {t.text_secondary};
        font-weight: 500;
    }}

    #NavButton:hover {{
        background: {t.hover};
        color: {t.text_primary};
    }}

    #NavButton:checked {{
        background: {t.selection};
        color: {t.text_primary};
        font-weight: 600;
    }}

    /* Header */

    #Header {{
        background: {t.page};
    }}

    #PageTitle {{
        font-size: 22px;
        font-weight: 700;
    }}

    #PageSubtitle {{
        color: {t.text_secondary};
    }}

    /* Inputs & buttons */

    QLineEdit, QComboBox {{
        background: {t.surface};
        border: 1px solid {t.border};
        border-radius: 8px;
        padding: 7px 10px;
        selection-background-color: {t.selection};
        selection-color: {t.text_primary};
    }}

    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {t.accent};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 22px;
    }}

    QComboBox QAbstractItemView {{
        background: {t.surface};
        border: 1px solid {t.border};
        selection-background-color: {t.selection};
        selection-color: {t.text_primary};
        outline: none;
    }}

    QPushButton {{
        background: {t.surface};
        border: 1px solid {t.border};
        border-radius: 8px;
        padding: 7px 16px;
        font-weight: 600;
    }}

    QPushButton:hover {{
        background: {t.hover};
    }}

    QPushButton:disabled {{
        color: {t.text_muted};
    }}

    #PrimaryButton {{
        background: {t.accent};
        border: 1px solid {t.accent};
        color: {t.accent_text};
    }}

    #PrimaryButton:hover {{
        background: {t.accent_hover};
        border: 1px solid {t.accent_hover};
    }}

    #PrimaryButton:disabled {{
        background: {t.baseline};
        border: 1px solid {t.baseline};
        color: {t.surface};
    }}

    #GhostButton {{
        background: transparent;
        border: 1px solid {t.border};
        color: {t.text_secondary};
        text-align: left;
        padding: 8px 12px;
    }}

    #GhostButton:hover {{
        background: {t.hover};
        color: {t.text_primary};
    }}

    QProgressBar {{
        background: transparent;
        border: none;
        max-height: 3px;
    }}

    QProgressBar::chunk {{
        background: {t.accent};
    }}

    /* Cards */

    #Card {{
        background: {t.surface};
        border: 1px solid {t.border};
        border-radius: 12px;
    }}

    #Card QLabel {{
        background: transparent;
        border: none;
    }}

    #CardTitle {{
        font-size: 14px;
        font-weight: 600;
    }}

    #CardSubtitle, #KpiCaption, #LegendValue {{
        color: {t.text_secondary};
        font-size: 12px;
    }}

    #KpiTitle {{
        color: {t.text_muted};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }}

    #KpiValue {{
        font-size: 26px;
        font-weight: 700;
    }}

    #LegendName {{
        font-size: 12px;
    }}

    /* Empty state */

    #EmptyTitle {{
        font-size: 20px;
        font-weight: 700;
    }}

    #EmptyText {{
        color: {t.text_secondary};
        font-size: 14px;
    }}

    /* Tables */

    QTableView {{
        background: {t.surface};
        alternate-background-color: {t.surface};
        border: none;
        gridline-color: transparent;
        selection-background-color: {t.selection};
        selection-color: {t.text_primary};
        outline: none;
    }}

    QTableView::item {{
        border-bottom: 1px solid {t.gridline};
        padding: 0 10px;
    }}

    QHeaderView::section {{
        background: {t.surface};
        color: {t.text_muted};
        font-size: 11px;
        font-weight: 600;
        border: none;
        border-bottom: 1px solid {t.baseline};
        padding: 10px;
    }}

    QTableCornerButton::section {{
        background: {t.surface};
        border: none;
    }}

    #CountLabel {{
        color: {t.text_muted};
        font-size: 12px;
    }}

    /* Scrollbars */

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px;
    }}

    QScrollBar::handle {{
        background: {t.baseline};
        border-radius: 3px;
        min-height: 30px;
        min-width: 30px;
    }}

    QScrollBar::handle:hover {{
        background: {t.text_muted};
    }}

    QScrollBar::add-line, QScrollBar::sub-line,
    QScrollBar::add-page, QScrollBar::sub-page {{
        background: none;
        border: none;
        width: 0;
        height: 0;
    }}

    /* Status bar & tooltips */

    QStatusBar {{
        background: {t.sidebar};
        border-top: 1px solid {t.border};
        color: {t.text_secondary};
        font-size: 12px;
    }}

    QStatusBar QLabel {{
        color: {t.text_secondary};
        font-size: 12px;
        padding: 0 8px;
    }}

    QToolTip {{
        background: {t.surface};
        color: {t.text_primary};
        border: 1px solid {t.border};
        border-radius: 6px;
        padding: 6px 8px;
    }}
    """
