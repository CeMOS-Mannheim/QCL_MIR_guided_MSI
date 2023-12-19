"""
notes
"""

import sys
from PyQt5 import QtWidgets, QtGui, QtCore

from QCL.Appearance.DarkMode import EnableDarkMode


class IR_Transfer_Settings_Dialog(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(IR_Transfer_Settings_Dialog, self).__init__(parent)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        self.initMe()

    def initMe(self):
        # Define geometry of this window
        self.setGeometry(550, 240, 250, 60)
        self.setMaximumSize(250, 180)
        self.setWindowTitle('Settings')

        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName('centralWidget')

        self.mainGridLayout = QtWidgets.QGridLayout(self.centralWidget)

        textSmooth = QtWidgets.QLabel('<font size="4"><p style="font-variant:small-caps;"><b>smoothing:<b></p>',
                                      self)

        self.checkboxYN = QtWidgets.QCheckBox("Apply gaussian filter y/n?")
        self.checkboxYN.setChecked(False)

        self.smoothValue = '0.5'
        self.validatorMaskSmooth = QtGui.QDoubleValidator(0.1, 5, 4, self)
        self.validatorMaskSmooth.setLocale(self.locale())
        self.smoothInput = QtWidgets.QLineEdit(self)
        self.smoothInput.setLocale(self.locale())
        self.smoothInput.setValidator(self.validatorMaskSmooth)
        self.smoothInput.setPlaceholderText('0.5')
        self.smoothInput.returnPressed.connect(self.smoothEnter)

        VerticalLayout = QtWidgets.QVBoxLayout()
        VerticalLayout.addWidget(textSmooth)
        VerticalLayout.addWidget(self.smoothInput)
        VerticalLayout.addWidget(self.checkboxYN)

        self.mainGridLayout.addLayout(VerticalLayout, 0, 0)

        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)

    def smoothEnter(self):
        self.smoothValue = self.smoothInput.text()
        self.smoothInput.clear()
        self.smoothInput.setPlaceholderText(str(self.smoothValue))


    def closeEvent(self, event):
        self.reply = QtWidgets.QMessageBox.question(self, 'Close window?', 'Are you sure you want to close the window?',
                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if self.reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)

    EnableDarkMode(app)

    ui = IR_Transfer_Settings_Dialog()
    ui.show()

    sys.exit(app.exec())