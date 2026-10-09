from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout
)


class SummaryCard(QFrame):
    """
    KPI tile: small title, large headline value and a short caption.
    """

    def __init__(self, title: str, caption: str = ""):
        super().__init__()

        self.setObjectName("Card")

        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("KpiTitle")

        self.value_label = QLabel("—")
        self.value_label.setObjectName("KpiValue")

        self.caption_label = QLabel(caption)
        self.caption_label.setObjectName("KpiCaption")

        self.setup_ui()

    def setup_ui(self):
        """
        Create the visual layout of the card.
        """

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.caption_label)

        self.setMinimumWidth(160)

    def set_value(self, value, caption: str = None):
        """
        Update the displayed value (ints get thousands separators).
        """

        if isinstance(value, int):
            value = f"{value:,}"

        self.value_label.setText(str(value))

        if caption is not None:
            self.caption_label.setText(caption)
            self.caption_label.setToolTip(caption)
