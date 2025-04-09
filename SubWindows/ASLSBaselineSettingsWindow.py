'''
This dialog window provides the option to set paramteres and methods for baseline correction.

Currently  ASLS is implemented: general Algorithmus for Asymetric Least Squares Smoothing for Baseline Correction: P.H.C.Eilers & H.F.M.Boelens(2005)
'''

import sys
from PyQt5 import QtWidgets, QtGui, QtCore

from QCL_v4.Appearance.DarkMode import EnableDarkMode


class ASLS_Settings_Dialog(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(ASLS_Settings_Dialog, self).__init__(parent)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        self.initMe()

    def initMe(self):
        # Define geometry of this window
        self.setGeometry(550, 240, 250, 180)
        self.setMaximumSize(250, 180)
        self.setWindowTitle('Settings')

        # Define central widget
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName('centralWidget')

        # Define main grid layout
        self.mainGridLayout = QtWidgets.QGridLayout(self.centralWidget)

        labelSettings = QtWidgets.QLabel('<font size="5">ASLS Parameters:</p>', self)
        labelSmooth = QtWidgets.QLabel('<font size="4">Smooth:</p>', self)
        labelWeighting = QtWidgets.QLabel('<font size="4">Weighting:</p>', self)
        labelIteration = QtWidgets.QLabel('<font size="4">Iteration:</p>', self)

        self.smoothFactorValue = '10000'
        self.validatorInputsmoothFactor = QtGui.QDoubleValidator(0, 10000000, 0, self)
        self.validatorInputsmoothFactor.setLocale(self.locale())
        self.smoothFactorInput = QtWidgets.QLineEdit(self)
        self.smoothFactorInput.setLocale(self.locale())
        self.smoothFactorInput.setValidator(self.validatorInputsmoothFactor)
        self.smoothFactorInput.setPlaceholderText('10000')
        self.smoothFactorInput.returnPressed.connect(self.smoothFactorInput_Enter)

        self.smoothFactorValue1 = '100'
        self.validatorInputsmoothFactor1 = QtGui.QDoubleValidator(0, 10000000, 0, self)
        self.validatorInputsmoothFactor1.setLocale(self.locale())
        self.smoothFactorInput1 = QtWidgets.QLineEdit(self)
        self.smoothFactorInput1.setLocale(self.locale())
        self.smoothFactorInput1.setValidator(self.validatorInputsmoothFactor1)
        self.smoothFactorInput1.setPlaceholderText('100')
        self.smoothFactorInput1.returnPressed.connect(self.smoothFactorInput_Enter1)

        self.weightingFactorValue = '0.01'
        self.validatorInputweightingFactor = QtGui.QDoubleValidator(0, 1, 5, self)
        self.validatorInputweightingFactor.setLocale(self.locale())
        self.weightingFactorInput = QtWidgets.QLineEdit(self)
        self.weightingFactorInput.setLocale(self.locale())
        self.weightingFactorInput.setValidator(self.validatorInputweightingFactor)
        self.weightingFactorInput.setPlaceholderText('0.01')
        self.weightingFactorInput.returnPressed.connect(self.weightingFactorInput_Enter)

        self.iterationFactorValue = '10'
        self.validatorInputiterationFactor = QtGui.QDoubleValidator(0, 100, 0, self)
        self.validatorInputiterationFactor.setLocale(self.locale())
        self.iterationFactorInput = QtWidgets.QLineEdit(self)
        self.iterationFactorInput.setLocale(self.locale())
        self.iterationFactorInput.setValidator(self.validatorInputiterationFactor)
        self.iterationFactorInput.setPlaceholderText('10')
        self.iterationFactorInput.returnPressed.connect(self.iterationFactorInput_Enter)

        HorizontalLayout = QtWidgets.QHBoxLayout()
        HorizontalLayout.addWidget(self.smoothFactorInput)
        HorizontalLayout.addWidget(self.smoothFactorInput1)

        VerticalLayout = QtWidgets.QVBoxLayout()
        VerticalLayout.addWidget(labelSettings)
        VerticalLayout.addWidget(labelSmooth)
        VerticalLayout.addLayout(HorizontalLayout)
        VerticalLayout.addWidget(labelWeighting)
        VerticalLayout.addWidget(self.weightingFactorInput)
        VerticalLayout.addWidget(labelIteration)
        VerticalLayout.addWidget(self.iterationFactorInput)

        self.mainGridLayout.addLayout(VerticalLayout, 0, 0)

        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)

    # functions used for changing the input values
    def smoothFactorInput_Enter(self):
        self.smoothFactorValue = self.smoothFactorInput.text()
        self.smoothFactorInput.clear()
        self.smoothFactorInput.setPlaceholderText(str(self.smoothFactorValue))
    def smoothFactorInput_Enter1(self):
        self.smoothFactorValue1 = self.smoothFactorInput1.text()
        self.smoothFactorInput1.clear()
        self.smoothFactorInput1.setPlaceholderText(str(self.smoothFactorValue1))
    def weightingFactorInput_Enter(self):
        self.weightingFactorValue = self.weightingFactorInput.text()
        self.weightingFactorInput.clear()
        self.weightingFactorInput.setPlaceholderText(str(self.weightingFactorValue))
    def iterationFactorInput_Enter(self):
        self.iterationFactorValue = self.iterationFactorInput.text()
        self.iterationFactorInput.clear()
        self.iterationFactorInput.setPlaceholderText(str(self.iterationFactorValue))

    # function executed once dialog window is closed
    def closeEvent(self, event):
        self.reply = QtWidgets.QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if self.reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)

    EnableDarkMode(app)

    ui = ASLS_Settings_Dialog()
    ui.show()

    sys.exit(app.exec())