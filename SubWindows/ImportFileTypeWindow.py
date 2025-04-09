"""

Stefan Schmidt
Dialog window for importing data of different data types

"""

import sys
from PyQt5 import QtWidgets, QtGui, QtCore

from QCL_v4.Appearance.DarkMode import EnableDarkMode


class ImportDataTypeWindow_Dialog(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(ImportDataTypeWindow_Dialog, self).__init__(parent)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        self.initMe()

    def initMe(self):
        # Define geometry of this window
        self.setGeometry(550, 240, 250, 180)
        self.setMaximumSize(240, 180)
        self.setWindowTitle('Export Dialog')

        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName('centralWidget')

        self.mainGridLayout = QtWidgets.QGridLayout(self.centralWidget)
        #self.mainGridLayout.setSpacing(5)

        label = QtWidgets.QLabel('<font size="5">Import settings: data type</p>', self)
        #label = QtWidgets.QLabel('<font size="6"><p style="font-variant:small-caps;"><b>Export Settings:<b></p>', self)
        self.rbtn1 = QtWidgets.QRadioButton('.zarr')
        self.rbtn2 = QtWidgets.QRadioButton('.fsm')
        self.rbtn3 = QtWidgets.QRadioButton('.pickle')

        self.rbtnTextSelected = '.zarr'

        self.rbtn1.toggled.connect(self.onClicked)
        self.rbtn2.toggled.connect(self.onClicked)
        self.rbtn3.toggled.connect(self.onClicked)

        VerticalSpacer0 = QtWidgets.QSpacerItem(15, 10, QtWidgets.QSizePolicy.Expanding)

        VerticalLayout0 = QtWidgets.QVBoxLayout()
        VerticalLayout0.addWidget(label)
        VerticalLayout0.addSpacerItem(VerticalSpacer0)
        VerticalLayout0.addWidget(self.rbtn1)
        VerticalLayout0.addWidget(self.rbtn2)
        VerticalLayout0.addWidget(self.rbtn3)

        self.NumberFilesBox = QtWidgets.QComboBox(self)
        self.NumberFilesBox.addItem("single file")
        self.NumberFilesBox.addItem("multiple files")
        self.NumberFilesBox.setIconSize(QtCore.QSize(50, 15))
        self.NumberFilesBox.setFixedWidth(120)

        VerticalLayout1 = QtWidgets.QVBoxLayout()
        VerticalLayout1.addSpacerItem(VerticalSpacer0)
        VerticalLayout1.addWidget(self.NumberFilesBox)

        self.mainGridLayout.addLayout(VerticalLayout0, 0, 0)
        self.mainGridLayout.addLayout(VerticalLayout1, 1, 0)

        # show  Widget
        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)

        self.rbtn1.setChecked(True)

    def onClicked(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.rbtnTextSelected = radioBtn.text()

    def topNvalueInput_Enter(self):
        self.topNvalue = self.topNvalueInput.text()
        self.topNvalueInput.clear()
        self.topNvalueInput.setPlaceholderText(str(self.topNvalue))

    def closeEvent(self, event):
        self.reply = QtWidgets.QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if self.reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            print('Window closed')
        else:
            event.ignore()

if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)

    EnableDarkMode(app)

    ui = ImportDataTypeWindow_Dialog()
    ui.show()

    sys.exit(app.exec())