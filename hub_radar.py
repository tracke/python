"""
======================================
Radar chart (aka spider or star chart)
======================================

This example creates a radar chart, also known as a spider or star chart [1]_.

Although this example allows a frame of either 'circle' or 'polygon', polygon
frames don't have proper gridlines (the lines are circles instead of polygons).
It's possible to get a polygon grid by setting GRIDLINE_INTERPOLATION_STEPS in
matplotlib.axis to the desired number of vertices, but the orientation of the
polygon is not aligned with the radial axes.

.. [1] http://en.wikipedia.org/wiki/Radar_chart
"""
from __future__ import print_function  #must be 1st
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.spines import Spine
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
plt.ion()
frame='circle'


class HubRadar(object):
    def __init__(self):
        self.N=8
        self.nrows=2
        self.ncols = 3
        self.frame='circle'
        pass

    def __call__(self,data):
        print("calling plot for ",self.N,"Nodes")
        self.on_launch(data)
        self.on_running(data)

        

    def radar_factory(self):
        """Create a radar chart with `num_vars` axes.
    
        This function creates a RadarAxes projection and registers it.
    
        Parameters
        ----------
        num_vars : int
            Number of variables for radar chart.
        frame : {'circle' | 'polygon'}
            Shape of frame surrounding axes.
    
        """
        # calculate evenly-spaced axis angles
        theta = np.linspace(0, 2*np.pi, self.N, endpoint=False)
        # rotate theta such that the first axis is at the top
        theta += np.pi/2
    
        def draw_poly_patch(self):
            verts = unit_poly_verts(theta)
            return plt.Polygon(verts, closed=True, edgecolor='k')
    
        def draw_circle_patch(self):
            # unit circle centered on (0.5, 0.5)
            return plt.Circle((0.5, 0.5), 0.5)
    
        patch_dict = {'polygon': draw_poly_patch, 'circle': draw_circle_patch}
        if self.frame not in patch_dict:
            raise ValueError('unknown value for `frame`: %s' % self.frame)
 
        class RadarAxes(PolarAxes):
            name = 'radar'
            # use 1 line segment to connect specified points
            RESOLUTION = 1
            # define draw_frame method
            draw_patch = patch_dict[frame]
    
            def fill(self, *args, **kwargs):
                """Override fill so that line is closed by default"""
                closed = kwargs.pop('closed', True)
                return super(RadarAxes, self).fill(closed=closed, *args, **kwargs)
    
            def plot(self, *args, **kwargs):
                """Override plot so that line is closed by default"""
                lines = super(RadarAxes, self).plot(*args, **kwargs)
                for line in lines:
                    self._close_line(line)
    
            def _close_line(self, line):
                x, y = line.get_data()
                # FIXME: markers at x[0], y[0] get doubled-up
                if x[0] != x[-1]:
                    x = np.concatenate((x, [x[0]]))
                    y = np.concatenate((y, [y[0]]))
                    line.set_data(x, y)
    
            def set_varlabels(self, labels):
                self.set_thetagrids(np.degrees(theta), labels)
    
            def _gen_axes_patch(self):
                return self.draw_patch()
    
            def _gen_axes_spines(self):
                if frame == 'circle':
                    return PolarAxes._gen_axes_spines(self)
                # The following is a hack to get the spines (i.e. the axes frame)
                # to draw correctly for a polygon frame.
    
                # spine_type must be 'left', 'right', 'top', 'bottom', or `circle`.
                spine_type = 'circle'
                verts = unit_poly_verts(theta)
                # close off polygon by repeating first vertex
                verts.append(verts[0])
                path = Path(verts)
    
                spine = Spine(self, spine_type, path)
                spine.set_transform(self.transAxes)
                return {'polar': spine}
        
        register_projection(RadarAxes)
        return theta
    
    
    def unit_poly_verts(theta):
        """Return vertices of polygon for subplot axes.
    
        This polygon is circumscribed by a unit circle centered at (0.5, 0.5)
        """
        x0, y0, r = [0.5] * 3
        verts = [(r*np.cos(t) + x0, r*np.sin(t) + y0) for t in theta]
        return verts


    def on_running(self,data):
        print("on running...")
        #Update data (with the new _and_ the old points)
        for ax, (title, case_data) in zip(axes.flatten(), data):
            ax.set_rgrids([5, 10, 20, 30])
            ax.set_title(title, weight='bold', size='medium', position=(0.5, 1.1),
                    horizontalalignment='center', verticalalignment='center')
        for d, color in zip(case_data, colors):
            ax.plot(theta, d, color=color)
            ax.fill(theta, d, facecolor=color, alpha=0.25)
        print("label spokes")    
        ax.set_varlabels(spoke_labels)
        #Need both of these in order to rescale
        ax.relim()
        ax.autoscale_view()
        #We need to draw *and* flush
        fig.canvas.draw()
        time.sleep(3)
        fig.canvas.flush_events()
        pass

 



    def on_launch(self,data):
        theta = self.radar_factory()        
        spoke_labels = data[0]#.pop(0)
        print("labels:",spoke_labels) 
        print("nrows=",self.nrows," ncols=",self.ncols)
        fig, axes = plt.subplots(figsize=(12, 9), nrows=self.nrows, ncols=self.ncols,
                                subplot_kw=dict(projection='radar'))
        fig.subplots_adjust(wspace=0.25, hspace=0.20, top=0.85, bottom=0.05)
    
        colors = ['b', 'r', 'g', 'm', 'y','k','c']
        # Plot the four cases from the example data on separate axes
        #for ax, (title, case_data) in zip(axes.flatten(), data[1]):
        for a in range(len(data[1])):
            ax=axes[a]
            title=data[1][a][0]
            case_data=data[1][a][1]
            print(title,"->",case_data,"->",ax)
            ax.set_rgrids([5, 10, 20, 30])
            ax.set_title(title, weight='bold', size='medium', position=(0.5, 1.1),
                        horizontalalignment='center', verticalalignment='center')
            for i in range(len(case_data)):        #d, color in zip(case_data, colors):
                d=case_data[i]
                c=i%len(colors)
                color=colors[c]
                ax.plot(theta, d, color=color)
                ax.fill(theta, d, facecolor=color, alpha=0.25)
            ax.set_varlabels(spoke_labels)
            print("done with",ax)


        # add legend relative to top-left plot
        ax = axes[0, 0]
        labels = ('Factor 1', 'Factor 2', 'Factor 3', 'Factor 4', 'Factor 5')
        legend = ax.legend(labels, loc=(0.9, .95),labelspacing=0.1, fontsize='small')
    
        fig.text(0.5, 0.965, 'Adjacent Node Distances per RSSI Reporting',
                horizontalalignment='center', color='black', weight='bold',
                size='large')
        print("done with on_launch")
    