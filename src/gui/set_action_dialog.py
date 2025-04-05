import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QDialogButtonBox, QWidget, QStackedWidget, QLineEdit,
                             QCheckBox, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSlot

from .constants import MODIFIER_KEYS, KEY_GROUPS

class SetActionDialog(QDialog):
    """Dialog to configure an action using category selection."""
    def __init__(self, expression_name, current_action_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Set Action for {expression_name.replace('_', ' ').title()}")
        self.setMinimumWidth(450)

        self.selected_action_config = current_action_config

        self.main_layout = QVBoxLayout(self)
        info_label = QLabel(f"Select action type for: <b>{expression_name.replace('_', ' ').title()}</b>")
        self.main_layout.addWidget(info_label)

        self.category_combo = QComboBox()
        self.categories = {
            "None": 0,
            "Keyboard Action": 1,
            "Type Text": 2
        }
        self.category_combo.addItems(self.categories.keys())
        self.main_layout.addWidget(self.category_combo)

        self.options_stack = QStackedWidget()
        self._create_category_pages()
        self.main_layout.addWidget(self.options_stack)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(button_box)

        self._set_initial_state(current_action_config)

        self.category_combo.currentTextChanged.connect(self._on_category_changed)

        self.setLayout(self.main_layout)

    def _create_category_pages(self):
        """Creates the different widget pages for the QStackedWidget."""
        self.page_none = QWidget()
        layout_none = QVBoxLayout(self.page_none)
        layout_none.addWidget(QLabel("No action will be triggered."))
        layout_none.addStretch()
        self.options_stack.addWidget(self.page_none)

        self.page_keyboard = QWidget()
        layout_keyboard = QVBoxLayout(self.page_keyboard)
        layout_keyboard.addWidget(QLabel("Select Key:"))
        self.key_combo = QComboBox()

        is_first_group = True
        for group_name, key_list in KEY_GROUPS:
            if not is_first_group:
                self.key_combo.insertSeparator(self.key_combo.count())
            else:
                is_first_group = False
            for display_name, key_value in key_list:
                 self.key_combo.addItem(display_name, userData=key_value)

        layout_keyboard.addWidget(self.key_combo)

        layout_keyboard.addWidget(QLabel("Select Modifiers (Optional):"))
        mod_layout = QHBoxLayout()
        mod_layout.setContentsMargins(0, 5, 0, 5)
        self.modifier_checkboxes = {}
        for display_name, key_value in MODIFIER_KEYS:
            checkbox = QCheckBox(display_name)
            self.modifier_checkboxes[key_value] = checkbox
            mod_layout.addWidget(checkbox)
        mod_layout.addStretch()
        layout_keyboard.addLayout(mod_layout)

        layout_keyboard.addStretch()
        self.options_stack.addWidget(self.page_keyboard)

        self.page_type_text = QWidget()
        layout_text = QVBoxLayout(self.page_type_text)
        layout_text.addWidget(QLabel("Enter text to type:"))
        self.text_input = QLineEdit()
        layout_text.addWidget(self.text_input)
        layout_text.addStretch()
        self.options_stack.addWidget(self.page_type_text)

    @pyqtSlot(str)
    def _on_category_changed(self, category_text):
        """Switches the visible page in the QStackedWidget."""
        index = self.categories.get(category_text, 0)
        self.options_stack.setCurrentIndex(index)

    def _set_initial_state(self, action_config):
        """ Sets the UI elements based on the currently configured action. """
        category_to_select = "None"
        page_index = self.categories[category_to_select]

        if isinstance(action_config, dict):
            action_type = action_config.get("type")
            action_value = action_config.get("value")

            if action_type == "press":
                category_to_select = "Keyboard Action"
                page_index = self.categories[category_to_select]
                key_index = self.key_combo.findData(action_value)
                if key_index >= 0: self.key_combo.setCurrentIndex(key_index)
                for checkbox in self.modifier_checkboxes.values(): checkbox.setChecked(False)

            elif action_type == "hotkey":
                category_to_select = "Keyboard Action"
                page_index = self.categories[category_to_select]
                keys = [k.strip() for k in action_value.split(',')]
                main_key = keys[-1]
                modifiers = keys[:-1]
                for mod_key, checkbox in self.modifier_checkboxes.items():
                    checkbox.setChecked(mod_key in modifiers)
                key_index = self.key_combo.findData(main_key)
                if key_index >= 0: self.key_combo.setCurrentIndex(key_index)

            elif action_type == "write":
                category_to_select = "Type Text"
                page_index = self.categories[category_to_select]
                self.text_input.setText(action_value or "")

        self.category_combo.setCurrentText(category_to_select)
        self.options_stack.setCurrentIndex(page_index)


    def accept(self):
        """Construct the action config based on UI state before accepting."""
        selected_category = self.category_combo.currentText()
        self.selected_action_config = None

        current_page_index = self.options_stack.currentIndex()

        if selected_category == "Keyboard Action":
            main_key_value = self.key_combo.currentData()
            if main_key_value:
                selected_modifiers = []
                for mod_key, checkbox in self.modifier_checkboxes.items():
                    if checkbox.isChecked():
                        selected_modifiers.append(mod_key)

                if not selected_modifiers:
                    self.selected_action_config = {"type": "press", "value": main_key_value}
                else:
                    hotkey_value = ",".join(selected_modifiers + [main_key_value])
                    self.selected_action_config = {"type": "hotkey", "value": hotkey_value}

        elif selected_category == "Type Text":
            text_value = self.text_input.text()
            if text_value:
                self.selected_action_config = {"type": "write", "value": text_value}

        print(f"Dialog closing. Constructed action config: {self.selected_action_config}")
        super().accept()

    def get_selected_action(self):
        """Returns the action dictionary constructed by the user's choices."""
        return self.selected_action_config
