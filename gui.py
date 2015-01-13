import sys
import cherrypy
import shutil
import socket
from cherrypy.process import plugins
from PySide import QtCore, QtGui
from zeroconf import ServiceBrowser, Zeroconf

from server import start
from client import Client

class GUIPlugin(plugins.SimplePlugin, QtCore.QObject):

    save = QtCore.Signal(object)

    def __init__(self, bus):
        QtCore.QObject.__init__(self)
        plugins.SimplePlugin.__init__(self, bus)

    def start(self):
        self.bus.log('Starting up GUI')
        self.bus.subscribe("file-ul", self.save_file)

    def stop(self):
        self.bus.log('Stopping GUI')
        self.bus.unsubscribe("file-ul", self.save_file)

    def share(self):
        (filename, _) = QtGui.QFileDialog.getOpenFileName()
        self.bus.publish('file-dl', filename)

    def save_file(self, file_ul):
        self.save.emit(file_ul)
        return True # hrm

class PeerMenu(QtGui.QMenu):

    def __init__(self, share, quit):
        QtGui.QMenu.__init__(self)
        self.peers = {}
        self.sep = self.addSeparator()
        self.addAction(QtGui.QAction("Share...", self, triggered=share))
        self.addAction(QtGui.QAction("Quit", self, triggered=quit))

    @QtCore.Slot(str, str, str)
    def add_peer(self, name, addr):
        def cb():
            print(name)
        act = self.peers.setdefault(name, QtGui.QAction(name, self, triggered=cb))
        self.insertAction(self.sep, act)

    @QtCore.Slot(str)
    def remove_peer(self, name):
        act = self.peers[name]
        self.removeAction(act)

class GUIListener(QtCore.QObject):

    added   = QtCore.Signal(str, str)
    removed = QtCore.Signal(str)

    def remove_service(self, zeroconf, type, name):
        self.removed.emit(name)

    def add_service(self, zeroconf, type, name):
        print(name)
        info = zeroconf.get_service_info(type, name)
        if info:
            addr = "http://%s:%d" % (socket.inet_ntoa(info.address), info.port)
            self.added.emit(name, addr)

class Application(QtGui.QApplication):

    @staticmethod
    def quit():
        QtGui.QApplication.quit()
        cherrypy.engine.exit()

    @QtCore.Slot(object)
    def save_file(self, file_ul):
        (filename, _) = QtGui.QFileDialog.getSaveFileName()
        print(filename)

        if filename:
            cherrypy.engine.log('Saving %s' % file_ul.filename)
            with open(filename, 'wb') as outfile:
                shutil.copyfileobj(file_ul.file, outfile)
            return True
        else:
            return False

if __name__ == '__main__':
    plugin = GUIPlugin(cherrypy.engine)
    plugin.subscribe()
    start(False)

    app = Application(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    plugin.save.connect(app.save_file)

    icon = QtGui.QSystemTrayIcon(QtGui.QIcon('images/glyphicons-206-electricity.png'), app)

    listener = GUIListener()
    menu = PeerMenu(share=plugin.share, quit=app.quit)
    listener.added.connect(menu.add_peer)
    listener.removed.connect(menu.remove_peer)

    icon.setContextMenu(menu)

    #cherrypy.engine.subscribe("progress", progress)
    zeroconf = Zeroconf()
    ServiceBrowser(zeroconf, "_http._tcp.local.", listener)

    icon.show()

    app.exec_()
