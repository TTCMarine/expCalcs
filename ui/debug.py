# dialogs.py
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, Signal
from datetime import datetime
from typing import Dict, Any

from ExpCalcs import InputVar, MathChannelConfig, Calculator
from Expedition import Var


class DebugDialog(QtWidgets.QDialog):
    """
    A simple dialog to display debug information for a calculator.
    """

    def __init__(self, calculator: Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.setWindowTitle(f"🪲 Debug: {calculator.name}")
        self.errors = []
        self.max_number_of_errors = 20

        self.setMinimumSize(500, 400)
        self.layout = QtWidgets.QVBoxLayout(self)

        # Title for info
        self.info_label = QtWidgets.QLabel("Info")
        self.info_label.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 4px;")
        self.layout.addWidget(self.info_label)

        self.info_display = QtWidgets.QPlainTextEdit(self)
        self.info_display.setReadOnly(True)
        self.info_display.setStyleSheet(
            "font-family: 'Courier New'; font-size: 12pt; background-color: #f4f4f4;"
        )

        self.layout.addWidget(self.info_display)
        # Title for value
        self.value_label = QtWidgets.QLabel("Latest Value")
        self.value_label.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        self.layout.addWidget(self.value_label)

        self.value_display = QtWidgets.QLabel(self)
        self.value_display.setStyleSheet(
            "font-family: 'Courier New'; font-size: 12pt; background-color: #f4f4f4; padding: 6px; border: 1px solid #ccc;"
        )
        self.value_display.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.layout.addWidget(self.value_display)

        # Title for variables
        self.variables_label = QtWidgets.QLabel("Variables")
        self.variables_label.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 4px;")
        self.layout.addWidget(self.variables_label)

        self.variables_display = QtWidgets.QPlainTextEdit(self)
        self.variables_display.setReadOnly(True)
        self.variables_display.setStyleSheet(
            "font-family: 'Courier New'; font-size: 12pt; background-color: #f4f4f4;"
        )
        self.layout.addWidget(self.variables_display)

        # Title for errors
        self.error_label = QtWidgets.QLabel("Errors")
        self.error_label.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 4px;")
        self.layout.addWidget(self.error_label)

        self.error_display = QtWidgets.QPlainTextEdit(self)
        self.error_display.setReadOnly(True)
        self.error_display.setStyleSheet(
            "font-family: 'Courier New'; font-size: 12pt; background-color: #f4f4f4;"
        )
        self.layout.addWidget(self.error_display)

        # dialog buttons
        self.button_box = QtWidgets.QDialogButtonBox(Qt.Horizontal, self)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        self.layout.addWidget(self.button_box)

        self.update_info()
        self.calculator.evaluated.connect(self.calculator_evaluated)
        self.calculator.error.connect(self.calculator_error)

    def update_info(self):
        info = f"Calculator: {self.calculator.__class__.__name__}\n"
        info += f"Expression: {self.calculator.expression}\n"
        info += f"Output Variable: {self.calculator.output_var.name}\n"
        info += f"Output User Name: {self.calculator.output_var_user_name}\n"
        self.info_display.setPlainText(info)

    def update_variables(self):
        variables = ""
        for var_name, var_value in self.calculator.evaluation_variables.items():
            variables += f"{var_name}: {var_value}\n"
        self.variables_display.setPlainText(variables)

    def calculator_evaluated(self, float_value: float):
        now = datetime.now()
        value_text = f"{float_value}  ({now.strftime('%Y-%m-%d %H:%M:%S.%f')})"
        self.value_display.setText(value_text)
        self.update_variables()

    def calculator_error(self, error_message: str):
        now = datetime.now()
        error_text = f"{error_message}  ({now.strftime('%Y-%m-%d %H:%M:%S.%f')})"
        self.errors.append(error_text)
        if len(self.errors) > self.max_number_of_errors:
            self.errors.pop(0)

        self.error_display.setPlainText("\n".join(self.errors))
        self.error_display.verticalScrollBar().setValue(self.error_display.verticalScrollBar().maximum())
        self.update_variables()
