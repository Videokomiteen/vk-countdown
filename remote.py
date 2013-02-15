#!encoding:utf-8
import sys
from PyQt4 import QtCore, QtGui,QtNetwork


normal_style = """
 QLabel {
   color: white;
   background-color: black;
   font-size: 70pt;
   font-family: "DejaVu Sans Mono";
   font-weight: bold;
}"""

info_style = """
 QLabel {
   color: white;
   background-color: black;
   font-size: 30pt;
   font-family: "DejaVu Sans Mono";
   font-weight: bold;
}"""

overtime_style = """
 QLabel {
   color: black;
   background-color: red;
   font-size: 70pt;
   font-family: "DejaVu Sans Mono";
   font-weight: bold;
}"""

class ConnectBox(QtGui.QDialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.lineEdit = QtGui.QLineEdit()
        self.lineEdit.setText('127.0.0.1')

        connectButton = QtGui.QPushButton('Kople til')
        connectButton.setDefault(True)
        cancelButton = QtGui.QPushButton('Avbryt')

        buttonBox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
        buttonBox.addButton(connectButton, QtGui.QDialogButtonBox.AcceptRole)
        buttonBox.addButton(cancelButton, QtGui.QDialogButtonBox.RejectRole)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.lineEdit)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def connect_to(self):
        return self.lineEdit.text()

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)

        cb = ConnectBox()
        if cb.exec_():
            self.ip = cb.connect_to()

        self.socket = QtNetwork.QTcpSocket(self)
        self.socket.readyRead.connect(self.read)
        self.socket.error.connect(self.socketError)

        layout = QtGui.QGridLayout()

        self.countdownLabel = QtGui.QLabel()
        self.countdownLabel.setStyleSheet(info_style)
        self.countdownLabel.setText('Not Connected')
        self.countdownLabel.setAlignment(QtCore.Qt.AlignCenter)


        layout.addWidget(self.countdownLabel,0,0,1,2)


        self.standbyText = QtGui.QLineEdit()
        self.standbyText.returnPressed.connect(self.standby)
        self.countdownTime = QtGui.QLineEdit()
        self.countdownTime.returnPressed.connect(self.start)

        layout.addWidget(self.standbyText,1,0,1,1)
        layout.addWidget(self.countdownTime,2,0,1,1)

        self.standbyButton = QtGui.QPushButton('Standby')
        self.standbyButton.clicked.connect(self.standby)
        self.startButton = QtGui.QPushButton('Start')
        self.startButton.clicked.connect(self.start)
        layout.addWidget(self.standbyButton,1,1)
        layout.addWidget(self.startButton,2,1)


        self.widget = QtGui.QWidget()
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)

        self.connect()
        self.reconnect = 0

    def sizeHint(self):
        return QtCore.QSize(400,400)

    def minimumSizeHint(self):
        return QtCore.QSize(400,400)

    def read(self):
        self.reconnect = 0
        text = str(self.socket.readLine()).strip()
        cmd = text.split()
        if cmd[0] == 'COUNTDOWN':
            self.countdownLabel.setStyleSheet(normal_style)
            self.countdownLabel.setText(cmd[1])
        elif cmd[0] == 'OVERTIME':
            self.countdownLabel.setStyleSheet(overtime_style)
            self.countdownLabel.setText(cmd[1])
        elif cmd[0] == 'STANDINGBY':
            self.countdownLabel.setStyleSheet(info_style)

            fjs = text.replace(cmd[0],"").strip()
            self.countdownLabel.setText(fjs)
            self.standbyText.setText(fjs)
        
        if self.socket.bytesAvailable(): self.read()

    @QtCore.pyqtSlot()
    def connect(self):
        self.socket.connectToHost(self.ip, 8675) #VK

    def socketError(self, e):
        if self.reconnect > 10:
            qmb = QtGui.QMessageBox.information(self, 'FEIL', u'Nettverksfeil. Kople til på nytt?',
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if qmb == QtGui.QMessageBox.Yes:
                self.reconnect = 0
                self.socketError(e)
            else:
                self.close()
        else:
            self.reconnect += 1
            QtCore.QTimer.singleShot(1000, self, QtCore.SLOT('connect()'))


    def standby(self):
        self.socket.write('STANDBY %s\n'%self.standbyText.text())

    def start(self):
        self.socket.write('START %s\n'%self.countdownTime.text())
        

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    mw = MainWindow()
    mw.show()

    sys.exit(app.exec_())
