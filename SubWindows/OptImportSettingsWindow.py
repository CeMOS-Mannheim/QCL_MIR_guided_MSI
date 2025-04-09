'''
This dialog window provides the option to toggle between "infrared" and "optical". This defines in which "window" the input data is transfered.
it accepts a .tif(f) image of size 3 (three color channels).

'''

import sys
from PyQt5 import QtWidgets, QtGui, QtCore

from QCL_v4.Appearance.DarkMode import EnableDarkMode


class Opt_Import_Settings_Dialog(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(Opt_Import_Settings_Dialog, self).__init__(parent)
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

        textType = QtWidgets.QLabel('<font size="4"><p style="font-variant:small-caps;"><b>Data:<b></p>',
                                      self)


        layoutRadioButton = QtWidgets.QGridLayout()

        self.RadioButton_IR = QtWidgets.QRadioButton("Infrared")
        layoutRadioButton.addWidget(self.RadioButton_IR, 0, 0)

        self.RadioButton_Opt = QtWidgets.QRadioButton("Optical")
        self.RadioButton_Opt.setChecked(True)
        layoutRadioButton.addWidget(self.RadioButton_Opt, 0, 1)

        # Define vertical layout
        VerticalLayout = QtWidgets.QVBoxLayout()
        VerticalLayout.addWidget(textType)
        VerticalLayout.addLayout(layoutRadioButton)

        self.mainGridLayout.addLayout(VerticalLayout, 0, 0)

        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)

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

    ui = Opt_Import_Settings_Dialog()
    ui.show()

    sys.exit(app.exec())