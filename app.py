import sys
from enum import IntEnum, auto
from PySide6 import QtCore, QtWidgets, QtGui

from pydantic import ValidationError

import ExpCalcs
from Expedition import ExpeditionDLL

from typing import Optional, Dict, List
import logging
import os

DEFAULT_CONFIG_FILE = "config.json"


class Column(IntEnum):
    Name = 0
    Inputs = auto()
    Expression = auto()
    WindowLength = auto()
    OutputVar = auto()
    OutputLabel = auto()
    Value = auto()


class ExpCalcsWidget(QtWidgets.QWidget):
    load_default_config = QtCore.Signal()
    licensed = QtCore.Signal(bool)

    COLUMN_LABELS = {
        Column.Name: "Config",
        Column.Inputs: "Inputs",
        Column.Expression: "Expression",
        Column.WindowLength: "Window Length",
        Column.OutputVar: "Output Var",
        Column.OutputLabel: "Output Label",
        Column.Value: "Value",
    }

    def __init__(self):
        super().__init__()
        self.config = None
        self.expedition = None
        self.calculators: List[ExpCalcs.MathChannelCalculator] = []
        self._licensed = False

        self.layout = QtWidgets.QVBoxLayout(self)
        self.config_tree = QtWidgets.QTreeWidget()
        self.config_tree.setHeaderLabels([self.COLUMN_LABELS[col] for col in Column])
        self.config_tree.setColumnCount(len(Column))
        self.config_tree.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.layout.addWidget(self.config_tree)
        self.channel_items = {}

        self.load_default_config.connect(self.on_load_default_config)
        self.load_default_config.emit()

        self.timer_10hz = QtCore.QTimer()
        self.timer_10hz.timeout.connect(self.update_10hz)

        self.licensed.connect(self.run_calcs)

    @QtCore.Slot()
    def run_calcs(self):
        if self._licensed:
            self.timer_10hz.start(100)

    @QtCore.Slot()
    def on_load_default_config(self):
        if os.path.exists(DEFAULT_CONFIG_FILE):
            path = DEFAULT_CONFIG_FILE
            self.load_config(path)

    def check_license(self):
        self._licensed = ExpCalcs.licensing.check_license()
        self.licensed.emit(self._licensed)

    def load_config_from_file(self, file_path: str) -> Optional[ExpCalcs.Config]:
        if os.path.exists(file_path):
            try:
                config = ExpCalcs.Config.parse_file(file_path)
                return config
            except ValidationError as e:
                print(f"Error loading config from file: {e}")
                # show error message in a qt popup
                QtWidgets.QMessageBox.critical(self, "Error", f"Error loading config from file: {e}")
                return None
        else:
            raise Exception(f"file '{file_path}' does not exist")

    def load_config(self, path):
        if path:
            self.config = self.load_config_from_file(path)
            if self.config is not None:
                try:
                    self.expedition = ExpeditionDLL(self.config.expedition.install_path)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error", f"Error loading expedition: {e}")
                    return

                self.config_tree.clear()
                self.calculators = []
                self.channel_items = {}
                math_channels_item = QtWidgets.QTreeWidgetItem(self.config_tree, ["Math Channels"])
                for math_channel in self.config.math_channels:
                    self.add_chanel_tree_item(math_channel, math_channels_item)
                    calculator = ExpCalcs.MathChannelCalculator(math_channel, self.expedition)
                    self.calculators.append(calculator)
                rolling_channels_item = QtWidgets.QTreeWidgetItem(self.config_tree, ["Rolling Channels"])
                for rolling_channel in self.config.rolling_math_channels:
                    self.add_chanel_tree_item(rolling_channel, rolling_channels_item)
                    calculator = ExpCalcs.RollingMathChannelCalculator(rolling_channel, self.expedition)
                    self.calculators.append(calculator)

    def add_chanel_tree_item(self, channel, parent):
        channel_item = QtWidgets.QTreeWidgetItem(parent, [channel.name])
        channel_item.setText(Column.Inputs, f'{[i.local_var_name for i in channel.inputs]}')
        channel_item.setText(Column.Expression, channel.expression)
        channel_item.setText(Column.OutputVar, channel.output_expedition_var_enum_string)

        if isinstance(channel, ExpCalcs.RollingMathChannelConfig):
            channel_item.setText(Column.WindowLength, channel.window_length)

        if channel.output_expedition_user_name:
            channel_item.setText(Column.OutputLabel, channel.output_expedition_user_name)
        self.channel_items[channel.name] = channel_item

    @QtCore.Slot()
    def update_10hz(self):
        for calculator in self.calculators:
            name = calculator.config.name
            result = calculator.calculate()
            channel_item = self.channel_items.get(name, None)
            if channel_item:
                value_str = f"{result:.2f}"
                channel_item.setText(Column.Value, value_str)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ExpCalcs")
        self.exp_calcs = ExpCalcsWidget()
        self.setCentralWidget(self.exp_calcs)
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        # set window size
        self.resize(800, 600)

        self.exp_calcs.licensed.connect(self.on_licence_check)
        self.exp_calcs.check_license()

    @QtCore.Slot(bool)
    def on_licence_check(self, is_licensed):
        if is_licensed:
            self.status_bar.showMessage("Licensed")
        else:
            client_id = ExpCalcs.get_client_id()
            self.status_bar.addWidget(QtWidgets.QLabel("Client ID:"))
            self.status_bar.addWidget(QtWidgets.QLineEdit(client_id, readOnly=True))
            self.status_bar.addWidget(QtWidgets.QPushButton("Copy Client ID", clicked=self.on_copy_client_id))
            QtCore.QTimer.singleShot(2000, self.show_license_check_failed_message)

    @QtCore.Slot()
    def on_copy_client_id(self):
        client_id = ExpCalcs.get_client_id()
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(client_id)

    @QtCore.Slot()
    def show_license_check_failed_message(self):
        QtWidgets.QMessageBox.critical(self, "License Check", "License check failed!")


if __name__ == "__main__":
    log_level = "INFO"
    logging.basicConfig(level=log_level)

    app = QtWidgets.QApplication([])
    # set icon to be expcalcs.ico
    app.setWindowIcon(QtGui.QIcon("expcalcs.ico"))

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
