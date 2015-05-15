import os
import signal
import yaml

from gi.repository import GLib
from gi.repository import Gtk

from pylsner import gui


class ConfigNotFoundError(Exception):
    pass


class Loader(yaml.Loader):

    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(Loader, self).__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f, Loader)


Loader.add_constructor('!include', Loader.include)


class Pylsner:

    def __init__(self):
        self.widgets = []
        self.tick_cnt = 0
        self.config_mtime = 0
        self.interval = 50
        self.config_dir_path = self.find_configs()

    @staticmethod
    def find_configs():
        search_paths = ['~', '/etc', './etc']
        for root in search_paths:
            root = os.path.normpath(os.path.expanduser(root))
            if os.path.isdir(os.path.join(root, 'pylsner')):
                return os.path.join(root, 'pylsner')
            elif os.path.isdir(os.path.join(root, '.pylsner')):
                return os.path.join(root, '.pylsner')
        raise ConfigNotFoundError

    def run(self):
        self.load_config()

        while True:
            GLib.timeout_add(self.interval, self.tick)
            GLib.timeout_add(1000, self.load_config)
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            Gtk.main()

    def tick(self):
        self.tick_cnt += self.interval
        if self.tick_cnt >= 60000:
            self.tick_cnt = 0
        for widget in self.widgets:
            widget.refresh(self.tick_cnt)
        return True

    def load_config(self):
        reload_required = self.check_config_mtime()
        if reload_required:
            self.reload_config()
        return True

    def check_config_mtime(self):
        for filename in os.listdir(self.config_dir_path):
            if filename.startswith('.'):
                continue
            file_path = os.path.join(self.config_dir_path, filename)
            mtime = os.path.getmtime(file_path)
            if mtime > self.config_mtime:
                self.config_mtime = mtime
                return True
        return False

    def reload_config(self):
        config_path = os.path.join(self.config_dir_path, 'config.yml')
        with open(config_path) as config_file:
            config = yaml.load(config_file, Loader)
        for widget in self.widgets:
            widget.destroy()
        self.widgets = self.init_widgets(config)
        for widget in self.widgets:
            widget.refresh()

    def init_widgets(self, config):
        widgets = []
        for widget_spec in config['widgets']:
            widget = gui.Widget(**widget_spec)
            widgets.append(widget)
        return widgets
