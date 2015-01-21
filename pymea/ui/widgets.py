from PySide import QtGui, QtCore  # noqa

class MEAViewerStatusBar(QtGui.QStatusBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text_fmt = 't0: %1.3f    dt: %1.3f    electrode: %s'
        self._t0 = 0
        self._dt = 0
        self._electrode = ''

    @property
    def t0(self):
        return self._t0

    @t0.setter
    def t0(self, val):
        self._t0 = val
        self._update()

    @property
    def dt(self):
        return self._dt

    @dt.setter
    def dt(self, val):
        self._dt = val
        self._update()

    @property
    def electrode(self):
        return self._electrode

    @electrode.setter
    def electrode(self, val):
        self._electrode = val.upper()
        self._update()

    def _update(self):
        self.showMessage(self._text_fmt %
                         (self._t0, self._dt, self._electrode))
