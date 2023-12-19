"""
notes
"""

import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from QCL.Appearance.DarkMode import EnableDarkMode


class Parameters_Mask_Settings_Dialog(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(Parameters_Mask_Settings_Dialog, self).__init__(parent)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        self.initMe()

    def initMe(self):
        # Define geometry of this window
        self.setGeometry(550, 240, 250, 20)
        self.setMaximumSize(250, 180)
        self.setWindowTitle('Mask Settings')

        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName('centralWidget')

        self.mainGridLayout = QtWidgets.QGridLayout(self.centralWidget)

        self.MaskBinaryClosingCheckboxIR = QtWidgets.QCheckBox("binary closing")
        self.MaskBinaryClosingCheckboxIR.setChecked(False)

        self.MaskRemoveHolesObjectsCheckboxIR = QtWidgets.QCheckBox("remove holes")
        self.MaskRemoveHolesObjectsCheckboxIR.setChecked(False)

        self.MaskRemoveSmallObjectsCheckboxIR = QtWidgets.QCheckBox("remove objects")
        self.MaskRemoveSmallObjectsCheckboxIR.setChecked(False)

        self.MaskBinaryClosingInputValueIR = '1'
        self.validatorMaskBinaryClosingInputIR = QtGui.QDoubleValidator(0, 15000, 0, self)
        self.validatorMaskBinaryClosingInputIR.setLocale(self.locale())
        self.MaskBinaryClosingInputIR = QtWidgets.QLineEdit(self)
        self.MaskBinaryClosingInputIR.setLocale(self.locale())
        self.MaskBinaryClosingInputIR.setValidator(self.validatorMaskBinaryClosingInputIR)
        self.MaskBinaryClosingInputIR.setPlaceholderText('1')
        self.MaskBinaryClosingInputIR.returnPressed.connect(self.MaskBinaryClosingInputIREnter)

        self.MaskRemoveHolesObjectsInputValueIR = '200'
        self.validatorMaskRemoveHolesObjectsInputIR = QtGui.QDoubleValidator(0, 15000, 0, self)
        self.validatorMaskRemoveHolesObjectsInputIR.setLocale(self.locale())
        self.MaskRemoveHolesObjectsInputIR = QtWidgets.QLineEdit(self)
        self.MaskRemoveHolesObjectsInputIR.setLocale(self.locale())
        self.MaskRemoveHolesObjectsInputIR.setValidator(self.validatorMaskRemoveHolesObjectsInputIR)
        self.MaskRemoveHolesObjectsInputIR.setPlaceholderText('200')
        self.MaskRemoveHolesObjectsInputIR.returnPressed.connect(self.MaskRemoveHolesObjectsInputIREnter)

        self.MaskRemoveSmallObjectsInputValueIR = '200'
        self.validatorMaskRemoveSmallObjectsInputIR = QtGui.QDoubleValidator(0, 15000, 0, self)
        self.validatorMaskRemoveSmallObjectsInputIR.setLocale(self.locale())
        self.MaskRemoveSmallObjectsInputIR = QtWidgets.QLineEdit(self)
        self.MaskRemoveSmallObjectsInputIR.setLocale(self.locale())
        self.MaskRemoveSmallObjectsInputIR.setValidator(self.validatorMaskRemoveSmallObjectsInputIR)
        self.MaskRemoveSmallObjectsInputIR.setPlaceholderText('200')
        self.MaskRemoveSmallObjectsInputIR.returnPressed.connect(self.MaskRemoveSmallObjectsInputIREnter)

        HorizontalLayoutMask0 = QtWidgets.QHBoxLayout()
        HorizontalLayoutMask0.addWidget(self.MaskBinaryClosingCheckboxIR)
        HorizontalLayoutMask0.addWidget(self.MaskRemoveHolesObjectsCheckboxIR)
        HorizontalLayoutMask0.addWidget(self.MaskRemoveSmallObjectsCheckboxIR)

        HorizontalLayoutMask1 = QtWidgets.QHBoxLayout()
        HorizontalLayoutMask1.addWidget(self.MaskBinaryClosingInputIR)
        HorizontalLayoutMask1.addWidget(self.MaskRemoveHolesObjectsInputIR)
        HorizontalLayoutMask1.addWidget(self.MaskRemoveSmallObjectsInputIR)

        self.mainGridLayout.addLayout(HorizontalLayoutMask0, 0, 0)
        self.mainGridLayout.addLayout(HorizontalLayoutMask1, 1, 0)

        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)

    def MaskRemoveSmallObjectsInputIREnter(self):
        self.MaskRemoveSmallObjectsInputValueIR = self.MaskRemoveSmallObjectsInputIR.text()
        self.MaskRemoveSmallObjectsInputIR.clear()
        self.MaskRemoveSmallObjectsInputIR.setPlaceholderText(str(self.MaskRemoveSmallObjectsInputValueIR))
    def MaskRemoveHolesObjectsInputIREnter(self):
        self.MaskRemoveHolesObjectsInputValueIR = self.MaskRemoveHolesObjectsInputIR.text()
        self.MaskRemoveHolesObjectsInputIR.clear()
        self.MaskRemoveHolesObjectsInputIR.setPlaceholderText(str(self.MaskRemoveHolesObjectsInputValueIR))
    def MaskBinaryClosingInputIREnter(self):
        self.MaskBinaryClosingInputValueIR = self.MaskBinaryClosingInputIR.text()
        self.MaskBinaryClosingInputIR.clear()
        self.MaskBinaryClosingInputIR.setPlaceholderText(str(self.MaskBinaryClosingInputValueIR))


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

    ui = Parameters_Mask_Settings_Dialog()
    ui.show()

    sys.exit(app.exec())