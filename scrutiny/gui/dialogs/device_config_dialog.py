#    device_config_dialog.py
#        A dialog meant to change the link between the server and the device and its configuration.
#        Contains no app logic, has callback to integrate with an app.
#
#   - License : MIT - See LICENSE file.
#   - Project :  Scrutiny Debugger (github.com/scrutinydebugger/scrutiny-main)
#
#   Copyright (c) 2024 Scrutiny Debugger

__all__ = ['DeviceConfigDialog']

import logging
import traceback

from PySide6.QtWidgets import QDialog, QWidget, QComboBox, QVBoxLayout, QDialogButtonBox, QFormLayout, QLabel, \
    QPushButton, QLineEdit, QSpinBox
from PySide6.QtGui import QIntValidator, QDoubleValidator, QFontMetrics
from PySide6.QtCore import Qt

from scrutiny import sdk
from scrutiny.gui.widgets.validable_line_edit import ValidableLineEdit
from scrutiny.gui.widgets.feedback_label import FeedbackLabel
from scrutiny.gui.tools.validators import IpPortValidator, NotEmptyValidator
from scrutiny.gui.core.persistent_data import gui_persistent_data, AppPersistentData
from scrutiny.sdk import LinkUserInterfaceSpecification
from scrutiny.tools.typing import *


class BaseConfigPane(QWidget):
    def get_config(self) -> Optional[sdk.BaseLinkConfig]:
        raise NotImplementedError("abstract method")

    def load_config(self, config: Optional[sdk.BaseLinkConfig]) -> None:
        raise NotImplementedError("abstract method")

    def visual_validation(self) -> None:
        pass

    def commit_preferences(self) -> None:
        pass

    @classmethod
    def make_config_valid(self, config: Optional[sdk.BaseLinkConfig]) -> sdk.BaseLinkConfig:
        assert config is not None
        return config


class NoConfigPane(BaseConfigPane):
    def get_config(self) -> Optional[sdk.BaseLinkConfig]:
        return sdk.NoneLinkConfig()

    def load_config(self, config: Optional[sdk.BaseLinkConfig]) -> None:
        self.make_config_valid(config)


# class IPConfigPane(BaseConfigPane):
#     _hostname_textbox: ValidableLineEdit
#     _port_textbox: ValidableLineEdit
#
#     def __init__(self, parent: Optional[QWidget] = None) -> None:
#         super().__init__(parent)
#
#         form_layout = QFormLayout(self)
#         form_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
#
#         hostname_label = QLabel("Hostname: ")
#         port_label = QLabel("Port: ")
#         self._hostname_textbox = ValidableLineEdit(soft_validator=NotEmptyValidator())
#         self._port_textbox = ValidableLineEdit(hard_validator=QIntValidator(0, 0xFFFF), soft_validator=IpPortValidator())
#
#         # Make sure the red background disappear when we type (fixing the invalid content)
#         self._hostname_textbox.textChanged.connect(self._hostname_textbox.validate_expect_not_wrong_default_slot)
#         self._port_textbox.textChanged.connect(self._port_textbox.validate_expect_not_wrong_default_slot)
#
#         form_layout.addRow(hostname_label, self._hostname_textbox)
#         form_layout.addRow(port_label, self._port_textbox)
#
#     def get_port(self) -> Optional[int]:
#         port_txt = self._port_textbox.text()
#         state, _, _ = IpPortValidator().validate(port_txt, 0)
#         if state == IpPortValidator.State.Acceptable:
#             return int(port_txt)    # Should not fail
#         return None
#
#     def set_port(self, port: int) -> None:
#         port_txt = str(port)
#         state, _, _ = IpPortValidator().validate(port_txt, 0)
#         if state != IpPortValidator.State.Acceptable:
#             raise ValueError(f"Invalid port number: {port}")
#         self._port_textbox.setText(port_txt)
#
#     def get_hostname(self) -> str:
#         return self._hostname_textbox.text()
#
#     def set_hostname(self, hostname: str) -> None:
#         self._hostname_textbox.setText(hostname)
#
#     def visual_validation(self) -> None:
#         # Called when OK is clicked
#         self._port_textbox.validate_expect_valid()
#         self._hostname_textbox.validate_expect_valid()
#
#
# class TCPConfigPane(IPConfigPane):
#     def get_config(self) -> Optional[sdk.TCPLinkConfig]:
#         port = self.get_port()
#         if port is None:
#             return None
#
#         return sdk.TCPLinkConfig(
#             host=self.get_hostname(),
#             port=port,
#         )
#
#     def load_config(self, config: Optional[sdk.BaseLinkConfig]) -> None:
#         config = self.make_config_valid(config)
#         assert isinstance(config, sdk.TCPLinkConfig)
#         self.set_hostname(config.host)
#         self.set_port(config.port)
#
#     @classmethod
#     def make_config_valid(self, config: Optional[sdk.BaseLinkConfig]) -> sdk.BaseLinkConfig:
#         assert isinstance(config, sdk.TCPLinkConfig)
#         port = max(min(config.port, 0xFFFF), 0)
#         hostname = config.host
#         if len(hostname) == 0:
#             hostname = 'localhost'
#
#         return sdk.TCPLinkConfig(
#             host=hostname,
#             port=port
#         )
#
#
# class UDPConfigPane(IPConfigPane):
#     def get_config(self) -> Optional[sdk.UDPLinkConfig]:
#         port = self.get_port()
#         if port is None:
#             return None
#
#         return sdk.UDPLinkConfig(
#             host=self.get_hostname(),
#             port=port,
#         )
#
#     def load_config(self, config: Optional[sdk.BaseLinkConfig]) -> None:
#         config = self.make_config_valid(config)
#         assert isinstance(config, sdk.UDPLinkConfig)
#         self.set_hostname(config.host)
#         self.set_port(config.port)
#
#     @classmethod
#     def make_config_valid(self, config: Optional[sdk.BaseLinkConfig]) -> sdk.BaseLinkConfig:
#         assert isinstance(config, sdk.UDPLinkConfig)
#         port = max(min(config.port, 0xFFFF), 0)
#         hostname = config.host
#         if len(hostname) == 0:
#             hostname = 'localhost'
#
#         return sdk.UDPLinkConfig(
#             host=hostname,
#             port=port
#         )
#
#
# class SerialConfigPane(BaseConfigPane):
#     _port_name_textbox: ValidableLineEdit
#     _baudrate_textbox: ValidableLineEdit
#     _stopbits_combo_box: QComboBox
#     _databits_combo_box: QComboBox
#     _parity_combo_box: QComboBox
#     _start_delay_textbox: ValidableLineEdit
#
#     def __init__(self, parent: Optional[QWidget] = None) -> None:
#         super().__init__(parent)
#
#         layout = QFormLayout(self)
#         self._port_name_textbox = ValidableLineEdit(soft_validator=NotEmptyValidator())
#         self._baudrate_textbox = ValidableLineEdit(
#             hard_validator=QIntValidator(0, 0x7FFFFFFF),
#             soft_validator=NotEmptyValidator()
#         )
#         self._start_delay_textbox = ValidableLineEdit(
#             hard_validator=QDoubleValidator(0, 5, 2, self),
#             soft_validator=NotEmptyValidator()
#         )
#         self._stopbits_combo_box = QComboBox()
#         self._stopbits_combo_box.addItem("1", sdk.SerialLinkConfig.StopBits.ONE)
#         self._stopbits_combo_box.addItem("1.5", sdk.SerialLinkConfig.StopBits.ONE_POINT_FIVE)
#         self._stopbits_combo_box.addItem("2", sdk.SerialLinkConfig.StopBits.TWO)
#         self._stopbits_combo_box.setCurrentIndex(self._stopbits_combo_box.findData(sdk.SerialLinkConfig.StopBits.ONE))
#
#         self._databits_combo_box = QComboBox()
#         self._databits_combo_box.addItem("5", sdk.SerialLinkConfig.DataBits.FIVE)
#         self._databits_combo_box.addItem("6", sdk.SerialLinkConfig.DataBits.SIX)
#         self._databits_combo_box.addItem("7", sdk.SerialLinkConfig.DataBits.SEVEN)
#         self._databits_combo_box.addItem("8", sdk.SerialLinkConfig.DataBits.EIGHT)
#         self._databits_combo_box.setCurrentIndex(self._databits_combo_box.findData(sdk.SerialLinkConfig.DataBits.EIGHT))
#
#         self._parity_combo_box = QComboBox()
#         self._parity_combo_box.addItem("None", sdk.SerialLinkConfig.Parity.NONE)
#         self._parity_combo_box.addItem("Even", sdk.SerialLinkConfig.Parity.EVEN)
#         self._parity_combo_box.addItem("Odd", sdk.SerialLinkConfig.Parity.ODD)
#         self._parity_combo_box.addItem("Mark", sdk.SerialLinkConfig.Parity.MARK)
#         self._parity_combo_box.addItem("Space", sdk.SerialLinkConfig.Parity.SPACE)
#         self._parity_combo_box.setCurrentIndex(self._parity_combo_box.findData(sdk.SerialLinkConfig.Parity.NONE))
#
#         layout.addRow(QLabel("Port: "), self._port_name_textbox)
#         layout.addRow(QLabel("Baudrate: "), self._baudrate_textbox)
#         layout.addRow(QLabel("Stop bits: "), self._stopbits_combo_box)
#         layout.addRow(QLabel("Data bits: "), self._databits_combo_box)
#         layout.addRow(QLabel("Parity: "), self._parity_combo_box)
#         layout.addRow(QLabel("Start delay (sec): "), self._start_delay_textbox)
#
#         # Make sure the red background disappear when we type (fixing the invalid content)
#         self._port_name_textbox.textChanged.connect(self._port_name_textbox.validate_expect_not_wrong_default_slot)
#         self._baudrate_textbox.textChanged.connect(self._baudrate_textbox.validate_expect_not_wrong_default_slot)
#         self._start_delay_textbox.textChanged.connect(self._baudrate_textbox.validate_expect_not_wrong_default_slot)
#
#     def get_config(self) -> Optional[sdk.SerialLinkConfig]:
#         port = self._port_name_textbox.text()
#         baudrate_str = self._baudrate_textbox.text()
#         stopbits = cast(sdk.SerialLinkConfig.StopBits, self._stopbits_combo_box.currentData())
#         databits = cast(sdk.SerialLinkConfig.DataBits, self._databits_combo_box.currentData())
#         parity = cast(sdk.SerialLinkConfig.Parity, self._parity_combo_box.currentData())
#         try:
#             start_delay = float(self._start_delay_textbox.text())
#         except Exception:
#             return None
#
#         if len(port) == 0:
#             return None
#
#         try:
#             baudrate = int(baudrate_str)
#         except Exception:
#             return None
#
#         if baudrate < 0:
#             return None
#
#         return sdk.SerialLinkConfig(
#             port=port,
#             baudrate=baudrate,
#             stopbits=stopbits,
#             databits=databits,
#             parity=parity,
#             start_delay=start_delay
#         )
#
#     def load_config(self, config: Optional[sdk.BaseLinkConfig]) -> None:
#         config = self.make_config_valid(config)
#         assert isinstance(config, sdk.SerialLinkConfig)
#
#         self._port_name_textbox.setText(config.port)
#         self._baudrate_textbox.setText(str(config.baudrate))
#         self._stopbits_combo_box.setCurrentIndex(self._stopbits_combo_box.findData(config.stopbits))
#         self._databits_combo_box.setCurrentIndex(self._databits_combo_box.findData(config.databits))
#         self._parity_combo_box.setCurrentIndex(self._parity_combo_box.findData(config.parity))
#         self._start_delay_textbox.setText(str(config.start_delay))
#
#     @classmethod
#     def make_config_valid(self, config: Optional[sdk.BaseLinkConfig]) -> sdk.BaseLinkConfig:
#         assert isinstance(config, sdk.SerialLinkConfig)
#         return sdk.SerialLinkConfig(
#             port="<port>" if len(config.port) == 0 else config.port,
#             baudrate=max(config.baudrate, 1),
#             stopbits=config.stopbits,
#             databits=config.databits,
#             parity=config.parity,
#             start_delay=max(config.start_delay, 0)
#         )
#
#     def visual_validation(self) -> None:
#         # Called when OK is clicked
#         self._port_name_textbox.validate_expect_valid()
#         self._baudrate_textbox.validate_expect_valid()
#         self._start_delay_textbox.validate_expect_valid()
#
#
# class RTTConfigPane(BaseConfigPane):
#     _target_device_text_box: ValidableLineEdit
#     _jlink_interface_combo_box: QComboBox
#
#     def __init__(self, parent: Optional[QWidget] = None) -> None:
#         super().__init__(parent)
#
#         layout = QFormLayout(self)
#
#         self._target_device_text_box = ValidableLineEdit(soft_validator=NotEmptyValidator())
#         self._jlink_interface_combo_box = QComboBox()
#
#         self._jlink_interface_combo_box.addItem("SWD", sdk.RTTLinkConfig.JLinkInterface.SWD)
#         self._jlink_interface_combo_box.addItem("JTAG", sdk.RTTLinkConfig.JLinkInterface.JTAG)
#         self._jlink_interface_combo_box.addItem("ICSP", sdk.RTTLinkConfig.JLinkInterface.ICSP)
#         self._jlink_interface_combo_box.addItem("FINE", sdk.RTTLinkConfig.JLinkInterface.FINE)
#         self._jlink_interface_combo_box.addItem("SPI", sdk.RTTLinkConfig.JLinkInterface.SPI)
#         self._jlink_interface_combo_box.addItem("C2", sdk.RTTLinkConfig.JLinkInterface.C2)
#
#         layout.addRow(QLabel("Interface: "), self._jlink_interface_combo_box)
#         layout.addRow(QLabel("Target Device: "), self._target_device_text_box)
#
#         # Make sure the red background disappear when we type (fixing the invalid content)
#         self._target_device_text_box.textChanged.connect(self._target_device_text_box.validate_expect_not_wrong_default_slot)
#
#     def get_config(self) -> Optional[sdk.RTTLinkConfig]:
#         target_device = self._target_device_text_box.text()
#         interface = cast(sdk.RTTLinkConfig.JLinkInterface, self._jlink_interface_combo_box.currentData())
#
#         if len(target_device) == 0:
#             return None
#
#         return sdk.RTTLinkConfig(
#             target_device=target_device,
#             jlink_interface=interface
#         )
#
#     def load_config(self, config: Optional[sdk.BaseLinkConfig]) -> None:
#         config = self.make_config_valid(config)
#         assert isinstance(config, sdk.RTTLinkConfig)
#
#         self._target_device_text_box.setText(config.target_device)
#         self._jlink_interface_combo_box.setCurrentIndex(self._jlink_interface_combo_box.findData(config.jlink_interface))
#
#     @classmethod
#     def make_config_valid(self, config: Optional[sdk.BaseLinkConfig]) -> sdk.BaseLinkConfig:
#         assert isinstance(config, sdk.RTTLinkConfig)
#         return sdk.RTTLinkConfig(
#             target_device="<device>" if len(config.target_device) else config.target_device,
#             jlink_interface=config.jlink_interface
#         )
#
#     def visual_validation(self) -> None:
#         # Called when OK is clicked
#         self._target_device_text_box.validate_expect_valid()
#


class ConfigForm(BaseConfigPane):
    _preferences: AppPersistentData

    def __init__(self, name: str, config : sdk.LinkUserInterfaceSpecification, parent=None):
        super().__init__(parent)

        layout = QFormLayout(self)

        self._preferences = gui_persistent_data.get_namespace(self.__class__.__name__ + '.' + name)

        self.fields = {}  # Store widgets by param name

        for field in config.fields:
            widget = self._create_widget_for_param(field, config.fields[field])
            if widget:
                layout.addRow(QLabel(config.fields[field].description), widget)
                self.fields[field] = widget

    @staticmethod
    def set_combo_box_width_to_longest_item(combo: QComboBox):
        fm = QFontMetrics(combo.font())
        max_text_width = max(fm.horizontalAdvance(combo.itemText(i)) for i in range(combo.count()))
        combo.setMinimumWidth(max_text_width + 30)  # Add padding for arrow etc.

    def commit_preferences(self) -> None:
        all_preference_keys = list[self.fields.keys()]

        self._preferences.prune(all_preference_keys)    # Remove extra keys

        for field_name in self.fields:
            widget = self.fields[field_name]
            if type(widget) is QLineEdit:
                self._preferences.set(field_name, widget.text())
            elif type(widget) is QSpinBox:
                self._preferences.set(field_name, widget.value())
            elif type(widget) is QComboBox:
                self._preferences.set(field_name, widget.currentText())
            else:
                pass




    def _create_widget_for_param(self, name, info:sdk.LinkUserInterfaceField):
        param_type = info.type
        default = info.default

        if param_type == sdk.LinkUserInterfaceFieldTypes.TEXT:
            widget = QLineEdit()
            widget.setText(self._preferences.get_str(name, default))
            return widget

        elif param_type == sdk.LinkUserInterfaceFieldTypes.INTEGER:
            widget = QSpinBox()
            if info.max_value is not None and info.min_value is not None:
                widget.setRange(info.min_value , info.max_value)
            widget.setValue(self._preferences.get_int(name, int(default)))
            # widget.setMinimumWidth(80)
            return widget

        elif param_type == sdk.LinkUserInterfaceFieldTypes.EDITABLE_SELECTOR or param_type == sdk.LinkUserInterfaceFieldTypes.FIXED_SELECTOR:
            values = info.options
            editable =  False if param_type == sdk.LinkUserInterfaceFieldTypes.FIXED_SELECTOR else True

            widget = QComboBox()
            widget.setEditable(editable)
            widget.addItems([str(v) for v in values])
            self.set_combo_box_width_to_longest_item(widget)
            widget.setCurrentText(str(self._preferences.get(name, default)))
            return widget

        return None

    def get_config(self):
        result = {}
        for name, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                result[name] = widget.text()
            elif isinstance(widget, QSpinBox):
                result[name] = widget.value()
            elif isinstance(widget, QComboBox):
                result[name] = widget.currentText()
        return sdk.DynamicLinkConfig(**result)


    def load_config(self, config_object) -> None:
        for name, widget in self.fields.items():
            if not hasattr(config_object, name):
                continue
            value = getattr(config_object, name)

            if isinstance(widget, QLineEdit):
                widget.setText(str(value))

            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value))

            elif isinstance(widget, QComboBox):
                str_value = str(value)
                if str_value not in [widget.itemText(i) for i in range(widget.count())]:
                    widget.addItem(str_value)
                widget.setCurrentText(str_value)

    def visual_validation(self) -> None:
        # todo: fix visual validation
        pass

class DeviceConfigDialog(QDialog):


    _link_type_combo_box: QComboBox
    _config_container: QWidget
    _configs: Dict[str, sdk.BaseLinkConfig]
    _active_pane: BaseConfigPane
    _apply_callback: Optional[Callable[["DeviceConfigDialog"], None]]
    _feedback_label: FeedbackLabel
    _btn_ok: QPushButton
    _btn_cancel: QPushButton

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 apply_callback: Optional[Callable[["DeviceConfigDialog"], None]] = None
                 ) -> None:
        super().__init__(parent)
        self.setModal(True)
        self._apply_callback = apply_callback
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setMinimumWidth(300)
        vlayout = QVBoxLayout(self)

        # Combobox at the top
        self._link_type_combo_box = QComboBox()

        # Bottom part that changes based on combo box selection
        self._config_container = QWidget()
        self._config_container.setLayout(QVBoxLayout())

        # A feed
        self._feedback_label = FeedbackLabel()
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._btn_ok_click)
        buttons.rejected.connect(self._btn_cancel_click)

        vlayout.addWidget(self._link_type_combo_box)
        vlayout.addWidget(self._config_container)
        vlayout.addWidget(self._feedback_label)
        vlayout.addWidget(buttons)

        self._btn_ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._btn_cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)

        self._configs = {}
        # Preload some default configs to avoid having a blank form


        self._link_type_combo_box.currentIndexChanged.connect(self._combobox_changed)
        self._active_pane = NoConfigPane()

        self._current_link_options = []

    def set_link_options(self, config):
        self._link_type_combo_box.clear()
        self._current_link_options = {}
        self._configs =         {}
        if config is not None:
            for option in config:
                self._current_link_options[option] = config[option]
                self._configs[option]  = sdk.BaseLinkConfig()
                self._link_type_combo_box.addItem(option)

    def _get_selected_link_type(self) -> sdk.DeviceLinkType:
        return self._link_type_combo_box.currentText()

    def _combobox_changed(self) -> None:
        link_type = self._get_selected_link_type()
        self._rebuild_config_layout(link_type)

    def _rebuild_config_layout(self, link_type: sdk.DeviceLinkType) -> None:
        """Change the variable part of the dialog based on the type of link the user wants."""

        for pane in self._config_container.children():
            if isinstance(pane, BaseConfigPane):
                pane.setParent(None)
                pane.deleteLater()

        if link_type in self._configs:
            # get index by name
            self._active_pane = ConfigForm(link_type, self._current_link_options[link_type])
            layout = self._config_container.layout()
            layout.addWidget(self._active_pane)

            self.window().adjustSize()
            self.adjustSize()

    def _btn_ok_click(self) -> None:
        link_type = self._get_selected_link_type()
        config = self._active_pane.get_config()
        self._active_pane.visual_validation()
        # if config is None, it is invalid. Don't close and expect the user to fix
        if config is not None:
            self._configs[link_type] = config
            self._btn_ok.setEnabled(False)
            self._set_waiting_status()
            self._active_pane.commit_preferences()
            if self._apply_callback is not None:
                self._apply_callback(self)

    def change_fail_callback(self, error: str) -> None:
        """To be called to confirm a device link change fails"""
        self._set_error_status(error)
        self._btn_ok.setEnabled(True)

    def change_success_callback(self) -> None:
        """To be called to confirm a device link change succeeded"""
        self._clear_status()
        self._btn_ok.setEnabled(True)
        self.close()

    def _clear_status(self) -> None:
        self._feedback_label.clear()

    def _set_error_status(self, error: str) -> None:
        self._feedback_label.set_error(error)

    def _set_waiting_status(self) -> None:
        self._feedback_label.set_info("Waiting for the server...")

    def _btn_cancel_click(self) -> None:
        # Reload to the UI the config that is saved
        config = self._configs[self._get_selected_link_type()]
        self._active_pane.load_config(config)   # Should not raise. This config was there before.
        self._clear_status()
        self.close()

    def set_config(self, link_type: sdk.DeviceLinkType, config: sdk.BaseLinkConfig) -> None:
        """Set the config for a given link type. 
        This config will be displayed when the user select the given link type"""
        if link_type not in self._configs:
            raise ValueError("Unsupported config type")

        valid_config = ConfigForm(link_type, self._current_link_options[link_type]).make_config_valid(config)
        self._configs[link_type] = valid_config

    def get_type_and_config(self) -> Tuple[sdk.DeviceLinkType, Optional[sdk.BaseLinkConfig]]:
        """Return the device link configuration selected by the user"""
        link_type = self._get_selected_link_type()
        config = self._active_pane.get_config()
        return (link_type, config)

    def swap_config_pane(self, link_type: sdk.DeviceLinkType) -> None:
        """Reconfigure the dialog for a new device type. Change the combo box value + reconfigure the variable part"""
        combobox_index = self._link_type_combo_box.findData(link_type)
        if combobox_index < 0:
            raise ValueError(f"Given link type not in the combobox {link_type}")
        self._link_type_combo_box.setCurrentIndex(combobox_index)   # Will trgger "currentIndexChanged"
