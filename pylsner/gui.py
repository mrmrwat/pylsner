import cairo

from gi.repository import Gtk
from gi.repository import Gdk

from pylsner import plugin


class Window(Gtk.Window):

    def __init__(self):
        super(Window, self).__init__(skip_pager_hint=True,
                                     skip_taskbar_hint=True,
                                    )
        self.set_title('Pylsner')

        screen = self.get_screen()
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.set_size_request(self.width, self.height)
        self.set_position(Gtk.WindowPosition.CENTER)
        rgba = screen.get_rgba_visual()
        self.set_visual(rgba)
        self.override_background_color(Gtk.StateFlags.NORMAL,
                                       Gdk.RGBA(0, 0, 0, 0),
                                      )

        self.set_wmclass('pylsner', 'pylsner')
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.stick()
        self.set_keep_below(True)

        drawing_area = Gtk.DrawingArea()
        drawing_area.connect('draw', self.redraw)
        self.refresh_cnt = 0
        self.add(drawing_area)

        self.connect('destroy', lambda q: Gtk.main_quit())

        self.widgets = []

        self.show_all()

    def refresh(self, force=False):
        self.refresh_cnt += 1
        if self.refresh_cnt >= 60000:
            self.refresh_cnt = 0
        redraw_required = False
        for widget in self.widgets:
            if (self.refresh_cnt % widget.metric.refresh_rate == 0) or force:
                widget.refresh()
                redraw_required = True
        if redraw_required:
            self.queue_draw()
        return True

    def redraw(self, _, ctx):
        ctx.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
        for widget in self.widgets:
            widget.redraw(ctx, self)


class Widget:

    def __init__(self,
                 name='default',
                 metric={'plugin': 'time'},
                 indicator={'plugin': 'arc'},
                 fill={'plugin': 'rgba_255'},
                ):
        self.name = name
        MetricPlugin = plugin.load_plugin('metrics', metric.pop('plugin'))
        self.metric = MetricPlugin(**metric)
        IndicatorPlugin = plugin.load_plugin('indicators', indicator.pop('plugin'))
        self.indicator = IndicatorPlugin(**indicator)
        FillPlugin = plugin.load_plugin('fills', fill.pop('plugin'))
        self.fill = FillPlugin(**fill)

    def refresh(self):
        self.metric.refresh(self)
        self.fill.refresh(self)

    def redraw(self, ctx, window):
        ctx.set_source(self.fill.pattern)
        self.indicator.redraw(ctx, window, self)
