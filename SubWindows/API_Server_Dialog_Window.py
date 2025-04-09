"""
Dialog window to ask if SCiLS API Server is local or external
"""

import sys
from PyQt5 import QtWidgets, QtGui, QtCore

from QCL_v4.Appearance.DarkMode import EnableDarkMode


class API_Server_Dialog(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(API_Server_Dialog, self).__init__(parent)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        self.initMe()

    def initMe(self):
        # Define geometry of this window
        self.setGeometry(550, 350, 300, 100)
        self.setWindowTitle('API Server Dialog Window')

        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName('centralWidget')

        self.mainGridLayout = QtWidgets.QGridLayout(self.centralWidget)
        #self.mainGridLayout.setSpacing(10)

        self.label = QtWidgets.QLabel('<font size="4">Start API as...</p>', self)
        self.rbtn1 = QtWidgets.QRadioButton('Local Server')
        self.rbtn2 = QtWidgets.QRadioButton('External Server')

        self.rbtn1.toggled.connect(self.onClicked)
        self.rbtn2.toggled.connect(self.onClicked)

        VerticalLayout = QtWidgets.QVBoxLayout()
        VerticalLayout.addWidget(self.label)
        VerticalLayout.addWidget(self.rbtn1)
        VerticalLayout.addWidget(self.rbtn2)

        self.subGridLayout = QtWidgets.QGridLayout()

        self.textToken = QtWidgets.QLabel('<font size="4"><p style="font-variant:small-caps;"><b>authentification token:<b></p>',
                                         self)

        self.authentificationTokenInput = 'kennwort'
        self.authentificationToken = QtWidgets.QLineEdit(self)
        self.authentificationToken.setLocale(self.locale())
        self.authentificationToken.setPlaceholderText('kennwort')
        self.authentificationToken.returnPressed.connect(self.authentificationTokenEnter)
        self.authentificationToken.setEnabled(True)

        self.textLocal = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Local server:<b></p>',
            self)

        self.LocalServerInput = 'C:/Program Files/SCiLS/SCiLS Lab/scilsMSserver.exe'
        self.LocalServer = QtWidgets.QLineEdit(self)
        self.LocalServer.setLocale(self.locale())
        self.LocalServer.setPlaceholderText('C:/Program Files/SCiLS/SCiLS Lab/scilsMSserver.exe')
        self.LocalServer.returnPressed.connect(self.LocalServerEnter)
        self.LocalServer.setEnabled(True)

        self.textIP = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>IP address:<b></p>',
            self)

        self.IPInput = '141.19.44.238'
        self.IP = QtWidgets.QLineEdit(self)
        self.IP.setLocale(self.locale())
        self.IP.setPlaceholderText('141.19.44.238')
        self.IP.returnPressed.connect(self.IPEnter)
        self.IP.setEnabled(True)

        self.subGridLayout.addWidget(self.textToken, 0, 1)
        self.subGridLayout.addWidget(self.authentificationToken, 0, 2)
        self.subGridLayout.addWidget(self.textIP, 1, 1)
        self.subGridLayout.addWidget(self.IP, 1, 2)
        self.subGridLayout.addWidget(self.textLocal, 0, 1)
        self.subGridLayout.addWidget(self.LocalServer, 1, 1)
        self.textLocal.setVisible(False)
        self.LocalServer.setVisible(False)

        self.mainGridLayout.addLayout(VerticalLayout, 0, 0)
        self.mainGridLayout.addLayout(self.subGridLayout, 1, 0)

        # show  Widget
        self.centralWidget.setLayout(self.mainGridLayout)
        self.setCentralWidget(self.centralWidget)

        self.rbtn1.setChecked(True)

    def onClicked(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            if radioBtn.text() ==  'Local Server':
                self.IP.setEnabled(False)
                self.authentificationToken.setEnabled(False)
                self.textToken.setVisible(False)
                self.IP.setVisible(False)
                self.textIP.setVisible(False)
                self.authentificationToken.setVisible(False)
                self.textLocal.setVisible(True)
                self.LocalServer.setVisible(True)
            else:
                self.IP.setEnabled(True)
                self.authentificationToken.setEnabled(True)
                self.IP.setVisible(True)
                self.textToken.setVisible(True)
                self.textIP.setVisible(True)
                self.authentificationToken.setVisible(True)
                self.textLocal.setVisible(False)
                self.LocalServer.setVisible(False)
            return radioBtn.text()


    def authentificationTokenEnter(self):
        self.authentificationTokenInput = self.authentificationToken.text()
        self.authentificationToken.clear()
        self.authentificationToken.setPlaceholderText(str(self.authentificationTokenInput))

    def IPEnter(self):
        self.IPInput = self.IP.text()
        self.IP.clear()
        self.IP.setPlaceholderText(str(self.IPInput))

    def LocalServerEnter(self):
        self.LocalServerInput = self.LocalServer.text()
        self.LocalServer.clear()
        self.LocalServer.setPlaceholderText(str(self.LocalServerInput))

if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)

    EnableDarkMode(app)

    ui = API_Server_Dialog()
    ui.show()

    sys.exit(app.exec())