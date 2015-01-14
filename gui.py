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
        self.bus.subscribe("file-ul", self.save_file)

    def stop(self):
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
        self.share = share
        self.quit = quit
        self.set_peers([])

    def callback(self, addr):
        def cb():
            print(addr)
        return cb

    @QtCore.Slot(object)
    def set_peers(self, files):
        print(files)
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
        print(name)
        info = zeroconf.get_service_info(type, name)
        if info:
            addr = "http://%s:%d" % (socket.inet_ntoa(info.address), info.port)
            self.services[name] = addr

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
    t = QtCore.QThread()
    t.start()
    listener.moveToThread(t)

    menu = PeerMenu(share=plugin.share, quit=app.quit)
    icon.activated.connect(listener.check)
    listener.files.connect(menu.set_peers)

    icon.setContextMenu(menu)

    #cherrypy.engine.subscribe("progress", progress)
    zeroconf = Zeroconf()
    ServiceBrowser(zeroconf, "_http._tcp.local.", listener)

    icon.show()

    app.exec_()
