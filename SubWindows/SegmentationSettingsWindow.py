"""
notes
"""

import sys
from PyQt5 import QtWidgets, QtGui, QtCore

from QCL.Appearance.DarkMode import EnableDarkMode


class Segmentation_Settings_Dialog(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(Segmentation_Settings_Dialog, self).__init__(parent)
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

        # Segmentation
        textSegmentation = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>segmentation:<b></p>', self)

        self.SegmentationMethodCombo = QtWidgets.QComboBox(self)
        self.SegmentationMethodCombo.addItem("K-means")

        self.SegmentationInputValue = '2'
        self.validatorSegmentationInput = QtGui.QDoubleValidator(0, 1000, 0, self)
        self.validatorSegmentationInput.setLocale(self.locale())
        self.SegmentationInput = QtWidgets.QLineEdit(self)
        self.SegmentationInput.setLocale(self.locale())
        self.SegmentationInput.setValidator(self.validatorSegmentationInput)
        self.SegmentationInput.setPlaceholderText('2')
        self.SegmentationInput.returnPressed.connect(self.SegmentationInputEnter)

        VerticalLayout = QtWidgets.QHBoxLayout()
        VerticalLayout.addWidget(textSegmentation)
        VerticalLayout.addWidget(self.SegmentationMethodCombo)
        VerticalLayout.addWidget(self.SegmentationInput)

        self.mainGridLayout.addLayout(VerticalLayout, 0, 0)

        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)

    def SegmentationInputEnter(self):
        self.SegmentationInputValue = self.SegmentationInput.text()
        self.SegmentationInput.clear()
        self.SegmentationInput.setPlaceholderText(str(self.SegmentationInputValue))


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

    ui = Segmentation_Settings_Dialog()
    ui.show()

    sys.exit(app.exec())