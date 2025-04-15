# dialogs.py
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QStringListModel, Signal

from ExpCalcs import InputVar, MathChannelConfig
from Expedition import Var


class FilterableList(QtWidgets.QWidget):
    itemSelected = Signal(str)

    def __init__(self, current_var: str = ""):
        super().__init__()

        self.selectedItem = current_var

        # Widgets
        self.filter_input = QtWidgets.QLineEdit()
        self.filter_input.setPlaceholderText("Type to filter...")
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.list_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.list_widget.setSortingEnabled(True)

        # Populate list
        self.items = [v.name for v in Var]
        for item in self.items:
            self.list_widget.addItem(item)

        # select the current item if it exists
        if current_var in self.items:
            item = self.list_widget.findItems(current_var, Qt.MatchExactly)
            if item:
                self.list_widget.setCurrentItem(item[0])

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(self.filter_input)
        layout.addWidget(self.list_widget)

        # Connect filter
        self.filter_input.textChanged.connect(self.filter_items)
        self.list_widget.itemSelectionChanged.connect(self.on_item_selected)

    def filter_items(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def on_item_selected(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            selected_item = selected_items[0].text()
            self.selectedItem = selected_item
            self.itemSelected.emit(selected_item)
        else:
            self.selectedItem = ""
            self.itemSelected.emit("")


class SelectVarDialog(QtWidgets.QDialog):
    def __init__(self, current_var: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Variable")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.selected_item = current_var

        # Filterable list
        self.filterable_list = FilterableList(current_var=current_var)
        self.layout.addWidget(self.filterable_list)
        self.filterable_list.itemSelected.connect(self.on_item_selected)

        # Buttons
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def on_item_selected(self):
        self.selected_item = self.filterable_list.selectedItem


class SelectInputsDialog(QtWidgets.QDialog):
    def __init__(self, current_inputs=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Inputs")
        self.layout = QtWidgets.QVBoxLayout(self)

        self.inputs = current_inputs if current_inputs else []

        self.input_list = QtWidgets.QListWidget()
        self.layout.addWidget(self.input_list)
        for iv in self.inputs:
            self.input_list.addItem(f"{iv.local_var_name} ← {iv.expedition_var.name}")

        form_layout = QtWidgets.QHBoxLayout()
        self.var_label = QtWidgets.QLabel("Var: (none)")
        self.select_var_button = QtWidgets.QPushButton("Select Var")
        self.select_var_button.clicked.connect(self.select_var)
        self.local_name_input = QtWidgets.QLineEdit()
        self.local_name_input.setPlaceholderText("Local name")
        self.add_button = QtWidgets.QPushButton("Add")
        self.add_button.clicked.connect(self.add_input)

        form_layout.addWidget(self.var_label)
        form_layout.addWidget(self.select_var_button)
        form_layout.addWidget(self.local_name_input)
        form_layout.addWidget(self.add_button)
        self.layout.addLayout(form_layout)

        self.delete_button = QtWidgets.QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_selected_input)
        self.layout.addWidget(self.delete_button)
        self.delete_button.setEnabled(False)
        self.input_list.itemSelectionChanged.connect(lambda: self.delete_button.setEnabled(bool(self.input_list.selectedItems())))

        self.selected_var = None

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def select_var(self):
        dialog = SelectVarDialog(parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.selected_var = dialog.selected_item
            self.var_label.setText(f"Var: {self.selected_var}")

    def add_input(self):
        if self.selected_var and self.local_name_input.text().strip():
            var_name = self.selected_var
            local_name = self.local_name_input.text().strip()
            self.inputs.append(InputVar(expedition_var_enum_string=var_name, local_var_name=local_name))
            self.input_list.addItem(f"{local_name} ← {var_name}")
            self.local_name_input.clear()

    def delete_selected_input(self):
        selected_items = self.input_list.selectedItems()
        if selected_items:
            for item in selected_items:
                row = self.input_list.row(item)
                del self.inputs[row]
                self.input_list.takeItem(row)

    def get_inputs(self):
        return self.inputs


class MathChannelConfigDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("Math Channel Configuration")
        self.dialog_layout = QtWidgets.QVBoxLayout(self)
        self.layout = QtWidgets.QVBoxLayout()
        self.dialog_layout.addLayout(self.layout)
        self.setWindowTitle("Rolling Math Channel Configuration")

        # Name fields
        name_group = QtWidgets.QGroupBox("Name")
        self.layout.addWidget(name_group)
        name_layout = QtWidgets.QVBoxLayout()
        name_group.setLayout(name_layout)

        self.name_input = QtWidgets.QLineEdit()
        name_layout.addWidget(self.name_input)

        # Inputs
        inputs_group = QtWidgets.QGroupBox("Inputs")
        self.layout.addWidget(inputs_group)
        inputs_layout = QtWidgets.QVBoxLayout()
        inputs_group.setLayout(inputs_layout)

        self.inputs = config.inputs.copy() if config else []
        self.inputs_table = QtWidgets.QTreeWidget()
        # set two columns for the table widget and set headers for Var name and local name
        self.inputs_table.setColumnCount(2)
        self.inputs_table.setHeaderLabels(["Exp Var", "Local Name"])

        self.inputs_button = QtWidgets.QPushButton("Edit Inputs")
        self.inputs_button.clicked.connect(self.on_select_inputs)

        inputs_layout.addWidget(self.inputs_table)
        inputs_layout.addWidget(self.inputs_button)

        # Expression
        expression_group = QtWidgets.QGroupBox("Expression")
        self.layout.addWidget(expression_group)
        expression_layout = QtWidgets.QVBoxLayout()
        expression_group.setLayout(expression_layout)
        self.expression_input = QtWidgets.QLineEdit()
        expression_layout.addWidget(self.expression_input)

        # Window length
        window_layout = QtWidgets.QHBoxLayout()
        self.window_length_input = QtWidgets.QLineEdit()
        window_layout.addWidget(QtWidgets.QLabel("Window Length (optional):"))
        window_layout.addWidget(self.window_length_input)
        expression_layout.addLayout(window_layout)
        window_help_label = QtWidgets.QLabel("Set the window length for the expression (e.g. 1s, 5m, 1h)\n"
                             "If the window length is not set, the expression will be evaluated every time step")
        window_help_label.setStyleSheet("color: gray; font-size: 10px; font-style: italic;")
        expression_layout.addWidget(window_help_label)

            # Output Variable
        outputs_group = QtWidgets.QGroupBox("Output")
        self.layout.addWidget(outputs_group)
        outputs_layout = QtWidgets.QVBoxLayout()
        outputs_group.setLayout(outputs_layout)

        output_var_layout = QtWidgets.QHBoxLayout()
        output_var_layout.setContentsMargins(0, 0, 0, 0)
        output_var_layout.setSpacing(10)
        output_var_layout.addWidget(QtWidgets.QLabel("Expedition Var:"))
        self.output_var_name = QtWidgets.QLabel("(none)")
        self.output_var_select_button = QtWidgets.QPushButton("Select")
        self.output_var_select_button.clicked.connect(self.on_select_output_var)

        output_var_layout.addWidget(self.output_var_name)
        output_var_layout.addWidget(self.output_var_select_button)
        outputs_layout.addLayout(output_var_layout)

        output_name_layout = QtWidgets.QHBoxLayout()
        output_name_layout.setContentsMargins(0, 0, 0, 0)
        output_name_layout.setSpacing(10)
        outputs_layout.addLayout(output_name_layout)

        self.output_label = QtWidgets.QLabel("Custom name (optional):")
        self.output_label_input = QtWidgets.QLineEdit()
        self.output_label_input.setPlaceholderText("MyVariable")
        output_name_layout.addWidget(self.output_label)
        output_name_layout.addWidget(self.output_label_input)
        output_name_help_label = QtWidgets.QLabel("Custom names only work for user variables, e.g. User0, User1")
        output_name_help_label.setStyleSheet("color: gray; font-size: 10px; font-style: italic;")
        outputs_layout.addWidget(output_name_help_label)

        # Buttons
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.dialog_layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Populate fields if editing an existing config
        if config:
            self.name_input.setText(config.name)
            self.expression_input.setText(config.expression)
            self.window_length_input.setText(config.window_length)
            self.output_var_name.setText(config.output_expedition_var.name)
            self.output_label_input.setText(config.output_expedition_user_name)
            # add items to the table widget (Var name in first column, local name in second column)
            for i in self.inputs:
                item = QtWidgets.QTreeWidgetItem([i.expedition_var.name, i.local_var_name])
                self.inputs_table.addTopLevelItem(item)

    def on_select_output_var(self):
        current_var = self.output_var_name.text()
        dialog = SelectVarDialog(current_var=current_var, parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            selected_var = dialog.selected_item
            self.output_var_name.setText(selected_var)

    def on_select_inputs(self):
        dialog = SelectInputsDialog(current_inputs=self.inputs, parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.inputs = dialog.get_inputs()
            self.inputs_table.clear()
            for iv in self.inputs:
                item = QtWidgets.QTreeWidgetItem([iv.expedition_var.name, iv.local_var_name])
                self.inputs_table.addTopLevelItem(item)

    # add a window length input
    def get_config(self):
        # Return a RollingMathChannelConfig object based on user input
        name = self.name_input.text()
        expression = self.expression_input.text()
        output_var = self.output_var_name.text()
        if not output_var:
            output_var = Var.User0.name
        output_label = self.output_label_input.text()
        input_vars = self.inputs
        window_length = self.window_length_input.text()
        if not window_length:
            window_length = None

        return MathChannelConfig(
            name=name,
            expression=expression,
            output_expedition_var_enum_string=output_var,
            output_expedition_user_name=output_label,
            inputs=input_vars,
            window_length=window_length
        )
