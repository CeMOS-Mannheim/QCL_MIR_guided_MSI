'''
This dialog window provides the option to set input parameters and methods spectral differentation.

In its current implementation it allows for "piecewise linear interpolation" and "Savitzky-Golay filtering".

The order can be selected (1: first derivative, 2: second derivative)

- optional arguments:
    window length
    polynomial order

'''

import sys
from PyQt5 import QtWidgets, QtGui, QtCore

from QCL_v4.Appearance.DarkMode import EnableDarkMode


class Parameters_derivative_Settings_Dialog(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(Parameters_derivative_Settings_Dialog, self).__init__(parent)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        self.initMe()

    def initMe(self):
        # Define geometry of this window
        self.setGeometry(550, 240, 250, 20)
        self.setMaximumSize(200, 180)
        self.setWindowTitle('Spectral differentiation settings')

        # Define central widget
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName('centralWidget')

        # Define main grid layout
        self.mainGridLayout = QtWidgets.QGridLayout(self.centralWidget)

        OrderText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Der. order:<b></p>',
            self)

        self.OrderInputValue = '2'
        self.validatorOrderInput = QtGui.QDoubleValidator(0, 2, 0, self)
        self.validatorOrderInput.setLocale(self.locale())
        self.OrderInput = QtWidgets.QLineEdit(self)
        self.OrderInput.setLocale(self.locale())
        self.OrderInput.setValidator(self.validatorOrderInput)
        self.OrderInput.setPlaceholderText('2')
        self.OrderInput.returnPressed.connect(self.OrderInputEnter)

        LengthText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Win. length:<b></p>',
            self)

        self.LengthInputValue = 'None'
        self.validatorLengthInput = QtGui.QDoubleValidator(1, 50, 0, self)
        self.validatorLengthInput.setLocale(self.locale())
        self.LengthInput = QtWidgets.QLineEdit(self)
        self.LengthInput.setLocale(self.locale())
        self.LengthInput.setValidator(self.validatorLengthInput)
        self.LengthInput.setPlaceholderText('None')
        self.LengthInput.returnPressed.connect(self.LengthInputEnter)

        PolyOrderText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Poly. order:<b></p>',
            self)

        self.PolyInputValue = 'None'
        self.validatorPolyInput = QtGui.QDoubleValidator(1, 4, 0, self)
        self.validatorPolyInput.setLocale(self.locale())
        self.PolyInput = QtWidgets.QLineEdit(self)
        self.PolyInput.setLocale(self.locale())
        self.PolyInput.setValidator(self.validatorPolyInput)
        self.PolyInput.setPlaceholderText('None')
        self.PolyInput.returnPressed.connect(self.PolyInputEnter)

        # Define horizontal layouts
        HorizontalLayout0 = QtWidgets.QHBoxLayout()
        HorizontalLayout0.addWidget(OrderText)
        HorizontalLayout0.addWidget(self.OrderInput)

        HorizontalLayout1 = QtWidgets.QHBoxLayout()
        HorizontalLayout1.addWidget(LengthText)
        HorizontalLayout1.addWidget(self.LengthInput)

        HorizontalLayout2 = QtWidgets.QHBoxLayout()
        HorizontalLayout2.addWidget(PolyOrderText)
        HorizontalLayout2.addWidget(self.PolyInput)

        self.mainGridLayout.addLayout(HorizontalLayout0, 0, 0)
        self.mainGridLayout.addLayout(HorizontalLayout1, 1, 0)
        self.mainGridLayout.addLayout(HorizontalLayout2, 2, 0)

        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)

    # functions used for changing the input values
    def OrderInputEnter(self):
        self.OrderInputValue = self.OrderInput.text()
        self.OrderInput.clear()
        self.OrderInput.setPlaceholderText(str(self.OrderInputValue))
    def LengthInputEnter(self):
        self.LengthInputValue = self.LengthInput.text()
        self.LengthInput.clear()
        self.LengthInput.setPlaceholderText(str(self.LengthInputValue))
    def PolyInputEnter(self):
        self.PolyInputValue = self.PolyInput.text()
        self.PolyInput.clear()
        self.PolyInput.setPlaceholderText(str(self.PolyInputValue))

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

    ui = Parameters_derivative_Settings_Dialog()
    ui.show()

    sys.exit(app.exec())