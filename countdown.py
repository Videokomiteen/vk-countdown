#!encoding:utf-8

normal_style_template = """
 QLabel {
   color: white;
   background-color: black;
   font-size: %dpt;
   font-family: "DejaVu Sans Mono";
   font-weight: bold;
}"""
normal_style = normal_style_template%180

warning_style_template = """
 QLabel {
   color: red;
   background-color: black;
   font-size: %dpt;
   font-family: "DejaVu Sans Mono";
   font-weight: bold;
}"""
warning_style = warning_style_template%180

negative_style_template = """
 QLabel {
   color: black;
   background-color: red;
   font-size: %dpt;
   font-family: "DejaVu Sans Mono";
   font-weight: bold;
}"""
negative_style = negative_style_template%180

standby_style_template = """
 QLabel {
   color: yellow;
   background-color: black;
   font-size: %dpt;
   font-family: "DejaVu Sans Mono";
   font-weight: bold;
}"""

standby_style = standby_style_template%100

import sys
from PyQt4 import QtCore, QtGui, QtNetwork


def StartTcpServer():
    tcpServer = QtNetwork.QTcpServer()
    if not tcpServer.listen(port=8675):
        print 'error'

    ips = QtNetwork.QNetworkInterface.allAddresses()
    ipa = "127.0.0.1"

    for ip in ips:
        if ip != QtNetwork.QHostAddress.LocalHost and \
                ip.toIPv4Address():
            ipa = ip.toString()
            break
    return ipa, tcpServer

def write_all(cs, t):
    remove = []
    for c in cs:
        if c.connected:
            c.write(t)
        else:
            remove.append(c)
    for c in remove:
        cs.remove(c)


class ActiveLabel(QtGui.QLabel):
    clicked = QtCore.pyqtSignal(QtGui.QMouseEvent)
    keypress= QtCore.pyqtSignal(QtGui.QKeyEvent)

    def __init__(self, *args):
        super(ActiveLabel, self).__init__(*args)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def mouseReleaseEvent(self, ev):
        self.clicked.emit(ev)

    def keyReleaseEvent(self, ev):
        self.keypress.emit(ev)


class FSAutomaton(object):
    def __init__(self, mw, label, ipa, clients):
        self.fontsize = 100
        self.label = label
        self.ipa = ipa

        self.current_state = self.not_connected
        self.current_state()

        self.timer = QtCore.QTimer(interval=1000) # miliseconds
        self.timer.timeout.connect(self.on_every_second)

        self.remainingTime = 0
        self.clients = clients

        self.standbyText = 'VIDEOKOMITEEN'
        self.mw = mw


    # Event methods:
    def on_every_second(self):
        self.remainingTime -= 1
        self.current_state()

    # Methods:
    def start(self, time):
        if self.current_state not in [self.standingby, self.not_connected]:
            return

        w = self.mw.width()-100
        h = self.mw.height()-100

        for i in range(10,500):
            self.label.setStyleSheet(normal_style_template%i)
            fm = self.label.fontMetrics()
            if fm.width("00:00") > w: break
            if fm.height() > h: break

        self.fontsize = i

        self.remainingTime = time
        self.current_state = self.countdown
        self.current_state()
        self.timer.start()

    def standby(self):
        self.timer.stop()
        self.current_state = self.standingby


        w = self.mw.width()-150
        h = self.mw.height()-150

        for i in range(10,300):
            self.label.setStyleSheet(standby_style_template%i)
            fm = self.label.fontMetrics()
            if fm.width(self.standbyText) > w: break
            if fm.height() > h: break

        self.fontsize = i
        
        self.current_state()
        
    def connect(self):
        if self.current_state == self.not_connected:
            self.standby()
        self.current_state()


    # States:
    def not_connected(self):
        self.label.setStyleSheet(standby_style_template%self.fontsize)
        self.label.setText(self.ipa)

    def standingby(self):
        self.label.setStyleSheet(standby_style_template%self.fontsize)
        self.label.setText(self.standbyText)

        write_all(self.clients, 'STANDINGBY %s'%self.standbyText)


    def countdown(self):
        if self.remainingTime < 0:
            self.label.setStyleSheet(negative_style_template%self.fontsize)
            self.label.setText("00:00")
            #self.label.setText("%02d:%02d" % divmod(abs(self.remainingTime), 60))
            write_all(self.clients, 'OVERTIME %02d:%02d'%divmod(abs(self.remainingTime),60))
        elif self.remainingTime < 60:
            self.label.setStyleSheet(warning_style_template%self.fontsize)
            self.label.setText("%02d:%02d" % divmod(self.remainingTime, 60))
            write_all(self.clients, 'COUNTDOWN %02d:%02d'%divmod(abs(self.remainingTime),60))
        else:
            self.label.setStyleSheet(normal_style_template%self.fontsize)
            self.label.setText("%02d:%02d" % divmod(self.remainingTime, 60))
            write_all(self.clients, 'COUNTDOWN %02d:%02d'%divmod(abs(self.remainingTime),60))


class ClientHandler(QtCore.QObject):

    def __init__(self, client_con, fsa):
        QtCore.QObject.__init__(self)
        self.socket = client_con
        self.socket.readyRead.connect(self.read_cmd)
        self.socket.disconnected.connect(self.socket.deleteLater)
        self.socket.disconnected.connect(self.disconnect)

        self.fsa = fsa
        self.connected = True

    def disconnect(self):
        self.connected = False

    def read_cmd(self):
        #instream = QtCore.QDataStream(self.socket)
        #nf = instream.readString()
        #print nf
        text = str(self.socket.readLine()).strip()
        cmd = text.split()
        try:
            if cmd[0] == 'START':
                self.fsa.start(int(cmd[1]))
            elif cmd[0] == 'STANDBY':
                if cmd[1]:
                    self.fsa.standbyText = text.replace(cmd[0], "").strip()
                self.fsa.standby()
        except:
            pass
        if self.socket.bytesAvailable(): self.read_cmd()

    def write(self, t):
        if self.connected and self.socket.isValid():
            self.socket.write(t+'\n')

def main(argv):
    app = QtGui.QApplication(argv)
    app.setOverrideCursor(QtCore.Qt.BlankCursor)
    mw = QtGui.QMainWindow()
    mw.setWindowTitle('VK Nedtelling')

    l = ActiveLabel()
    l.setAlignment(QtCore.Qt.AlignCenter)

    clients = []
    ipa,tcpServer = StartTcpServer()
    fsa = FSAutomaton(mw, l,ipa,clients)
    
    @l.keypress.connect
    def on_key(ev):
        if ev.key() == QtCore.Qt.Key_Escape:
            mw.close()

    @tcpServer.newConnection.connect
    def handle():
        clients.append(ClientHandler(tcpServer.nextPendingConnection(), fsa))
        fsa.connect()


    mw.setCentralWidget(l)
    mw.showFullScreen()
    #mw.show()
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main(sys.argv))

