import sys
import os
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = r'C:\Users\starg\OneDrive\바탕 화면\risk-management-system\venv\Lib\site-packages\PyQt5\Qt5\plugins'
from PyQt5.QtWidgets import QApplication, QWidget, QLabel

try:
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('Test Window')
    window.setGeometry(100, 100, 300, 200)
    label = QLabel('PyQt5 Test', window)
    label.move(100, 50)
    window.show()
    print("PyQt5 window created successfully")
    sys.exit(app.exec_())
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()