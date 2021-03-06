import os
import signal
import yaml

from gi.repository import Gtk
from gi.repository import GLib

from pylsner import gui


class Loader(yaml.Loader):

    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(Loader, self).__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f, Loader)


Loader.add_constructor('!include', Loader.include)


def main():
    main_win = gui.Window()
    reload_config(main_win)

    GLib.timeout_add(1, main_win.refresh)
    GLib.timeout_add(1000, reload_config, main_win)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()


def reload_config(window):
    if 'mtime' not in reload_config.__dict__:
        reload_config.mtime = 0
    config_path = 'etc/pylsner/config.yml'
    config_mtime = os.path.getmtime(config_path)
    widgets_path = 'etc/pylsner/widgets.yml'
    widgets_mtime = os.path.getmtime(widgets_path)
    reload_required = False
    if config_mtime > reload_config.mtime:
        reload_config.mtime = config_mtime
        reload_required = True
    if widgets_mtime > reload_config.mtime:
        reload_config.mtime = widgets_mtime
        reload_required = True
    if reload_required:
        with open(config_path) as config_file:
            config = yaml.load(config_file, Loader)
        window.widgets = init_widgets(config, window)
        window.refresh(True)
    return True


def init_widgets(config, window):
    widgets = []
    for wid_spec in config['widgets']:
        wid = gui.Widget(**wid_spec)
        wid.indicator.position[0] = ((window.width / 2)
                                     + wid.indicator.position[0]
                                    )
        wid.indicator.position[1] = ((window.height / 2)
                                     + (wid.indicator.position[1] * -1)
                                    )
        widgets.append(wid)
    return widgets
