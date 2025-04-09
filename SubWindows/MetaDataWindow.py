'''
This dialog window provides the option to set and display the meta data information.
'''

import sys
from PyQt5 import QtWidgets, QtGui, QtCore

from QCL_v4.Appearance.DarkMode import EnableDarkMode


class MetaData_Dialog(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(MetaData_Dialog, self).__init__(parent)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        self.initMe()

    def initMe(self):
        # Define geometry of this window
        self.setGeometry(550, 240, 250, 20)
        self.setMaximumSize(240, 240)
        self.setWindowTitle('Metadata')

        # Define central widget
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName('centralWidget')

        # Define main grid layout
        self.mainGridLayout = QtWidgets.QGridLayout(self.centralWidget)

        DeviceText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Device:<b></p>',
            self)

        self.deviceBox = QtWidgets.QComboBox(self)
        self.deviceBox.addItem("Lumos II ILIM")
        self.deviceBox.addItem("Hyperion II ILIM")

        ModeText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Mode:<b></p>',
            self)

        self.modeBox = QtWidgets.QComboBox(self)
        self.modeBox.addItem("Sweep scan")
        self.modeBox.addItem("Discrete scan")

        MinText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Wvnm_min:<b></p>',
            self)

        self.WvnmMinInputValue = '954'
        self.validatorWvnmMinInput = QtGui.QDoubleValidator(500, 2000, 0, self)
        self.validatorWvnmMinInput.setLocale(self.locale())
        self.WvnmMinInput = QtWidgets.QLineEdit(self)
        self.WvnmMinInput.setLocale(self.locale())
        self.WvnmMinInput.setValidator(self.validatorWvnmMinInput)
        self.WvnmMinInput.setPlaceholderText('950')
        self.WvnmMinInput.setMaximumSize(40, 20)
        self.WvnmMinInput.returnPressed.connect(self.WvnmMinInputEnter)

        MaxText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Wvnm_max:<b></p>',
            self)

        self.WvnmMaxInputValue = '1802'
        self.validatorWvnmMaxInput = QtGui.QDoubleValidator(500, 2000, 0, self)
        self.validatorWvnmMaxInput.setLocale(self.locale())
        self.WvnmMaxInput = QtWidgets.QLineEdit(self)
        self.WvnmMaxInput.setLocale(self.locale())
        self.WvnmMaxInput.setValidator(self.validatorWvnmMaxInput)
        self.WvnmMaxInput.setPlaceholderText('1800')
        self.WvnmMaxInput.setMaximumSize(40, 20)
        self.WvnmMaxInput.returnPressed.connect(self.WvnmMaxInputEnter)

        PxText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>px (um):<b></p>',
            self)

        self.pxInputValue = '4.25'
        self.validatorpxInput = QtGui.QDoubleValidator(1, 50, 2, self)
        self.validatorpxInput.setLocale(self.locale())
        self.pxInput = QtWidgets.QLineEdit(self)
        self.pxInput.setLocale(self.locale())
        self.pxInput.setValidator(self.validatorpxInput)
        self.pxInput.setPlaceholderText('4.25')
        self.pxInput.setMaximumSize(40, 20)
        self.pxInput.returnPressed.connect(self.pxInputEnter)

        PyText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>px (um):<b></p>',
            self)

        self.pyInputValue = '4.25'
        self.validatorpyInput = QtGui.QDoubleValidator(1, 50, 2, self)
        self.validatorpyInput.setLocale(self.locale())
        self.pyInput = QtWidgets.QLineEdit(self)
        self.pyInput.setLocale(self.locale())
        self.pyInput.setValidator(self.validatorpyInput)
        self.pyInput.setPlaceholderText('4.25')
        self.pyInput.setMaximumSize(40, 20)
        self.pyInput.returnPressed.connect(self.pyInputEnter)

        tsxText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>tsx:<b></p>',
            self)

        self.tsxInputValue = '520'
        self.validatortsxInput = QtGui.QDoubleValidator(100, 1000, 0, self)
        self.validatortsxInput.setLocale(self.locale())
        self.tsxInput = QtWidgets.QLineEdit(self)
        self.tsxInput.setLocale(self.locale())
        self.tsxInput.setValidator(self.validatortsxInput)
        self.tsxInput.setPlaceholderText('520')
        self.tsxInput.setMaximumSize(40, 20)
        self.tsxInput.returnPressed.connect(self.tsxInputEnter)

        tsyText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>tsy:<b></p>',
            self)

        self.tsyInputValue = '480'
        self.validatortsyInput = QtGui.QDoubleValidator(100, 1000, 0, self)
        self.validatortsyInput.setLocale(self.locale())
        self.tsyInput = QtWidgets.QLineEdit(self)
        self.tsyInput.setLocale(self.locale())
        self.tsyInput.setValidator(self.validatortsyInput)
        self.tsyInput.setPlaceholderText('480')
        self.tsyInput.setMaximumSize(40, 20)
        self.tsyInput.returnPressed.connect(self.tsyInputEnter)

        # Define horizontal layouts
        HorizontalLayout0 = QtWidgets.QHBoxLayout()
        HorizontalLayout0.addWidget(DeviceText)
        HorizontalLayout0.addWidget(self.deviceBox)

        HorizontalLayout1 = QtWidgets.QHBoxLayout()
        HorizontalLayout1.addWidget(ModeText)
        HorizontalLayout1.addWidget(self.modeBox)

        HorizontalLayout2 = QtWidgets.QHBoxLayout()
        HorizontalLayout2.addWidget(MinText)
        HorizontalLayout2.addWidget(self.WvnmMinInput)

        HorizontalLayout3 = QtWidgets.QHBoxLayout()
        HorizontalLayout3.addWidget(MaxText)
        HorizontalLayout3.addWidget(self.WvnmMaxInput)

        HorizontalLayout4 = QtWidgets.QHBoxLayout()
        HorizontalLayout4.addWidget(PxText)
        HorizontalLayout4.addWidget(self.pxInput)

        HorizontalLayout5 = QtWidgets.QHBoxLayout()
        HorizontalLayout5.addWidget(PyText)
        HorizontalLayout5.addWidget(self.pyInput)

        HorizontalLayout6 = QtWidgets.QHBoxLayout()
        HorizontalLayout6.addWidget(tsxText)
        HorizontalLayout6.addWidget(self.tsxInput)

        HorizontalLayout7 = QtWidgets.QHBoxLayout()
        HorizontalLayout7.addWidget(tsyText)
        HorizontalLayout7.addWidget(self.tsyInput)

        self.mainGridLayout.addLayout(HorizontalLayout0, 0, 0)
        self.mainGridLayout.addLayout(HorizontalLayout1, 1, 0)
        self.mainGridLayout.addLayout(HorizontalLayout2, 2, 0)
        self.mainGridLayout.addLayout(HorizontalLayout3, 3, 0)
        self.mainGridLayout.addLayout(HorizontalLayout4, 4, 0)
        self.mainGridLayout.addLayout(HorizontalLayout5, 5, 0)
        self.mainGridLayout.addLayout(HorizontalLayout6, 6, 0)
        self.mainGridLayout.addLayout(HorizontalLayout7, 7, 0)

        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)

    # functions used for changing the input values
    def pxInputEnter(self):
        self.pxInputValue = self.pxInput.text()
        self.pxInput.clear()
        self.pxInput.setPlaceholderText(str(self.pxInputValue))
    def pyInputEnter(self):
        self.pyInputValue = self.pyInput.text()
        self.pyInput.clear()
        self.pyInput.setPlaceholderText(str(self.pyInputValue))
    def tsxInputEnter(self):
        self.tsxInputValue = self.tsxInput.text()
        self.tsxInput.clear()
        self.tsxInput.setPlaceholderText(str(self.tsxInputValue))
    def tsyInputEnter(self):
        self.tsyInputValue = self.tsyInput.text()
        self.tsyInput.clear()
        self.tsyInput.setPlaceholderText(str(self.tsyInputValue))

    def WvnmMinInputEnter(self):
        self.WvnmMinInputValue = self.WvnmMinInput.text()
        self.WvnmMinInput.clear()
        self.WvnmMinInput.setPlaceholderText(str(self.WvnmMinInputValue))
    def WvnmMaxInputEnter(self):
        self.WvnmMaxInputValue = self.WvnmMaxInput.text()
        self.WvnmMaxInput.clear()
        self.WvnmMaxInput.setPlaceholderText(str(self.WvnmMaxInputValue))

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

    ui = MetaData_Dialog()
    ui.show()

    sys.exit(app.exec())