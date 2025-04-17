import sys
from enum import IntEnum, auto
from PySide6 import QtCore, QtWidgets, QtGui

from pydantic import ValidationError

if sys.platform.startswith("win"):
    from Expedition import ExpeditionDLL
else:
    # Dummy import for non-Windows platforms (so that I can develop on my Mac)
    from dummy_client import DummyExpeditionDLL as ExpeditionDLL

import ExpCalcs
from ui.dialogs import MathChannelConfigDialog
from ui.debug import DebugDialog
from ui.about import AboutDialog

from typing import Optional, Dict, List
import logging
import os

DEFAULT_CONFIG_FILE = "config.json"

logger = logging.getLogger(__name__)


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

    COLUMN_LABELS = {
        Column.Name: "Name",
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
        self.timer_step = 0.1

        self.layout = QtWidgets.QVBoxLayout(self)
        self.config_tree = QtWidgets.QTreeWidget()
        self.config_tree.setHeaderLabels([self.COLUMN_LABELS[col] for col in Column])
        self.config_tree.setColumnCount(len(Column))
        self.config_tree.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.layout.addWidget(self.config_tree)
        self.channel_items = {}

        self.load_default_config.connect(self.on_load_default_config)
        self.load_default_config.emit()

        # Add buttons for managing MathChannelConfigs
        self.button_layout = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton("➕ Add Math Channel")
        self.edit_button = QtWidgets.QPushButton("✏️ Edit Math Channel")
        self.edit_button.setEnabled(False)
        self.delete_button = QtWidgets.QPushButton("❌ Delete Math Channel")
        self.delete_button.setEnabled(False)
        self.debug_info_button = QtWidgets.QPushButton("🔍 Debug Info")
        self.debug_info_button.setEnabled(False)

        # enable/disable buttons based on selection
        self.config_tree.itemSelectionChanged.connect(lambda: [
            self.edit_button.setEnabled(bool(self.config_tree.selectedItems())),
            self.delete_button.setEnabled(bool(self.config_tree.selectedItems())),
            self.debug_info_button.setEnabled(bool(self.config_tree.selectedItems()))
        ])

        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.edit_button)
        self.button_layout.addWidget(self.delete_button)
        self.button_layout.addWidget(self.debug_info_button)
        self.layout.addLayout(self.button_layout)

        # Connect buttons to their respective slots
        self.add_button.clicked.connect(self.on_add_math_channel)
        self.edit_button.clicked.connect(self.on_edit_math_channel)
        self.delete_button.clicked.connect(self.on_delete_math_channel)
        self.debug_info_button.clicked.connect(self.on_debug_info)

        self.calc_timer = QtCore.QTimer()
        self.calc_timer.timeout.connect(self.update_10hz)
        timer_interval = int(self.timer_step * 1000)  # convert to milliseconds
        self.calc_timer.start(timer_interval)

    @QtCore.Slot()
    def on_load_default_config(self):
        if os.path.exists(DEFAULT_CONFIG_FILE):
            path = DEFAULT_CONFIG_FILE
            self.load_config(path)

    def load_config_from_file(self, file_path: str) -> Optional[ExpCalcs.Config]:
        if os.path.exists(file_path):
            try:
                with open(file_path) as f:
                    config = ExpCalcs.Config.model_validate_json(f.read())
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
            self.apply_config()

    def apply_config(self):
        if self.config is not None:
            try:
                self.expedition = ExpeditionDLL(self.config.expedition.install_path)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Error loading expedition: {e}")
                return

            self.config_tree.clear()
            self.channel_items = {}
            self.calculators = []

            for math_channel in self.config.math_channels:
                self.add_chanel_tree_item(math_channel, self.config_tree)
                calculator = ExpCalcs.Calculator.from_config(math_channel, self.expedition, time_step=0.1)
                self.calculators.append(calculator)

        else:
            QtWidgets.QMessageBox.critical(self, "Error", "No config loaded")

    def add_chanel_tree_item(self, channel, parent):
        channel_item = QtWidgets.QTreeWidgetItem(parent, [channel.name])

        channel_item.setText(Column.Inputs,
                             f'{[f'{i.local_var_name} = {i.expedition_var.name}' for i in channel.inputs]}')
        channel_item.setText(Column.Expression, channel.expression)
        channel_item.setText(Column.OutputVar, channel.output_expedition_var_enum_string)

        # attach the channel to the channel_item so we can access it later
        channel_item.setData(0, QtCore.Qt.UserRole, channel)
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

    def on_add_math_channel(self):
        dialog = MathChannelConfigDialog(self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            try:
                new_config = dialog.get_config()
            except ValidationError as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Error creating config: {e}")
                return
            self.config.math_channels.append(new_config)
            self.save()
            self.apply_config()

    def on_delete_math_channel(self):
        selected_items = self.config_tree.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            # get the channel from the selected item data
            channel_config = selected_item.data(0, QtCore.Qt.UserRole)

            if channel_config:
                # remove the config from the list
                self.config.math_channels.remove(channel_config)
                self.save()
                self.apply_config()

    def on_edit_math_channel(self):
        selected_items = self.config_tree.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            # get the channel from the selected item data
            channel_config = selected_item.data(0, QtCore.Qt.UserRole)

            # check if the selected item is a math channel
            if channel_config:
                dialog = MathChannelConfigDialog(self, channel_config)
                if dialog.exec() == QtWidgets.QDialog.Accepted:
                    updated_config = dialog.get_config()
                    # Update the config in the list
                    index = self.config.math_channels.index(channel_config)
                    self.config.math_channels[index] = updated_config
                    self.save()
                    self.apply_config()

    def on_debug_info(self):
        selected_items = self.config_tree.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            # get the channel from the selected item data
            channel_config = selected_item.data(0, QtCore.Qt.UserRole)
            if channel_config:
                index = self.config.math_channels.index(channel_config) # calculators are in the same order as the config
                calculator = self.calculators[index]
                debug_dialog = DebugDialog(calculator, self)
                debug_dialog.exec()

    def save(self):
        # save the config to file
        if self.config:
            with open(DEFAULT_CONFIG_FILE, "w") as f:
                f.write(self.config.model_dump_json(indent=4))
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "No config loaded")


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

        # add a top menu with help and about
        self.menu_bar = self.menuBar()
        self.setMenuBar(self.menu_bar)
        self.channels_menu = self.menu_bar.addMenu("Math Channels")
        self.add_channel_action = QtGui.QAction("Add Channel", self)
        self.add_channel_action.triggered.connect(self.exp_calcs.on_add_math_channel)

        self.help_menu = self.menu_bar.addMenu("Help")
        self.about_action = QtGui.QAction("About", self)
        self.about_action.triggered.connect(self.show_about_dialog)
        self.help_menu.addAction(self.about_action)

    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec()

if __name__ == "__main__":
    log_level = "INFO"
    logging.basicConfig(level=log_level)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("ExpCalcs")
    # set icon to be expcalcs.ico
    app.setWindowIcon(QtGui.QIcon("expcalcs.ico"))

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
