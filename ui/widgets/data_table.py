from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QRectF,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QStyle,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ui.theme import Theme


SORT_ROLE = Qt.UserRole + 1


@dataclass
class Column:
    """
    Table column definition.
    kind: "text", "int", "percent" or "bar" (int with an inline magnitude bar).
    """

    header: str
    value: Callable[[Any], Any]
    kind: str = "text"


class DataTableModel(QAbstractTableModel):

    def __init__(self, columns: List[Column]):
        super().__init__()

        self.columns = columns
        self.rows: List[Any] = []
        self.maximums: List[float] = []

    def set_rows(self, rows: List[Any]):
        self.beginResetModel()

        self.rows = rows
        self.maximums = [
            max((column.value(row) for row in rows), default=0)
            if column.kind != "text" else 0
            for column in self.columns
        ]

        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal:
            return None

        column = self.columns[section]

        if role == Qt.DisplayRole:
            return column.header.upper()

        if role == Qt.TextAlignmentRole:
            if column.kind == "text":
                return int(Qt.AlignLeft | Qt.AlignVCenter)
            return int(Qt.AlignRight | Qt.AlignVCenter)

        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        column = self.columns[index.column()]
        value = column.value(self.rows[index.row()])

        if role == Qt.DisplayRole:
            if column.kind == "percent":
                return f"{value:.1%}"
            if column.kind in ("int", "bar"):
                return f"{value:,}"
            return value

        if role == SORT_ROLE:
            return value.lower() if isinstance(value, str) else value

        if role == Qt.TextAlignmentRole:
            if column.kind == "text":
                return int(Qt.AlignLeft | Qt.AlignVCenter)
            return int(Qt.AlignRight | Qt.AlignVCenter)

        if role == Qt.ToolTipRole and column.kind == "text":
            return value

        return None

    def column_maximum(self, column: int) -> float:
        return self.maximums[column] if self.maximums else 0


class FilterProxyModel(QSortFilterProxyModel):
    """
    Free-text search across all columns plus an exact-match column filter.
    """

    def __init__(self):
        super().__init__()

        self.setSortRole(SORT_ROLE)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1)

        self.choice_column: Optional[int] = None
        self.choice_value: Optional[str] = None

    def set_choice(self, column: Optional[int], value: Optional[str]):
        self.choice_column = column
        self.choice_value = value
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if self.choice_column is not None and self.choice_value:
            index = self.sourceModel().index(
                source_row, self.choice_column, source_parent
            )
            if index.data(Qt.DisplayRole) != self.choice_value:
                return False

        return super().filterAcceptsRow(source_row, source_parent)


class BarDelegate(QStyledItemDelegate):
    """
    Number with a thin magnitude bar underneath, scaled to the column maximum.
    """

    def __init__(self, model: DataTableModel, theme: Theme, parent=None):
        super().__init__(parent)

        self.model = model
        self.theme = theme

    def paint(self, painter: QPainter, option, index):
        source = index.model().mapToSource(index)
        value = source.data(SORT_ROLE) or 0
        maximum = self.model.column_maximum(source.column()) or 1

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor(self.theme.selection))

        rect = option.rect.adjusted(10, 0, -10, 0)

        painter.setPen(QColor(self.theme.text_primary))
        painter.drawText(
            rect.adjusted(0, 0, 0, -6),
            Qt.AlignRight | Qt.AlignVCenter,
            index.data(Qt.DisplayRole)
        )

        track = QRectF(rect.left(), rect.bottom() - 9, rect.width(), 3)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(self.theme.gridline))
        painter.drawRoundedRect(track, 1.5, 1.5)

        fill = QRectF(track)
        fill.setWidth(max(2.0, track.width() * value / maximum))
        painter.setBrush(QColor(self.theme.series[0]))
        painter.drawRoundedRect(fill, 1.5, 1.5)

        painter.setPen(QColor(self.theme.gridline))
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())

        painter.restore()


class DataTablePage(QWidget):
    """
    Card containing a search box, an optional choice filter and a sortable table.
    """

    def __init__(self, columns: List[Column], theme: Theme,
                 search_placeholder: str,
                 choice_column: Optional[int] = None,
                 choice_label: str = "All",
                 sort_column: int = 0):
        super().__init__()

        self.columns = columns
        self.choice_column = choice_column
        self.choice_label = choice_label
        self.sort_column = sort_column

        self.model = DataTableModel(columns)
        self.proxy = FilterProxyModel()
        self.proxy.setSourceModel(self.model)

        self.bar_delegates: List[BarDelegate] = []

        self.create_ui(theme, search_placeholder)

    def create_ui(self, theme: Theme, search_placeholder: str):
        card = QFrame()
        card.setObjectName("Card")

        # Toolbar

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(search_placeholder)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMaximumWidth(360)
        self.search_input.textChanged.connect(self.update_filter)

        self.choice_combo = QComboBox()
        self.choice_combo.setMinimumWidth(160)
        self.choice_combo.currentIndexChanged.connect(self.update_filter)
        self.choice_combo.setVisible(self.choice_column is not None)

        self.count_label = QLabel()
        self.count_label.setObjectName("CountLabel")

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(16, 14, 16, 10)
        toolbar.setSpacing(10)
        toolbar.addWidget(self.search_input, 1)
        toolbar.addWidget(self.choice_combo)
        toolbar.addStretch()
        toolbar.addWidget(self.count_label)

        # Table

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setTextElideMode(Qt.ElideMiddle)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)

        header = self.table.horizontalHeader()
        header.setHighlightSections(False)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setMinimumSectionSize(90)

        for index, column in enumerate(self.columns):
            if column.kind == "bar":
                delegate = BarDelegate(self.model, theme, self.table)
                self.bar_delegates.append(delegate)
                self.table.setItemDelegateForColumn(index, delegate)
                header.resizeSection(index, 170)
            elif index > 0:
                header.resizeSection(index, 120)

        self.table.sortByColumn(self.sort_column, Qt.DescendingOrder)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 6)
        card_layout.setSpacing(0)
        card_layout.addLayout(toolbar)
        card_layout.addWidget(self.table, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(card)

    def set_rows(self, rows: List[Any]):
        self.model.set_rows(rows)

        if self.choice_column is not None:
            values = sorted({
                str(self.columns[self.choice_column].value(row))
                for row in rows
            })

            self.choice_combo.blockSignals(True)
            self.choice_combo.clear()
            self.choice_combo.addItem(self.choice_label, "")
            for value in values:
                self.choice_combo.addItem(value, value)
            self.choice_combo.blockSignals(False)

        self.update_filter()

    def set_theme(self, theme: Theme):
        for delegate in self.bar_delegates:
            delegate.theme = theme
        self.table.viewport().update()

    def update_filter(self):
        self.proxy.setFilterFixedString(self.search_input.text())
        self.proxy.set_choice(
            self.choice_column,
            self.choice_combo.currentData()
        )

        shown = self.proxy.rowCount()
        total = self.model.rowCount()

        if shown == total:
            self.count_label.setText(f"{total:,} rows")
        else:
            self.count_label.setText(f"{shown:,} of {total:,} rows")
