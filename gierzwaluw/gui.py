import sys
import shutil
import socket
from PySide import QtCore, QtGui
from zeroconf import ServiceBrowser, Zeroconf

from gierzwaluw.server import FileServer
from gierzwaluw.client import Client


class GUIListener(QtCore.QObject):

    files = QtCore.Signal(object)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.services = {}

    @QtCore.Slot()
    def check(self):
        files = []
        for name, addr in self.services.items():
            c = Client(addr)
            filename = c.poll()
            if filename:
                files.append((addr, filename))
        self.files.emit(files)

    def remove_service(self, zeroconf, type, name):
        self.services.pop(name)

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            addr = "http://%s:%d" % (socket.inet_ntoa(info.address), info.port)
            self.services[name] = addr

class ListenerThread(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.listener = GUIListener()
        self.listener.moveToThread(self)

    def run(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.listener.check)
        timer.start(1000*60)
        self.exec_()

class ServerThread(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.server = FileServer()

    def run(self):
        self.server.start()

class Peer(QtGui.QListWidgetItem):

    def __init__(self, filename, addr):
        QtGui.QListWidgetItem.__init__(self, filename)
        self.addr = addr

class PeerWindow(QtCore.QObject):
    
    opened = QtCore.Signal(object)

    def __init__(self, app, icon):
        QtCore.QObject.__init__(self)
        self.app = app
        self.icon = icon
        self.window = QtGui.QMainWindow(parent=None, flags=QtCore.Qt.Popup)

        frame = QtGui.QFrame(self.window)
        self.window.setCentralWidget(frame)
        layout = QtGui.QVBoxLayout(frame)

        self.peers = QtGui.QListWidget(self.window)
        self.peers.itemClicked.connect(self.callback)
        layout.addWidget(self.peers)

        self.progress = QtGui.QProgressBar(self.window)
        layout.addWidget(self.progress)

        share = QtGui.QPushButton("Share...", self.window)
        share.clicked.connect(self.open_file)
        layout.addWidget(share)

        quit = QtGui.QPushButton("Quit", self.window)
        quit.clicked.connect(app.quit)
        layout.addWidget(quit)

    @QtCore.Slot(str)
    def open_file(self):
        (filename, _) = QtGui.QFileDialog.getOpenFileName()
        self.opened.emit(filename)

    @QtCore.Slot(object)
    def save_file(self, upload):
        (filename, _) = QtGui.QFileDialog.getSaveFileName()
        if filename:
            upload.save(filename)

    @QtCore.Slot(object)
    def toggle(self, files):
        if self.window.isVisible():
            self.window.hide()
        else:
            self.window.show()
            height = self.window.geometry().height()
            width = self.window.geometry().width()
            icon = self.icon.geometry().center()
            desktop = self.app.desktop().availableGeometry()
            center = desktop.center();
            margin = 50
            if   icon.x() > center.x() and icon.y() > center.y(): # bottom right icon
                self.window.move(desktop.right() - margin - width, desktop.bottom() - margin - height)
            elif icon.x() > center.x() and icon.y() < center.y(): # top right icon
                self.window.move(desktop.right() - margin - width, margin)
            elif icon.x() < center.x() and icon.y() < center.y(): # top left icon
                self.window.move(margin, margin)
            elif icon.x() < center.x() and icon.y() > center.y(): # bottom left icon
                self.window.move(margin, desktop.bottom() - margin - height)

    @QtCore.Slot(object)
    def set_peers(self, files):
        self.peers.clear()
        for addr, filename in files:
            self.peers.addItem(Peer(filename, addr))

    @QtCore.Slot(object)
    def callback(self, item):
        (filename, _) = QtGui.QFileDialog.getSaveFileName()
        c = Client(item.addr)
        c.progress.connect(self.progress.setValue)
        c.save(filename)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    st = ServerThread()
    st.start()

    lt = ListenerThread()
    lt.start()

    icon = QtGui.QSystemTrayIcon(QtGui.QIcon('static/swallow.png'), app)
    
    window = PeerWindow(app, icon)
    icon.activated.connect(lt.listener.check)
    icon.activated.connect(window.toggle)
    lt.listener.files.connect(window.set_peers)
    window.opened.connect(st.server.set_download)
    st.server.uploaded.connect(window.save_file)

    zeroconf = Zeroconf()
    ServiceBrowser(zeroconf, "_http._tcp.local.", lt.listener)

    icon.show()

    app.exec_()
