'''
This dialog window provides the option to set cropping details.
'''

import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import os

from QCL_v4.Appearance.DarkMode import EnableDarkMode

#define functions
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class Crop_Dialog(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(Crop_Dialog, self).__init__(parent)
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

        #self.CropButtonYN = QtWidgets.QPushButton('', self)
        #self.CropButtonYN.setMaximumSize(40, 40)
        #self.CropButtonYN.setIcon(QtGui.QIcon(resource_path('Graphics/CropButton.png')))
        #self.CropButtonYN.setIconSize(QtCore.QSize(30, 30))
        #self.CropButtonYN.setCheckable(True)
        #self.CropButtonYN.setChecked(False)

        NxText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>N_x (tiles):<b></p>',
            self)

        self.NxInputValue = '1'
        self.validatorNxInput = QtGui.QDoubleValidator(1, 15, 0, self)
        self.validatorNxInput.setLocale(self.locale())
        self.NxInput = QtWidgets.QLineEdit(self)
        self.NxInput.setLocale(self.locale())
        self.NxInput.setValidator(self.validatorNxInput)
        self.NxInput.setPlaceholderText('1')
        self.NxInput.setMaximumSize(40, 20)
        self.NxInput.returnPressed.connect(self.NxInputEnter)

        NyText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>N_y (tiles):<b></p>',
            self)

        self.NyInputValue = '1'
        self.validatorNyInput = QtGui.QDoubleValidator(1, 15, 0, self)
        self.validatorNyInput.setLocale(self.locale())
        self.NyInput = QtWidgets.QLineEdit(self)
        self.NyInput.setLocale(self.locale())
        self.NyInput.setValidator(self.validatorNyInput)
        self.NyInput.setPlaceholderText('1')
        self.NyInput.setMaximumSize(40, 20)
        self.NyInput.returnPressed.connect(self.NyInputEnter)

        tsxText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>tsx:<b></p>',
            self)

        self.tsxInputValue = '480'
        self.validatortsxInput = QtGui.QDoubleValidator(100, 1000, 0, self)
        self.validatortsxInput.setLocale(self.locale())
        self.tsxInput = QtWidgets.QLineEdit(self)
        self.tsxInput.setLocale(self.locale())
        self.tsxInput.setValidator(self.validatortsxInput)
        self.tsxInput.setPlaceholderText('480')
        self.tsxInput.setMaximumSize(40, 20)
        self.tsxInput.returnPressed.connect(self.tsxInputEnter)

        tsyText = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>tsy:<b></p>',
            self)

        self.tsyInputValue = '520'
        self.validatortsyInput = QtGui.QDoubleValidator(100, 1000, 0, self)
        self.validatortsyInput.setLocale(self.locale())
        self.tsyInput = QtWidgets.QLineEdit(self)
        self.tsyInput.setLocale(self.locale())
        self.tsyInput.setValidator(self.validatortsyInput)
        self.tsyInput.setPlaceholderText('520')
        self.tsyInput.setMaximumSize(40, 20)
        self.tsyInput.returnPressed.connect(self.tsyInputEnter)

        # Define horizontal layouts
        horSpace = QtWidgets.QSpacerItem(180, 0)

        #HorizontalLayout3 = QtWidgets.QHBoxLayout()
        #HorizontalLayout3.addSpacerItem(horSpace)
        #HorizontalLayout3.addWidget(self.CropButtonYN)

        HorizontalLayout4 = QtWidgets.QHBoxLayout()
        HorizontalLayout4.addWidget(NxText)
        HorizontalLayout4.addWidget(self.NxInput)

        HorizontalLayout5 = QtWidgets.QHBoxLayout()
        HorizontalLayout5.addWidget(NyText)
        HorizontalLayout5.addWidget(self.NyInput)

        HorizontalLayout6 = QtWidgets.QHBoxLayout()
        HorizontalLayout6.addWidget(tsxText)
        HorizontalLayout6.addWidget(self.tsxInput)

        HorizontalLayout7 = QtWidgets.QHBoxLayout()
        HorizontalLayout7.addWidget(tsyText)
        HorizontalLayout7.addWidget(self.tsyInput)

        #self.mainGridLayout.addLayout(HorizontalLayout3, 1, 0)
        self.mainGridLayout.addLayout(HorizontalLayout4, 2, 0)
        self.mainGridLayout.addLayout(HorizontalLayout5, 3, 0)
        self.mainGridLayout.addLayout(HorizontalLayout6, 4, 0)
        self.mainGridLayout.addLayout(HorizontalLayout7, 5, 0)

        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)

    # functions used for changing the input values
    def NxInputEnter(self):
        self.NxInputValue = self.NxInput.text()
        self.NxInput.clear()
        self.NxInput.setPlaceholderText(str(self.NxInputValue))
    def NyInputEnter(self):
        self.NyInputValue = self.NyInput.text()
        self.NyInput.clear()
        self.NyInput.setPlaceholderText(str(self.NyInputValue))
    def tsxInputEnter(self):
        self.tsxInputValue = self.tsxInput.text()
        self.tsxInput.clear()
        self.tsxInput.setPlaceholderText(str(self.tsxInputValue))
    def tsyInputEnter(self):
        self.tsyInputValue = self.tsyInput.text()
        self.tsyInput.clear()
        self.tsyInput.setPlaceholderText(str(self.tsyInputValue))

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

    ui = Crop_Dialog()
    ui.show()

    sys.exit(app.exec())