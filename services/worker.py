from PySide6.QtCore import (
    QObject,
    Signal
)

from services.analyzer import Analyzer


class AnalyzerWorker(QObject):

    finished = Signal(object)
    error = Signal(str)


    def __init__(self, path: str):
        super().__init__()

        self.path = path
        self.analyzer = Analyzer()


    def run(self):
        """
        Execute analysis in background thread.
        """

        try:
            result = self.analyzer.analyze(
                self.path
            )

            self.finished.emit(
                result
            )

        except Exception as ex:
            self.error.emit(
                str(ex)
            )