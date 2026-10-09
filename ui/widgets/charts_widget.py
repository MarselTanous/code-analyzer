from typing import List, Sequence, Tuple

from PySide6.QtCore import Qt, QMargins, QRectF
from PySide6.QtGui import QColor, QCursor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QToolTip,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCharts import (
    QAbstractBarSeries,
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QHorizontalBarSeries,
    QPieSeries,
    QValueAxis,
)

from ui.theme import Theme


class ChartCard(QFrame):
    """
    Card with a title, a one-line subtitle and an arbitrary body widget.
    """

    def __init__(self, title: str, subtitle: str, body: QWidget):
        super().__init__()

        self.setObjectName("Card")

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("CardSubtitle")
        subtitle_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(2)

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addSpacing(8)
        layout.addWidget(body, 1)

        self.setMinimumHeight(330)


class DonutChartView(QChartView):
    """
    Chart view that paints a headline figure in the middle of a donut.
    """

    def __init__(self, chart: QChart, theme: Theme,
                 center_text: str, center_caption: str):
        super().__init__(chart)

        self.theme = theme
        self.center_text = center_text
        self.center_caption = center_caption

        self.setRenderHint(QPainter.Antialiasing)
        self.setStyleSheet("background: transparent; border: none;")

    def drawForeground(self, painter: QPainter, rect: QRectF):
        super().drawForeground(painter, rect)

        area = self.chart().plotArea()
        center = area.center()

        value_font = QFont(self.font())
        value_font.setPixelSize(22)
        value_font.setBold(True)

        caption_font = QFont(self.font())
        caption_font.setPixelSize(11)

        painter.save()

        painter.setFont(value_font)
        painter.setPen(QColor(self.theme.text_primary))
        painter.drawText(
            QRectF(center.x() - 80, center.y() - 24, 160, 28),
            Qt.AlignHCenter | Qt.AlignBottom,
            self.center_text
        )

        painter.setFont(caption_font)
        painter.setPen(QColor(self.theme.text_secondary))
        painter.drawText(
            QRectF(center.x() - 80, center.y() + 4, 160, 18),
            Qt.AlignHCenter | Qt.AlignTop,
            self.center_caption
        )

        painter.restore()


class Legend(QWidget):
    """
    Legend rows: color swatch, name, value and share of total.
    Identity is never carried by color alone.
    """

    def __init__(self, items: Sequence[Tuple[str, int, str]]):
        super().__init__()

        total = sum(value for _, value, _ in items) or 1

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)

        for row, (name, value, color) in enumerate(items):
            swatch = QFrame()
            swatch.setFixedSize(10, 10)
            swatch.setStyleSheet(
                f"background: {color}; border-radius: 2px; border: none;"
            )

            name_label = QLabel(name)
            name_label.setObjectName("LegendName")

            value_label = QLabel(f"{value:,}  ·  {value / total:.1%}")
            value_label.setObjectName("LegendValue")
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            layout.addWidget(swatch, row, 0, Qt.AlignVCenter)
            layout.addWidget(name_label, row, 1)
            layout.addWidget(value_label, row, 2)

        layout.setColumnStretch(1, 1)
        layout.setRowStretch(len(items), 1)


def base_chart(theme: Theme) -> QChart:
    """
    Create a chart with a flat background matching the card surface.
    """

    chart = QChart()

    chart.setBackgroundBrush(QColor(theme.surface))
    chart.setBackgroundRoundness(0)
    chart.setMargins(QMargins(0, 0, 0, 0))
    chart.layout().setContentsMargins(0, 0, 0, 0)
    chart.legend().setVisible(False)
    chart.setAnimationOptions(QChart.SeriesAnimations)
    chart.setAnimationDuration(450)

    return chart


def style_axis(axis, theme: Theme, grid: bool):
    """
    Recessive axis: muted labels, hairline grid, quiet baseline.
    """

    axis.setLabelsColor(QColor(theme.text_muted))
    axis.setLinePenColor(QColor(theme.baseline))
    axis.setGridLineVisible(grid)
    axis.setGridLineColor(QColor(theme.gridline))
    axis.setMinorGridLineVisible(False)
    axis.setTruncateLabels(False)

    font = axis.labelsFont()
    font.setPixelSize(11)
    axis.setLabelsFont(font)


def create_view(chart: QChart) -> QChartView:
    view = QChartView(chart)
    view.setRenderHint(QPainter.Antialiasing)
    view.setStyleSheet("background: transparent; border: none;")
    return view


def show_tooltip(state: bool, text: str):
    if state:
        QToolTip.showText(QCursor.pos(), text)
    else:
        QToolTip.hideText()


def create_donut_card(
    title: str,
    subtitle: str,
    items: List[Tuple[str, int, str]],
    theme: Theme,
    center_text: str,
    center_caption: str,
) -> ChartCard:
    """
    Donut chart with a headline in the middle and a value legend beside it.
    items: (name, value, color)
    """

    total = sum(value for _, value, _ in items) or 1

    series = QPieSeries()
    series.setHoleSize(0.64)
    series.setPieSize(0.92)

    for name, value, color in items:
        pie_slice = series.append(name, value)
        pie_slice.setColor(QColor(color))

        # 2px surface gap between segments
        pie_slice.setBorderColor(QColor(theme.surface))
        pie_slice.setBorderWidth(2)
        pie_slice.setExplodeDistanceFactor(0.04)

        text = f"<b>{name}</b><br>{value:,} ({value / total:.1%})"

        pie_slice.hovered.connect(
            lambda state, s=pie_slice, t=text: (
                s.setExploded(state),
                show_tooltip(state, t)
            )
        )

    chart = base_chart(theme)
    chart.addSeries(series)

    view = DonutChartView(chart, theme, center_text, center_caption)
    view.setMinimumSize(200, 200)

    body = QWidget()
    layout = QHBoxLayout(body)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(16)
    layout.addWidget(view, 3)
    layout.addWidget(Legend(items), 2, Qt.AlignVCenter)

    return ChartCard(title, subtitle, body)


def create_bar_card(
    title: str,
    subtitle: str,
    labels: List[str],
    values: List[int],
    tooltips: List[str],
    theme: Theme,
    horizontal: bool = True,
    value_title: str = "Lines",
) -> ChartCard:
    """
    Single-series bar chart. Horizontal bars are ranked largest at the top.
    """

    if horizontal:
        # Qt draws the first category at the bottom.
        labels = list(reversed(labels))
        values = list(reversed(values))
        tooltips = list(reversed(tooltips))

    bar_set = QBarSet(value_title)
    bar_set.append(values)
    bar_set.setColor(QColor(theme.series[0]))
    bar_set.setBorderColor(QColor(theme.series[0]))
    bar_set.setLabelColor(QColor(theme.text_secondary))
    bar_set.setPen(QPen(Qt.NoPen))

    bar_set.hovered.connect(
        lambda state, index: show_tooltip(state, tooltips[index])
    )

    series = QHorizontalBarSeries() if horizontal else QBarSeries()
    series.append(bar_set)
    series.setBarWidth(0.62)
    series.setLabelsVisible(True)
    series.setLabelsPosition(QAbstractBarSeries.LabelsOutsideEnd)
    series.setLabelsFormat("@value")
    series.setLabelsPrecision(12)

    chart = base_chart(theme)
    chart.addSeries(series)

    category_axis = QBarCategoryAxis()
    category_axis.append(labels)
    style_axis(category_axis, theme, grid=False)

    value_axis = QValueAxis()
    value_axis.setLabelFormat("%d")
    # Headroom so the outside-end labels are never clipped.
    value_axis.setRange(0, max(values, default=0) * 1.22 or 1)
    value_axis.setTickCount(5)
    value_axis.applyNiceNumbers()
    style_axis(value_axis, theme, grid=True)
    value_axis.setLineVisible(False)

    if horizontal:
        chart.addAxis(category_axis, Qt.AlignLeft)
        chart.addAxis(value_axis, Qt.AlignBottom)
    else:
        chart.addAxis(category_axis, Qt.AlignBottom)
        chart.addAxis(value_axis, Qt.AlignLeft)

    series.attachAxis(category_axis)
    series.attachAxis(value_axis)

    return ChartCard(title, subtitle, create_view(chart))
