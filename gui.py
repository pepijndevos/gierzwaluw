import sys
import shutil
import socket
from PySide import QtCore, QtGui
from zeroconf import ServiceBrowser, Zeroconf

from server import FileServer
from client import Client

class PeerMenu(QtGui.QMenu):

    def __init__(self, share, quit):
        QtGui.QMenu.__init__(self)
        self.share = share
        self.quit = quit
        self.set_peers([])

    def callback(self, addr):
        def cb():
            (filename, _) = QtGui.QFileDialog.getSaveFileName()
            dialog = QtGui.QProgressDialog("Downloading file...", "Go Go Go!", 0, 100)
            dialog.setModal(True)
            c = Client(addr)
            c.progress.connect(lambda ratio: dialog.setValue(ratio * 100))
            c.save(filename)
        return cb

    @QtCore.Slot(object)
    def set_peers(self, files):
        self.clear()
        for addr, filename in files:
            self.addAction(QtGui.QAction(filename, self, triggered=self.callback(addr)))

        self.addSeparator()
        self.addAction(QtGui.QAction("Share...", self, triggered=self.share))
        self.addAction(QtGui.QAction("Quit", self, triggered=self.quit))

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

class Application(QtGui.QApplication):

    opened = QtCore.Signal(object)

    @QtCore.Slot(str)
    def open_file(self):
        (filename, _) = QtGui.QFileDialog.getOpenFileName()
        self.opened.emit(filename)

    @QtCore.Slot(object)
    def save_file(self, upload):
        (filename, _) = QtGui.QFileDialog.getSaveFileName()
        if filename:
            upload.save(filename)

class ServerThread(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.server = FileServer()

    def run(self):
        self.server.start()

if __name__ == '__main__':
    app = Application(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    st = ServerThread()
    st.start()
    st.server.uploaded.connect(app.save_file)
    app.opened.connect(st.server.set_download)

    icon = QtGui.QSystemTrayIcon(QtGui.QIcon('images/swallow.svg'), app)

    listener = GUIListener()
    t = QtCore.QThread()
    t.start()
    listener.moveToThread(t)

    menu = PeerMenu(share=app.open_file, quit=app.quit)
    icon.activated.connect(listener.check)
    listener.files.connect(menu.set_peers)

    icon.setContextMenu(menu)

    zeroconf = Zeroconf()
    ServiceBrowser(zeroconf, "_http._tcp.local.", listener)

    icon.show()

    app.exec_()
