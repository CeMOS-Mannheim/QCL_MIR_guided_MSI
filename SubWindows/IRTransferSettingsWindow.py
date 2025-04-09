'''
This dialog window provides the option to toggle between "infrared" and "optical". This defines in which "window" the MIR data from the M2iraViewer is transfered.
'''


import sys
from PyQt5 import QtWidgets, QtGui, QtCore

from QCL_v3.Appearance.DarkMode import EnableDarkMode


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

        # Define central widget
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName('centralWidget')

        # Define main grid layout
        self.mainGridLayout = QtWidgets.QGridLayout(self.centralWidget)

        textSmooth = QtWidgets.QLabel('<font size="4"><p style="font-variant:small-caps;"><b>smoothing:<b></p>',
                                      self)
        textType = QtWidgets.QLabel('<font size="4"><p style="font-variant:small-caps;"><b>Data:<b></p>',
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

        layoutRadioButton = QtWidgets.QGridLayout()

        self.RadioButton_IR = QtWidgets.QRadioButton("Infrared")
        self.RadioButton_IR.setChecked(True)
        #RadioButton.toggled.connect(self.onClicked)
        layoutRadioButton.addWidget(self.RadioButton_IR, 0, 0)

        self.RadioButton_Opt = QtWidgets.QRadioButton("Optical")
        #RadioButton.toggled.connect(self.onClicked)
        layoutRadioButton.addWidget(self.RadioButton_Opt, 0, 1)

        #Define Vertical layout
        VerticalLayout = QtWidgets.QVBoxLayout()
        VerticalLayout.addWidget(textType)
        VerticalLayout.addLayout(layoutRadioButton)
        VerticalLayout.addWidget(textSmooth)
        VerticalLayout.addWidget(self.smoothInput)
        VerticalLayout.addWidget(self.checkboxYN)


        self.mainGridLayout.addLayout(VerticalLayout, 0, 0)

        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)

    # functions used for changing the input values
    def smoothEnter(self):
        self.smoothValue = self.smoothInput.text()
        self.smoothInput.clear()
        self.smoothInput.setPlaceholderText(str(self.smoothValue))

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

    ui = IR_Transfer_Settings_Dialog()
    ui.show()

    sys.exit(app.exec())