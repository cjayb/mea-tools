# -*- coding: utf-8 -*-
# Copyright (c) 2015, UC Santa Barbara
# Hansma Lab, Kosik Lab
# Originally written by Daniel Bridges


import math

import numpy as np
from vispy import gloo
import OpenGL.GL as gl

from .base import Visualization, Theme
import pymea.util as util


class MEAAnalogVisualization(Visualization):
    VERTEX_SHADER = """
    attribute vec2 a_position;
    attribute float a_index;

    uniform vec4 u_color;
    uniform vec2 u_scale;
    uniform float u_pan;
    uniform float u_top_margin;
    uniform float u_height;
    uniform float u_adj_y_scale;

    varying vec4 v_color;
    varying float v_index;

    void main(void)
    {
        v_index = a_index;
        float y_offset = u_height * (a_index + 0.5);
        gl_Position = vec4(u_scale.x * (a_position.x - u_pan) - 1,
                           u_adj_y_scale * a_position.y + 1 - y_offset,
                           0.0, 1.0);
        v_color = u_color;
    }
    """

    FRAGMENT_SHADER = """
    varying vec4 v_color;
    varying float v_index;

    void main()
    {
        gl_FragColor = v_color;

        if (fract(v_index) > 0.0) {
            discard;
        }

    }
    """

    def __init__(self, canvas, data):
        self.canvas = canvas
        self.data = data
        self._t0 = 0
        self._dt = 20
        self._y_scale = 150
        self.mouse_t = 0
        self.electrode = ''
        self.electrodes = ['h11']  # l5, m5

        self.program = gloo.Program(self.VERTEX_SHADER,
                                    self.FRAGMENT_SHADER)
        self.program['u_pan'] = self._t0
        self.program['u_scale'] = (2.0/self._dt, 1/self._y_scale)
        self.program['u_top_margin'] = 20.0 * 2.0 / canvas.size[1]
        self.program['u_color'] = Theme.blue

        self.margin = {}
        self.margin['top'] = 20

        self.velocity = 0

        self.resample()

    @property
    def t0(self):
        return self._t0

    @t0.setter
    def t0(self, val):
        self._t0 = util.clip(val, 0 - self.dt/2,
                             self.data.index[-1] - self.dt/2)
        self.update()

    @property
    def dt(self):
        return self._dt

    @dt.setter
    def dt(self, val):
        self._dt = util.clip(val, 0.0025, 20)
        self.update()

    @property
    def y_scale(self):
        return self._y_scale

    @y_scale.setter
    def y_scale(self, val):
        self._y_scale = val
        self.program['u_adj_y_scale'] = 1 / (
            self._y_scale * len(self.electrodes))
        self.program['u_height'] = 2.0 / len(self.electrodes)
        self.update()

    def draw(self):
        gloo.clear((0.5, 0.5, 0.5, 1))
        self.program.draw('line_strip')

    def resample(self):
        xs = []
        ys = []
        zs = []
        for i, e in enumerate(self.electrodes):
            x = self.data[e].index.values.astype(np.float32)
            y = self.data[e].values
            z = np.full_like(x, i)
            xs.append(x)
            ys.append(y)
            zs.append(z)
        self.program['a_position'] = np.column_stack((np.concatenate(xs),
                                                      np.concatenate(ys)))
        self.program['a_index'] = np.concatenate(zs)
        self.program['u_adj_y_scale'] = 1 / (
            self._y_scale * len(self.electrodes))
        self.program['u_height'] = 2.0 / len(self.electrodes)

    def update(self):
        self.program['u_pan'] = self.t0
        self.program['u_scale'] = (2.0 / self.dt, 1 / self._y_scale)

    def on_mouse_move(self, event):
        x, y = event.pos
        x1, y1 = event.last_event.pos
        sec_per_pixel = self.dt / self.canvas.size[0]
        if event.is_dragging:
            dx = x1 - x
            self.t0 += dx * sec_per_pixel
        self.mouse_t = self.t0 + sec_per_pixel * x

    def on_mouse_release(self, event):
        dx = self.canvas.mouse_pos[0] - self.canvas.prev_mouse_pos[0]
        self.velocity = self.dt * dx / self.canvas.size[0]

    def on_mouse_press(self, event):
        self.velocity = 0

    def on_mouse_wheel(self, event):
        sec_per_pixel = self.dt / self.canvas.size[0]
        rel_x = event.pos[0]

        target_time = rel_x * sec_per_pixel + self.t0
        dx = -np.sign(event.delta[1]) * 0.025
        self.dt *= math.exp(2.5 * dx)

        sec_per_pixel = self.dt / self.canvas.size[0]
        self.t0 = target_time - (rel_x * sec_per_pixel)

    def on_mouse_double_click(self, event):
        self.canvas.show_analog_grid()

    def on_resize(self, event):
        self.program['u_top_margin'] = (self.margin['top'] * 2.0 /
                                        self.canvas.size[1])

    def on_tick(self, event):
        self.velocity *= 0.98
        self.t0 -= self.velocity
        self.update()

    def on_show(self):
        self.canvas.disable_antialiasing()
        gl.glLineWidth(1.5)
        self.resample()

    def on_hide(self):
        self.velocity = 0