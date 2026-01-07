import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QComboBox,
    QLabel,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QHBoxLayout,
    QGroupBox,
    QLineEdit,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QTabWidget,
    QStackedLayout,
    QProgressBar,
    QMessageBox,
)

from app.core.constants import PROJECT_ROOT, OUT_FOLDER
from app.core.file_processor import FileProcessor

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Zelda64 Sample Creator')
        self.setFixedSize(self.sizeHint())

        # Initialize data containers
        self.instrument_data = None
        self.drum_data = None
        self.effect_data = None

        # Initialize file processor var
        self.f_processor = None

        main_layout = QVBoxLayout()

        # Instrument type controls
        self.type_group = QGroupBox('Instrument Type')
        type_layout = QHBoxLayout(self.type_group)
        type_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        type_layout.setSpacing(24)

        self.instrument_radio = QRadioButton('Instrument')
        self.drum_radio = QRadioButton('Drum')
        self.effect_radio = QRadioButton('Sound Effect')

        self.instrument_radio.setChecked(True)
        self.instrument_radio.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.drum_radio.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.effect_radio.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.radio_group = QButtonGroup(self)
        self.radio_group.addButton(self.instrument_radio)
        self.radio_group.addButton(self.drum_radio)
        self.radio_group.addButton(self.effect_radio)

        self.instrument_radio.toggled.connect(lambda checked: checked and self.on_type_changed('Instrument'))
        self.drum_radio.toggled.connect(lambda checked: checked and self.on_type_changed('Drum'))
        self.effect_radio.toggled.connect(lambda checked: checked and self.on_type_changed('Sound Effect'))

        type_layout.addWidget(self.instrument_radio)
        type_layout.addWidget(self.drum_radio)
        type_layout.addWidget(self.effect_radio)

        # Instrument Settings
        self.instrument_settings_group = QGroupBox()
        self.instrument_settings_stack = QStackedLayout()
        self.instrument_settings_group.setLayout(
            self.instrument_settings_stack)

        # Initialize instrument settings for each instrument type
        self.instrument_controls = self._init_instrument_controls()
        self.drum_controls = self._init_drum_controls()
        self.effect_controls = self._init_effect_controls()

        # Create sample paths dictionary
        self.sample_paths = {
            'Low': self.low_sample_path_edit,
            'Prim': self.prim_sample_path_edit,
            'High': self.high_sample_path_edit,
            'Drum': self.drum_sample_path_edit,
            'Effect': self.effect_sample_path_edit
        }

        # Add widgets to the stack
        for widget in [self.instrument_controls, self.drum_controls, self.effect_controls]:
            self.instrument_settings_stack.addWidget(widget)

        # Tuning Information
        self.tuning_info_group = QGroupBox('Tuning Information')
        tuning_info_layout = QVBoxLayout()
        self.tuning_info_group.setLayout(tuning_info_layout)

        self.auto_detect_tuning_checkbox = QCheckBox('Auto-detect')
        self.auto_detect_tuning_checkbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tuning_info_layout.addWidget(self.auto_detect_tuning_checkbox)

        self.tuning_tabs = QTabWidget()
        tuning_info_layout.addWidget(self.tuning_tabs)

        self.tuning_fields_by_tab = []

        for name in ['Low', 'Primary', 'High']:
            tab, fields = self._create_tuning_tab(selected_type='Instrument')
            self.tuning_tabs.addTab(tab, name)
            self.tuning_fields_by_tab.append(fields)

        self.tuning_tabs.setCurrentIndex(1)
        self._update_tab_enabled_States()

        self.auto_detect_tuning_checkbox.toggled.connect(lambda checked: self._toggle_all_tuning_fields(checked, self.current_type))

        tuning_info_layout.setSpacing(16)
        self.tuning_info_group.setLayout(tuning_info_layout)

        self.generate_group = QHBoxLayout()
        self.generate_group.setContentsMargins(0, 12, 0, 0)
        # self.generate_group.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Progress Bar
        # self.progress_bar = QProgressBar()
        # self.progress_bar.setMinimum(0)
        # self.progress_bar.setMaximum(100)
        # self.progress_bar.setValue(0)
        # self.generate_group.addWidget(self.progress_bar)

        # Create Sample Button
        self.create_sample_button = create_push_button('Create Sample')
        self.create_sample_button.clicked.connect(self.on_create_sample_clicked)
        self.generate_group.addWidget(self.create_sample_button)

        # Add widgets to main layout
        main_layout.addWidget(self.type_group)
        main_layout.addWidget(self.instrument_settings_group)
        main_layout.addWidget(self.tuning_info_group)
        main_layout.addLayout(self.generate_group)

        self.setLayout(main_layout)
        self.on_type_changed('Instrument')

    def on_type_changed(self, selected_type):
        self.current_type = selected_type
        self.instrument_settings_group.setTitle(selected_type + ' Settings')
        self.tuning_tabs.clear()
        self.tuning_fields_by_tab.clear()

        for edit in self.sample_paths.values():
            edit.clear()

        self.low_sample_checkbox.setChecked(False)
        self.high_sample_checkbox.setChecked(False)

        if selected_type == 'Instrument':
            self.instrument_settings_stack.setCurrentWidget(
                self.instrument_controls)

            for name in ['Low Sample Tuning', 'Prim Sample Tuning', 'High Sample Tuning']:
                tab, fields = self._create_tuning_tab(selected_type)
                self.tuning_tabs.addTab(tab, name)
                self.tuning_fields_by_tab.append(fields)

            self.tuning_tabs.setCurrentIndex(1)
            self._update_tab_enabled_States()

        elif selected_type == 'Drum':
            self.instrument_settings_stack.setCurrentWidget(self.drum_controls)

            tab, fields = self._create_tuning_tab(selected_type)
            self.tuning_tabs.addTab(tab, 'Sample Tuning')
            self.tuning_fields_by_tab.append(fields)
            self.tuning_tabs.setCurrentIndex(0)

        elif selected_type == 'Sound Effect':
            self.instrument_settings_stack.setCurrentWidget(
                self.effect_controls)

            tab, fields = self._create_tuning_tab(selected_type)
            self.tuning_tabs.addTab(tab, "Sample Tuning")
            self.tuning_fields_by_tab.append(fields)
            self.tuning_tabs.setCurrentIndex(0)

        self._toggle_all_tuning_fields(
            self.auto_detect_tuning_checkbox.isChecked(), selected_type)

    def _select_file(self, label):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f'Select {label} sample', '', 'WAV Files (*.wav)')

        if file_path and label in self.sample_paths:
            self.sample_paths[label].setText(file_path)

    def _create_tuning_tab(self, selected_type):
        container = QWidget()
        layout = QVBoxLayout(container)

        sample_rate_layout, sample_rate_edit = create_labeled_spinbox('Sample Rate:', 0, 999999, 32000)

        if selected_type == 'Drum' or selected_type == 'Sound Effect':
            root_key_layout, root_key_edit = create_labeled_spinbox('Root Key:', 0, 127, 60, enabled=False)
        else:
            root_key_layout, root_key_edit = create_labeled_spinbox('Root Key:', 0, 127, 60)

        coarse_tune_layout, coarse_tune_edit = create_labeled_spinbox('Coarse Tune:', -127, 127, 0)
        fine_tune_layout, fine_tune_edit = create_labeled_spinbox('Fine Tune:', -100, 100, 0)

        fine_tune_edit.valueChanged.connect(lambda val, ct=coarse_tune_edit, ft=fine_tune_edit: self._fine_tune_wrapping(val, ct, ft))

        # Row 1
        row1 = QHBoxLayout()
        row1.addLayout(sample_rate_layout)
        row1.addLayout(root_key_layout)
        row1.setSpacing(8)

        # Row 2
        row2 = QHBoxLayout()
        row2.addLayout(coarse_tune_layout)
        row2.addLayout(fine_tune_layout)
        row2.setSpacing(8)

        for row in [row1, row2]:
            layout.addLayout(row)

        return container, {
            'sample_rate': sample_rate_edit,
            'root_key': root_key_edit,
            'coarse_tune': coarse_tune_edit,
            'fine_tune': fine_tune_edit
        }

    def _fine_tune_wrapping(self, value, coarse_tune_edit, fine_tune_edit):
        if value >= 100:
            fine_tune_edit.blockSignals(True)
            fine_tune_edit.setValue(0)
            fine_tune_edit.blockSignals(False)
            coarse_tune_edit.setValue(coarse_tune_edit.value() + 1)
        elif value <= -100:
            fine_tune_edit.blockSignals(True)
            fine_tune_edit.setValue(0)
            fine_tune_edit.blockSignals(False)
            coarse_tune_edit.setValue(coarse_tune_edit.value() - 1)

    def _toggle_all_tuning_fields(self, checked, selected_type=None):
        for fields in self.tuning_fields_by_tab:
            for name, field in fields.items():
                if selected_type in ('Drum', 'Sound Effect') and name == 'root_key':
                    field.setEnabled(False)
                else:
                    field.setEnabled(not checked)

    def _update_tab_enabled_States(self):
        states = [
            self.low_sample_checkbox.isChecked(),
            True,  # Primary is always enabled
            self.high_sample_checkbox.isChecked()
        ]

        for i, enabled in enumerate(states):
            self.tuning_tabs.setTabEnabled(i, enabled)

    def _init_instrument_controls(self) -> QWidget:
        container = QWidget()

        self.key_range_min_layout, self.key_range_min_spin = create_labeled_spinbox('Key Region Low:', 0, 127, 0, width=100)
        self.key_range_max_layout, self.key_range_max_spin = create_labeled_spinbox('Key Region High:', 0, 127, 127, width=100)
        self.instrument_decay_index_layout, self.instrument_decay_index_spin = create_labeled_spinbox('Decay Index:', 0, 255, 240, width=100)

        parameter_row = QHBoxLayout()
        # parameter_row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        parameter_row.setContentsMargins(0, 0, 0, 8)
        parameter_row.setSpacing(24)
        for param in [self.key_range_min_layout, self.key_range_max_layout, self.instrument_decay_index_layout]:
            # param.setContentsMargins(0,0, 12, 0)
            parameter_row.addLayout(param)

        # Instrument sample selectors
        self.low_sample_checkbox = create_checkbox('Low Sample')
        self.low_sample_checkbox.stateChanged.connect(lambda state: self.low_sample_file_button.setEnabled(state == 2))
        self.low_sample_checkbox.stateChanged.connect(lambda _: self._update_tab_enabled_States())

        self.prim_sample_checkbox = create_checkbox('Prim Sample', checked=True, enabled=False)
        # self.prim_sample_checkbox.stateChanged.connect(lambda state: self.prim_file_button.setEnabled(state == 2))
        # self.prim_sample_checkbox.stateChanged.connect(lambda _: self._update_tab_enabled_States())

        self.high_sample_checkbox = create_checkbox('High Sample')
        self.high_sample_checkbox.stateChanged.connect(lambda state: self.high_sample_file_button.setEnabled(state == 2))
        self.high_sample_checkbox.stateChanged.connect(lambda _: self._update_tab_enabled_States())

        checkbox_row = QHBoxLayout()
        checkbox_row.setSpacing(24)
        checkbox_row.setAlignment(Qt.AlignmentFlag.AlignRight)

        for checkbox in [self.low_sample_checkbox, self.prim_sample_checkbox, self.high_sample_checkbox]:
            checkbox_row.addWidget(checkbox)

        parameter_row.addLayout(checkbox_row)

        # Low sample dialog
        self.low_sample_file_button = create_push_button('Select Low Sample', enabled=False)
        self.low_sample_path_edit = create_line_edit(min_width=592, read_only=True, focus_policy=Qt.FocusPolicy.NoFocus)
        self.low_sample_file_button.clicked.connect(lambda: self._select_file('Low'))

        # Prim sample dialog
        self.prim_sample_file_button = create_push_button('Select Prim Sample')
        self.prim_sample_path_edit = create_line_edit(min_width=592, read_only=True, focus_policy=Qt.FocusPolicy.NoFocus)
        self.prim_sample_file_button.clicked.connect(lambda: self._select_file('Prim'))

        # High sample dialog
        self.high_sample_file_button = create_push_button('Select High Sample', enabled=False)
        self.high_sample_path_edit = create_line_edit(min_width=592, read_only=True, focus_policy=Qt.FocusPolicy.NoFocus)
        self.high_sample_file_button.clicked.connect(lambda: self._select_file('High'))

        layout = QVBoxLayout(container)
        layout.addLayout(parameter_row)
        # layout.addLayout(checkbox_row)
        for path_edit, file_button in [
            (self.low_sample_path_edit,  self.low_sample_file_button),
            (self.prim_sample_path_edit, self.prim_sample_file_button),
            (self.high_sample_path_edit, self.high_sample_file_button)
        ]:
            layout.addLayout(self._make_file_row(path_edit, file_button))

        return container

    def _init_drum_controls(self) -> QWidget:
        container = QWidget()

        self.drum_decay_index_layout, self.drum_decay_index_spin = create_labeled_spinbox('Decay Index:', 0, 255, 240, width=100)
        self.drum_pan_layout, self.drum_pan_spin = create_labeled_spinbox('Pan:', 0, 127, 64, width=100)

        parameter_row = QHBoxLayout()
        # parameter_row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        parameter_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        parameter_row.setContentsMargins(0, 0, 0, 8)
        parameter_row.setSpacing(24)

        for param in [self.drum_decay_index_layout, self.drum_pan_layout]:
            # param.setContentsMargins(0,0, 12, 0)
            parameter_row.addLayout(param)

        # Drum sample dialog
        self.drum_sample_file_button = create_push_button('Select Drum Sample')
        self.drum_sample_path_edit = create_line_edit(min_width=592, read_only=True, focus_policy=Qt.FocusPolicy.NoFocus)
        self.drum_sample_file_button.clicked.connect(lambda: self._select_file('Drum'))

        layout = QVBoxLayout(container)
        layout.addLayout(parameter_row)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addLayout(self._make_file_row(self.drum_sample_path_edit, self.drum_sample_file_button))

        return container

    def _init_effect_controls(self) -> QWidget:
        container = QWidget()

        # Effect sample dialog
        self.effect_sample_file_button = create_push_button('Select Effect Sample')
        self.effect_sample_path_edit = create_line_edit(min_width=592, read_only=True, focus_policy=Qt.FocusPolicy.NoFocus)
        self.effect_sample_file_button.clicked.connect(lambda: self._select_file('Effect'))

        layout = QVBoxLayout(container)
        layout.addLayout(self._make_file_row(self.effect_sample_path_edit, self.effect_sample_file_button))

        return container

    def _make_file_row(self, line_edit, button) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(line_edit)
        row.addWidget(button)
        return row

    def _collect_sample_data(self) -> None:
        from app.core.models import InstrumentData, DrumData, EffectData, SampleData, AudioSample
        if self.current_type == 'Instrument':
            if self.instrument_data is None:
                self.instrument_data = InstrumentData()

            # TODO: Make a name input
            self.instrument_data.name = 'Instrument'

            # Set checkbox data
            self.instrument_data.auto_detect_pitch = self.auto_detect_tuning_checkbox.isChecked()
            self.instrument_data.use_low_sample = self.low_sample_checkbox.isChecked()
            self.instrument_data.use_high_sample = self.high_sample_checkbox.isChecked()

            # Set instrument parameters
            self.instrument_data.key_region_low = self.key_range_min_spin.value()
            self.instrument_data.key_region_high = self.key_range_max_spin.value()
            self.instrument_data.decay_index = self.instrument_decay_index_spin.value()

            # Low sample data
            if self.instrument_data.use_low_sample:
                if self.instrument_data.low_sample is None:
                    self.instrument_data.low_sample = SampleData()

                # File path
                self.instrument_data.low_sample.path = self.low_sample_path_edit.text()

                # Tuning information
                self.instrument_data.low_sample.sample_rate = self.tuning_fields_by_tab[0]['sample_rate'].value()
                self.instrument_data.low_sample.root_key = self.tuning_fields_by_tab[0]['root_key'].value()
                self.instrument_data.low_sample.coarse_tune = self.tuning_fields_by_tab[0]['coarse_tune'].value()
                self.instrument_data.low_sample.fine_tune = self.tuning_fields_by_tab[0]['fine_tune'].value()
            else:
                self.instrument_data.low_sample = None

            # Prim sample data
            if self.instrument_data.prim_sample is None:
                self.instrument_data.prim_sample = SampleData()

            # File path
            self.instrument_data.prim_sample.path = self.prim_sample_path_edit.text()

            # Tuning information
            self.instrument_data.prim_sample.sample_rate = self.tuning_fields_by_tab[1]['sample_rate'].value()
            self.instrument_data.prim_sample.root_key = self.tuning_fields_by_tab[1]['root_key'].value()
            self.instrument_data.prim_sample.coarse_tune = self.tuning_fields_by_tab[1]['coarse_tune'].value()
            self.instrument_data.prim_sample.fine_tune = self.tuning_fields_by_tab[1]['fine_tune'].value()

            # High sample data
            if self.instrument_data.use_high_sample:
                if self.instrument_data.high_sample is None:
                    self.instrument_data.high_sample = SampleData()

                # File path
                self.instrument_data.high_sample.path = self.high_sample_path_edit.text()

                # Tuning information
                self.instrument_data.high_sample.sample_rate = self.tuning_fields_by_tab[2]['sample_rate'].value()
                self.instrument_data.high_sample.root_key = self.tuning_fields_by_tab[2]['root_key'].value()
                self.instrument_data.high_sample.coarse_tune = self.tuning_fields_by_tab[2]['coarse_tune'].value()
                self.instrument_data.high_sample.fine_tune = self.tuning_fields_by_tab[2]['fine_tune'].value()
            else:
                self.instrument_data.high_sample = None

        elif self.current_type == 'Drum':
            if self.drum_data is None:
                self.drum_data = DrumData()

            # TODO: Make a name input
            self.drum_data.name = 'Drum'

            # Set checkbox data
            self.drum_data.auto_detect_pitch = self.auto_detect_tuning_checkbox.isChecked()

            # Set drum parameters
            self.drum_data.decay_index = self.drum_decay_index_spin.value()
            self.drum_data.pan = self.drum_pan_spin.value()

            # Set sample path
            self.drum_data.sample.path = self.drum_sample_path_edit.text()

            # Set drum sample tuning data
            self.drum_data.sample.sample_rate = self.tuning_fields_by_tab[0]['sample_rate'].value()
            self.drum_data.sample.root_key = 60
            self.drum_data.sample.coarse_tune = self.tuning_fields_by_tab[0]['coarse_tune'].value()
            self.drum_data.sample.fine_tune = self.tuning_fields_by_tab[0]['fine_tune'].value()

        elif self.current_type == 'Sound Effect':
            if self.effect_data is None:
                self.effect_data = EffectData()

            # TODO: Make a name input
            self.effect_data.name = 'Effect'

            # Set checkbox data
            self.effect_data.auto_detect_pitch = self.auto_detect_tuning_checkbox.isChecked()

            # Set sample path
            self.effect_data.sample.path = self.effect_sample_path_edit.text()

            # Set effect sample tuning data
            self.effect_data.sample.sample_rate = self.tuning_fields_by_tab[0]['sample_rate'].value()
            self.effect_data.sample.root_key = 60
            self.effect_data.sample.coarse_tune = self.tuning_fields_by_tab[0]['coarse_tune'].value()
            self.effect_data.sample.fine_tune = self.tuning_fields_by_tab[0]['fine_tune'].value()

    def on_create_sample_clicked(self):
        # Check for missing file paths, and if there are any then throw an error message
        missing_paths = []
        if self.current_type == 'Instrument':
            if self.low_sample_checkbox.isChecked() and not self.low_sample_path_edit.text():
                missing_paths.append('Low Sample')
            if not self.prim_sample_path_edit.text():
                missing_paths.append('Prim Sample')
            if self.high_sample_checkbox.isChecked() and not self.high_sample_path_edit.text():
                missing_paths.append('High Sample')
        elif self.current_type == 'Drum':
            if not self.drum_sample_path_edit.text():
                missing_paths.append('Drum Sample')
        elif self.current_type == 'Sound Effect':
            if not self.effect_sample_path_edit.text():
                missing_paths.append('Effect Sample')

        if missing_paths:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            error_txt = (
                'Missing sample path(s).\n\n'
                'Please select a sample file for the following samples:'
                + '\n• ' + '\n• '.join(missing_paths)
            )

            msg.setText(error_txt)
            msg.setWindowTitle('Error')
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            return

        self._collect_sample_data()

        if self.current_type == 'Instrument':
            self.f_processor = FileProcessor(PROJECT_ROOT, OUT_FOLDER, self.instrument_data)
        elif self.current_type == 'Drum':
            self.f_processor = FileProcessor(PROJECT_ROOT, OUT_FOLDER, self.drum_data)
        elif self.current_type == 'Sound Effect':
            self.f_processor = FileProcessor(PROJECT_ROOT, OUT_FOLDER, self.effect_data)

        try:
            self.f_processor.process_files()
        except Exception as ex:
            tb_str = traceback.format_exc()
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setWindowTitle('Processing error')
            error_msg.setText(f'An error occurred while creating the sample:\n\n{ex}')
            error_msg.setDetailedText(tb_str)
            error_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            error_msg.exec()
            return

        # Success dialog
        success_msg = QMessageBox(self)
        success_msg.setIcon(QMessageBox.Icon.NoIcon)
        success_txt = (
            'Custom audio sample created successfully!\n\n'
            'The sample file and its instrument bank file can be found in the output folder.'
        )
        success_msg.setText(success_txt)
        success_msg.setWindowTitle('Success')
        success_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        success_msg.exec()

# GUI Creation Helpers


def create_checkbox(label: str, *, checked: bool = False, enabled: bool = True, focus_policy=Qt.FocusPolicy.NoFocus) -> QCheckBox:
    cb = QCheckBox(label)
    cb.setChecked(checked)
    cb.setEnabled(enabled)
    cb.setFocusPolicy(focus_policy)
    return cb


def create_push_button(text: str, *, fixed_width: int = 200, enabled: bool = True, focus_policy=Qt.FocusPolicy.NoFocus) -> QPushButton:
    pb = QPushButton(text)
    pb.setFixedWidth(fixed_width)
    pb.setEnabled(enabled)
    pb.setFocusPolicy(focus_policy)
    return pb


def create_line_edit(*, min_width: int = 200, read_only: bool = False, enabled: bool = True, focus_policy=Qt.FocusPolicy.ClickFocus) -> QLineEdit:
    le = QLineEdit()
    le.setMinimumWidth(min_width)
    le.setEnabled(enabled)
    le.setReadOnly(read_only)
    le.setFocusPolicy(focus_policy)
    return le


def create_labeled_spinbox(label_text, min_val, max_val, default, enabled: bool = True, width=None):
    label = QLabel(label_text, textFormat=Qt.TextFormat.MarkdownText)
    spin = QSpinBox(minimum=min_val, maximum=max_val, value=default)
    if width:
        spin.setFixedWidth(width)
    spin.setEnabled(enabled)
    spin.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
    spin.editingFinished.connect(spin.clearFocus)
    box = QVBoxLayout()
    box.setSpacing(4)
    box.addWidget(label)
    box.addWidget(spin)

    return box, spin
