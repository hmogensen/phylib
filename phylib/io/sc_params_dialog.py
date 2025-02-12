from PyQt5.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QLabel, QLineEdit, QPushButton, 
                           QDialogButtonBox)
from PyQt5.QtCore import Qt
import numpy as np

class ParameterWidget(QWidget):
    def __init__(self, param_name: str, value, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        label = QLabel(param_name.replace('_', ' ').title())
        label.setMinimumWidth(150)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label)
        
        self.value_edit = QLineEdit(str(value))
        self.value_edit.setMinimumWidth(100)
        layout.addWidget(self.value_edit)

        layout.setContentsMargins(0, 0, 0, 0)
        
        self.original_type = type(value)
        if isinstance(value, (np.int32, np.int64)):
            self.original_type = int
        elif isinstance(value, (np.float32, np.float64)):
            self.original_type = float
            
    def get_value(self):
        try:
            return self.original_type(self.value_edit.text())
        except ValueError:
            raise ValueError(f"Invalid value for {self.label.text()}")

class ComponentTab(QWidget):
    def __init__(self, component, parent=None):
        super().__init__(parent)
        self.component = component
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.param_widgets = {}
        for param_name, value in self.component.__dict__.items():
            if param_name != 'hlt_frange':  # Special handling for numpy array
                widget = ParameterWidget(param_name, value)
                self.param_widgets[param_name] = widget
                layout.addWidget(widget)
                
        # Special handling for hlt_frange if it exists
        if hasattr(self.component, 'hlt_frange'):
            frange = self.component.hlt_frange
            start_widget = ParameterWidget('frange_start', frange[0])
            stop_widget = ParameterWidget('frange_stop', frange[-1])
            length_widget = ParameterWidget('frange_length', len(frange))
            
            self.param_widgets['frange_start'] = start_widget
            self.param_widgets['frange_stop'] = stop_widget
            self.param_widgets['frange_length'] = length_widget
            
            layout.addWidget(start_widget)
            layout.addWidget(stop_widget)
            layout.addWidget(length_widget)
            
        layout.addStretch()
        
    def get_values(self):
        values = {}
        for param_name, widget in self.param_widgets.items():
            try:
                values[param_name] = widget.get_value()
            except ValueError as e:
                raise ValueError(f"Invalid value in {self.__class__.__name__}: {str(e)}")
                
        # Handle hlt_frange reconstruction if necessary
        if hasattr(self.component, 'hlt_frange'):
            start = values.pop('frange_start')
            stop = values.pop('frange_stop')
            length = values.pop('frange_length')
            values['hlt_frange'] = np.linspace(start, stop, length)
            
        return values

class ScParamsDialog(QDialog):
    def __init__(self, params, parent=None):
        super().__init__(parent)
        self.params = params
        self.result_params = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Edit ScParams")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs for each component
        components = {
            'Filter': self.params.filter,
            'Detection': self.params.detection,
            'Trigger': self.params.trigger,
            'TempGen': self.params.tempgen,
            'TempClust': self.params.tempclust,
            'Rematch': self.params.rematch
        }
        
        self.component_tabs = {}
        for name, component in components.items():
            tab = ComponentTab(component)
            self.component_tabs[name.lower()] = tab
            self.tab_widget.addTab(tab, name)
        
        # Add standard dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def accept(self):
        try:
            updated_params = type(self.params)(self.params.output_dir)

            for name, tab in self.component_tabs.items():
                values = tab.get_values()
                component_class = type(getattr(self.params, name))
                setattr(updated_params, name, component_class(**values))
            
            self.result_params = updated_params
            super().accept()
        except ValueError as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", str(e))
    
    @classmethod
    def edit_params(cls, params, parent=None):
        """
        Static convenience method to edit parameters
        
        Args:
            params: ScParams instance to edit
            parent: Optional parent widget
            
        Returns:
            tuple: (updated_params, accepted)
            where updated_params is the modified ScParams instance if accepted is True,
            otherwise returns (None, False)
        """
        dialog = cls(params, parent)
        result = dialog.exec_()
        return dialog.result_params, result == QDialog.Accepted

# Example usage:
"""
def edit_parameters(params):
    updated_params, accepted = ScParamsDialog.edit_params(params)
    if accepted:
        # Use the updated parameters
        return updated_params
    return None

# Usage:
params = ScParams(...)
if updated_params := edit_parameters(params):
    # Parameters were updated
    params = updated_params
"""