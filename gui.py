import sys
import cherrypy
from cherrypy.process import plugins
from PySide import QtCore, QtGui

from server import start

class GUIPlugin(plugins.SimplePlugin):

    def start(self):
        self.bus.log('Starting up GUI')
        self.bus.subscribe("file-ul", self.save_file)

    def stop(self):
        self.bus.log('Stopping GUI')
        self.bus.unsubscribe("file-ul", self.save_file)

    def share(self):
        (filename, _) = QtGui.QFileDialog.getOpenFileName()
        print(filename)
        self.bus.publish('file-dl', filename)

    def save_file(self, file_ul):
        if self.file_ul:
            self.bus.log('Saving %s' % file_ul.filename)
            with open(os.path.join(self.file_ul, file_ul.filename), 'wb') as outfile:
                shutil.copyfileobj(file_ul.file, outfile)
            return True
        else:
            return False

if __name__ == '__main__':
    plugin = GUIPlugin(cherrypy.engine)
    plugin.subscribe()

    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icon = QtGui.QSystemTrayIcon(QtGui.QIcon('images/glyphicons-206-electricity.png'), app)

    menu = QtGui.QMenu()
    menu.addAction(QtGui.QAction("Share...", menu, triggered=plugin.share))
    menu.addAction(QtGui.QAction("Quit", menu, triggered=app.quit))


    icon.setContextMenu(menu)
    icon.show()

    start(False)

    app.exec_()
