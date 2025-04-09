'''
This dialog window provides the option to set input parameters and methods for the image registration.

In its current implementation it allows for three different registration types: rigid, affine and a combination (rigid + affine).

The number of iterations can be set by the user.
'''

import sys
from PyQt5 import QtWidgets, QtGui, QtCore

from QCL_v4.Appearance.DarkMode import EnableDarkMode


class Registration_Settings_Dialog(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(Registration_Settings_Dialog, self).__init__(parent)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        self.initMe()

    def initMe(self):
        # Define geometry of this window
        self.setGeometry(550, 240, 250, 60)
        self.setMaximumSize(250, 180)
        self.setWindowTitle('Settings')

        # Define central widget
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName('centralWidget')

        # Define main grid layout
        self.mainGridLayout = QtWidgets.QGridLayout(self.centralWidget)

        # Registration Settings/Parameters
        textImageRegistration = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Registration Settings:<b></p>',
            self)

        self.registrationType = QtWidgets.QComboBox(self)
        self.registrationType.setObjectName(("comboBox"))
        self.registrationType.addItem("rigid")
        self.registrationType.addItem("affine")
        self.registrationType.addItem('iterative affine')
        self.registrationType.setMaximumSize(150,25)

        self.registrationInput1Value = '100'
        self.validatorregistrationInput1 = QtGui.QDoubleValidator(0, 15000, 0, self)
        self.validatorregistrationInput1.setLocale(self.locale())
        self.registrationInput1 = QtWidgets.QLineEdit(self)
        self.registrationInput1.setLocale(self.locale())
        self.registrationInput1.setValidator(self.validatorregistrationInput1)
        self.registrationInput1.setPlaceholderText('100')
        self.registrationInput1.returnPressed.connect(self.registrationInput1Enter)

        text_0 = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>#Iterations:<b></p>',
            self)

        # Define grid layout
        self.gridLayoutSettings = QtWidgets.QWidget(self)
        self.gridLayoutSettingsLayout = QtWidgets.QGridLayout(self.gridLayoutSettings)

        self.gridLayoutSettingsLayout.addWidget(textImageRegistration, 0, 0)
        self.gridLayoutSettingsLayout.addWidget(self.registrationType, 1, 0)
        self.gridLayoutSettingsLayout.addWidget(text_0, 2, 0)
        self.gridLayoutSettingsLayout.addWidget(self.registrationInput1, 2, 1)

        self.mainGridLayout.addWidget(self.gridLayoutSettings, 0, 0)

        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)

    #function used for changing the input value
    def registrationInput1Enter(self):
        self.registrationInput1Value = self.registrationInput1.text()
        self.registrationInput1.clear()
        self.registrationInput1.setPlaceholderText(str(self.registrationInput1Value))

    # function executed once dialog window is closed
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

    ui = Registration_Settings_Dialog()
    ui.show()

    sys.exit(app.exec())
