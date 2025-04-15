# dialogs.py
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, Signal


class AboutDialog(QtWidgets.QDialog):
    """
    A simple dialog to display information about the application.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setMinimumSize(400, 300)
        self.layout = QtWidgets.QVBoxLayout(self)

        # Title
        self.title_label = QtWidgets.QLabel("ExpCalcs")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 18pt; margin-top: 10px;")
        self.layout.addWidget(self.title_label)

        # Version
        self.version_label = QtWidgets.QLabel("Version 1.0.0")
        self.version_label.setStyleSheet("font-size: 12pt; margin-bottom: 10px;")
        self.layout.addWidget(self.version_label)

        # Description
        self.description_label = QtWidgets.QLabel(
            "ExpCalcs is a calculator for Expedition software, providing advanced mathematical capabilities."
        )
        self.description_label.setWordWrap(True)
        self.layout.addWidget(self.description_label)

        # Close button
        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.layout.addWidget(self.close_button)
