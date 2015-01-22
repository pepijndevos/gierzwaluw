from setuptools import setup
import sys


APP = ['gierzwaluw/gui.py']
DATA_FILES = [('static', ['static/swallow.png', 'static/index.html'])]
MAC_OPTIONS = {
    'argv_emulation': True,
    'iconfile':'static/swallow.icns',
    'plist': {
        "LSUIElement": True,
    },
}
WIN_OPTIONS = {}

options = {}

if sys.platform == 'darwin':
    import py2app
    options.update({
        'options': {'py2app': MAC_OPTIONS},
        'app': APP,
    })

if sys.platform == 'win32':
    import py2exe
    options.update({
        'options': {'py2exe': WIN_OPTIONS},
        'windows': [{
            "script": 'gierzwaluw/gui.py',
            "icon_resources": [(0, "static/swallow.ico")],
            "dest_base" : "Gierzwaluw"
        }],
    })


setup(
    name="Gierzwaluw",
    packages=['gierzwaluw'],
    scripts=['gierzwaluw/gui.py', 'gierzwaluw/cli.py'],
    data_files=DATA_FILES,
    **options
)
