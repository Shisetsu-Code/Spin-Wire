"""Persist user-sized desktop panes and columns independently of game evidence."""
import json
import tkinter as tk

class LayoutPreferences:
    def __init__(self, app, path):
        self.app, self.path = app, path
        self.panes = {name: getattr(app, name) for name in ('sections', 'workspace', 'middle', 'detail_panes')}
        self.pending = None
        app.bind('<ButtonRelease-1>', self.schedule, add='+')
        app.protocol('WM_DELETE_WINDOW', self.close)
        app.after(250, self.restore)

    def schedule(self, event=None):
        if self.pending is not None:
            self.app.after_cancel(self.pending)
        self.pending = self.app.after(300, self.save)

    def save(self):
        self.pending = None
        try:
            sizes = {}
            for name, pane in self.panes.items():
                extent = pane.winfo_width() if str(pane.cget('orient')) == 'horizontal' else pane.winfo_height()
                sizes[name] = [pane.sashpos(i) / max(1, extent) for i in range(len(pane.panes()) - 1)]
            value = {'geometry': self.app.geometry(), 'maximized': self.app.state() == 'zoomed', 'panes': sizes,
                     'columns': {column: self.app.tree.column(column, 'width') for column in ('#0', *self.app.tree['columns'])}}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
            temporary.replace(self.path)
        except (OSError, tk.TclError):
            pass

    def restore(self):
        # FlowFrame computes its requested height after the first layout pass.
        # Panedwindow otherwise retains the initial one-pixel allocation.
        self.app.update_idletasks()
        sections = self.panes['sections']
        position = 0
        for i, child in enumerate(sections.panes()[:-1]):
            position += self.app.nametowidget(child).winfo_reqheight()
            sections.sashpos(i, position)
            position = sections.sashpos(i) + 5
        detail = self.panes['detail_panes']
        children = detail.panes()
        if len(children) == 3:
            detail.sashpos(0, max(48, self.app.nametowidget(children[0]).winfo_reqheight()))
            detail.sashpos(1, max(80, detail.winfo_height() - self.app.nametowidget(children[2]).winfo_reqheight() - 5))
        try:
            value = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(value, dict):
                return
            geometry = value.get('geometry')
            if isinstance(geometry, str):
                self.app.geometry(geometry)
            if value.get('maximized') is True:
                self.app.state('zoomed')
            self.app.update_idletasks()
            for column, width in value.get('columns', {}).items():
                if column in ('#0', *self.app.tree['columns']) and isinstance(width, int) and 40 <= width <= 4000:
                    self.app.tree.column(column, width=width)
            for name, pane in self.panes.items():
                extent = pane.winfo_width() if str(pane.cget('orient')) == 'horizontal' else pane.winfo_height()
                fractions = value.get('panes', {}).get(name, [])
                if not isinstance(fractions, list):
                    continue
                for i, fraction in enumerate(fractions[:len(pane.panes())-1]):
                    if isinstance(fraction, (int, float)) and 0 <= fraction <= 1:
                        pane.sashpos(i, int(extent * fraction))
        except (OSError, ValueError, TypeError, AttributeError, tk.TclError):
            pass

    def close(self):
        self.save()
        self.app.destroy()
