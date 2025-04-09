'''
This dialog window provides the option to set input parameters for modifying the image mask

In its current implementation it allows "binary closing", "removal of holes", to "remove objects", to apply an "erosion" or "dilation" operation
which are additionally "masekd within the given image mask" in the given order.

'''

import sys
from PyQt5 import QtWidgets, QtGui, QtCore

from QCL_v4.Appearance.DarkMode import EnableDarkMode

class Mask_Settings_Dialog(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(Mask_Settings_Dialog, self).__init__(parent)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        self.initMe()

    def initMe(self):
        # Define geometry of this window
        self.setGeometry(550, 240, 240, 60)
        self.setMaximumSize(250, 240)
        self.setWindowTitle('Settings')

        # Define central widget
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName('centralWidget')

        # Define main grid layout
        self.mainGridLayout = QtWidgets.QGridLayout(self.centralWidget)

        # Image Mask Settings
        textMaskModify = QtWidgets.QLabel('<font size="4"><p style="font-variant:small-caps;"><b>Mask Settings:<b></p>',
                                          self)

        self.MaskBinaryClosingCheckbox = QtWidgets.QCheckBox("closing")
        self.MaskBinaryClosingCheckbox.setChecked(False)

        self.MaskRemoveHolesObjectsCheckbox = QtWidgets.QCheckBox("holes")
        self.MaskRemoveHolesObjectsCheckbox.setChecked(False)

        self.MaskRemoveSmallObjectsCheckbox = QtWidgets.QCheckBox("objects")
        self.MaskRemoveSmallObjectsCheckbox.setChecked(False)

        self.MaskBinaryClosingInputValue = '2'
        self.validatorMaskBinaryClosingInput = QtGui.QDoubleValidator(0, 15000, 0, self)
        self.validatorMaskBinaryClosingInput.setLocale(self.locale())
        self.MaskBinaryClosingInput = QtWidgets.QLineEdit(self)
        self.MaskBinaryClosingInput.setLocale(self.locale())
        self.MaskBinaryClosingInput.setValidator(self.validatorMaskBinaryClosingInput)
        self.MaskBinaryClosingInput.setPlaceholderText('2')
        self.MaskBinaryClosingInput.returnPressed.connect(self.MaskBinaryClosingInputEnter)

        self.MaskRemoveHolesObjectsInputValue = '200'
        self.validatorMaskRemoveHolesObjectsInput = QtGui.QDoubleValidator(0, 15000, 0, self)
        self.validatorMaskRemoveHolesObjectsInput.setLocale(self.locale())
        self.MaskRemoveHolesObjectsInput = QtWidgets.QLineEdit(self)
        self.MaskRemoveHolesObjectsInput.setLocale(self.locale())
        self.MaskRemoveHolesObjectsInput.setValidator(self.validatorMaskRemoveHolesObjectsInput)
        self.MaskRemoveHolesObjectsInput.setPlaceholderText('200')
        self.MaskRemoveHolesObjectsInput.returnPressed.connect(self.MaskRemoveHolesObjectsInputEnter)

        self.MaskRemoveSmallObjectsInputValue = '200'
        self.validatorMaskRemoveSmallObjectsInput = QtGui.QDoubleValidator(0, 15000, 0, self)
        self.validatorMaskRemoveSmallObjectsInput.setLocale(self.locale())
        self.MaskRemoveSmallObjectsInput = QtWidgets.QLineEdit(self)
        self.MaskRemoveSmallObjectsInput.setLocale(self.locale())
        self.MaskRemoveSmallObjectsInput.setValidator(self.validatorMaskRemoveSmallObjectsInput)
        self.MaskRemoveSmallObjectsInput.setPlaceholderText('200')
        self.MaskRemoveSmallObjectsInput.returnPressed.connect(self.MaskRemoveSmallObjectsInputEnter)

        self.MaskBinaryErosionCheckbox = QtWidgets.QCheckBox("erosion")
        self.MaskBinaryErosionCheckbox.setChecked(False)

        self.MaskBinaryDilationCheckbox = QtWidgets.QCheckBox("dilation")
        self.MaskBinaryDilationCheckbox.setChecked(False)

        self.MaskBinaryErosionInputValue = '1'
        self.validatorMaskBinaryErosionInput = QtGui.QDoubleValidator(0, 1000, 0, self)
        self.validatorMaskBinaryErosionInput.setLocale(self.locale())
        self.MaskBinaryErosionInput = QtWidgets.QLineEdit(self)
        self.MaskBinaryErosionInput.setLocale(self.locale())
        self.MaskBinaryErosionInput.setValidator(self.validatorMaskBinaryErosionInput)
        self.MaskBinaryErosionInput.setPlaceholderText('1')
        self.MaskBinaryErosionInput.returnPressed.connect(self.MaskBinaryErosionInputEnter)

        self.MaskBinaryDilationInputValue = '1'
        self.validatorMaskBinaryDilationInput = QtGui.QDoubleValidator(0, 1000, 0, self)
        self.validatorMaskBinaryDilationInput.setLocale(self.locale())
        self.MaskBinaryDilationInput = QtWidgets.QLineEdit(self)
        self.MaskBinaryDilationInput.setLocale(self.locale())
        self.MaskBinaryDilationInput.setValidator(self.validatorMaskBinaryDilationInput)
        self.MaskBinaryDilationInput.setPlaceholderText('1')
        self.MaskBinaryDilationInput.returnPressed.connect(self.MaskBinaryDilationInputEnter)

        self.MaskBinaryMaskCheckbox = QtWidgets.QCheckBox("within mask")
        self.MaskBinaryMaskCheckbox.setChecked(False)

        self.gridLayoutSettings = QtWidgets.QWidget(self)
        self.gridLayoutSettingsLayout = QtWidgets.QGridLayout(self.gridLayoutSettings)

        self.gridLayoutSettingsLayout.addWidget(textMaskModify, 0, 0)
        self.gridLayoutSettingsLayout.addWidget(self.MaskBinaryClosingCheckbox, 1, 0)
        self.gridLayoutSettingsLayout.addWidget(self.MaskBinaryClosingInput, 1, 1)
        self.gridLayoutSettingsLayout.addWidget(self.MaskRemoveHolesObjectsCheckbox, 2, 0)
        self.gridLayoutSettingsLayout.addWidget(self.MaskRemoveHolesObjectsInput, 2, 1)
        self.gridLayoutSettingsLayout.addWidget(self.MaskRemoveSmallObjectsCheckbox, 3, 0)
        self.gridLayoutSettingsLayout.addWidget(self.MaskRemoveSmallObjectsInput,3, 1)
        self.gridLayoutSettingsLayout.addWidget(self.MaskBinaryErosionCheckbox, 4, 0)
        self.gridLayoutSettingsLayout.addWidget(self.MaskBinaryErosionInput,4, 1)
        self.gridLayoutSettingsLayout.addWidget(self.MaskBinaryDilationCheckbox, 5, 0)
        self.gridLayoutSettingsLayout.addWidget(self.MaskBinaryDilationInput,5, 1)
        self.gridLayoutSettingsLayout.addWidget(self.MaskBinaryMaskCheckbox, 6, 0)

        self.mainGridLayout.addWidget(self.gridLayoutSettings, 0, 0)

        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)


    # functions used for changing the input values
    def MaskBinaryErosionInputEnter(self):
        self.MaskBinaryErosionInputValue = self.MaskBinaryErosionInput.text()
        self.MaskBinaryErosionInput.clear()
        self.MaskBinaryErosionInput.setPlaceholderText(str(self.MaskBinaryErosionInputValue))

    def MaskBinaryDilationInputEnter(self):
        self.MaskBinaryDilationInputValue = self.MaskBinaryDilationInput.text()
        self.MaskBinaryDilationInput.clear()
        self.MaskBinaryDilationInput.setPlaceholderText(str(self.MaskBinaryDilationInputValue))

    def MaskRemoveSmallObjectsInputEnter(self):
        self.MaskRemoveSmallObjectsInputValue = self.MaskRemoveSmallObjectsInput.text()
        self.MaskRemoveSmallObjectsInput.clear()
        self.MaskRemoveSmallObjectsInput.setPlaceholderText(str(self.MaskRemoveSmallObjectsInputValue))

    def MaskRemoveHolesObjectsInputEnter(self):
        self.MaskRemoveHolesObjectsInputValue = self.MaskRemoveHolesObjectsInput.text()
        self.MaskRemoveHolesObjectsInput.clear()
        self.MaskRemoveHolesObjectsInput.setPlaceholderText(str(self.MaskRemoveHolesObjectsInputValue))

    def MaskBinaryClosingInputEnter(self):
        self.MaskBinaryClosingInputValue = self.MaskBinaryClosingInput.text()
        self.MaskBinaryClosingInput.clear()
        self.MaskBinaryClosingInput.setPlaceholderText(str(self.MaskBinaryClosingInputValue))

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

    ui = Mask_Settings_Dialog()
    ui.show()

    sys.exit(app.exec())