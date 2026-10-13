from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.svg"


def logo_pixmap(size: int, device_pixel_ratio: float = 1.0) -> QPixmap:
    """
    Render the SVG logo crisply at the given logical size.
    """

    pixmap = QPixmap(round(size * device_pixel_ratio), round(size * device_pixel_ratio))
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    QSvgRenderer(str(LOGO_PATH)).render(painter)
    painter.end()

    pixmap.setDevicePixelRatio(device_pixel_ratio)
    return pixmap


def app_icon() -> QIcon:
    """
    Application icon with pre-rendered sizes for title bars and taskbars.
    """

    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(logo_pixmap(size))
    return icon
