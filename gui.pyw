import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from app.gui.main_window import MainWindow


QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

app = QApplication(sys.argv)
win = MainWindow()

apply_stylesheet(app, theme='dark_pink.xml')

win.show()
app.exec()
