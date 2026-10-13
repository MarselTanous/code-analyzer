import sys

from PySide6.QtWidgets import QApplication

from ui.logo import app_icon
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Code Analyzer")
    app.setWindowIcon(app_icon())

    # Fusion renders the stylesheet consistently on every platform.
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()