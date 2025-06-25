import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from Source.UI.MainWindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(900, 650)
    win.show()
    sys.exit(app.exec())
