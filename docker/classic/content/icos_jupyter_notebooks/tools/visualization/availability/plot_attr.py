#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    
    Description:      Class that creates objects to set the attributes of the
                      interactive availability plot.
                      The plot is created using Bokeh visualization library.
    
"""

__author__      = ["Karolina Pantazatou"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, elaborated products team"
__email__       = ['info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2020-10-13"






class PlotAttr():
    
    def __init__(self):
        
        #Plot size:
        self.width = 900
        self.height = 800
        self.y_range = None
        
        #Plot title:
        self.title_text = None
        self.title_font_size = '13pt'
        self.title_align = 'center'
        self.title_offset = 15
        
        #Plot xaxis label:
        self.xaxis_label = None
        self.xaxis_label_font_style = 'normal'
        self.xaxis_label_standoff = 15
        
        #Plot yaxis label:
        self.yaxis_label = None
        self.yaxis_label_font_style = 'normal'
        self.yaxis_label_standoff = 15
        self.yaxis_label_text_font_size = '8pt'
                
        #Dataframe column name for x- & y-axis:
        self.col_name_xaxis = None
        self.col_name_yaxis = None
        
        #Plot rectangle glyph:
        self.rect_width = 0.07
        self.rect_height = 0.15
        self.rect_fill_alpha = 0.5
        self.rect_dodge_x = 0.03
        self.rect_dodge_y = 0.03
        
        #Plot legend:
        self.legend_location = 'bottom_center'
        self.legend_position = 'below'
        self.legend_orientation = 'horizontal'
        self.legend_spacing = 10
        self.legend_click_policy = 'hide'
    
    
    #-------------------------------------
    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, width):
        self._width = width
    
    #-------------------------------------
    @property
    def height(self):
        return self._height
    
    @height.setter
    def height(self, height):
        self._height = height
    
    #-------------------------------------
    @property
    def y_range(self):
        return self._y_range
    
    @y_range.setter
    def y_range(self, y_range):
        self._y_range = y_range
    
    #-------------------------------------
    @property
    def title_text(self):
        return self._title_text
    
    @title_text.setter
    def title_text(self, title_text):
        self._title_text = title_text
        
    #-------------------------------------
    @property
    def title_font_size(self):
        return self._title_font_size
    
    @title_font_size.setter
    def title_font_size(self, title_font_size):
        self._title_font_size = title_font_size
    
    #-------------------------------------
    @property
    def title_align(self):
        return self._title_align
    
    @title_align.setter
    def title_align(self, title_align):
        self._title_align = title_align
    
    #-------------------------------------
    @property
    def title_offset(self):
        return self._title_offset
    
    @title_offset.setter
    def title_offset(self, title_offset):
        self._title_offset = title_offset
        
    #-------------------------------------
    @property
    def xaxis_label(self):
        return self._xaxis_label
    
    @xaxis_label.setter
    def xaxis_label(self, xaxis_label):
        self._xaxis_label = xaxis_label
        
    #-------------------------------------
    @property
    def xaxis_label_font_style(self):
        return self._xaxis_label_font_style
    
    @xaxis_label_font_style.setter
    def xaxis_label_font_style(self, xaxis_label_font_style):
        self._xaxis_label_font_style = xaxis_label_font_style
        
    #-------------------------------------
    @property
    def xaxis_label_standoff(self):
        return self._xaxis_label_standoff
    
    @xaxis_label_standoff.setter
    def xaxis_label_standoff(self, xaxis_label_standoff):
        self._xaxis_label_standoff = xaxis_label_standoff

    #-------------------------------------
    @property
    def yaxis_label(self):
        return self._yaxis_label
    
    @yaxis_label.setter
    def yaxis_label(self, yaxis_label):
        self._yaxis_label = yaxis_label
        
    #-------------------------------------
    @property
    def yaxis_label_font_style(self):
        return self._yaxis_label_font_style
    
    @yaxis_label_font_style.setter
    def yaxis_label_font_style(self, yaxis_label_font_style):
        self._yaxis_label_font_style = yaxis_label_font_style
        
    #-------------------------------------
    @property
    def yaxis_label_standoff(self):
        return self._yaxis_label_standoff
    
    @yaxis_label_standoff.setter
    def yaxis_label_standoff(self, yaxis_label_standoff):
        self._yaxis_label_standoff = yaxis_label_standoff
        
    #-------------------------------------
    @property
    def yaxis_label_text_font_size(self):
        return self._yaxis_label_text_font_size
    
    @yaxis_label_text_font_size.setter
    def yaxis_label_text_font_size(self, yaxis_label_text_font_size):
        self._yaxis_label_text_font_size = yaxis_label_text_font_size
        
    #-------------------------------------
    @property
    def col_name_xaxis(self):
        return self._col_name_xaxis
    
    @col_name_xaxis.setter
    def col_name_xaxis(self, col_name_xaxis):
        self._col_name_xaxis = col_name_xaxis
    
    #-------------------------------------
    @property
    def col_name_yaxis(self):
        return self._col_name_yaxis
    
    @col_name_yaxis.setter
    def col_name_yaxis(self, col_name_yaxis):
        self._col_name_yaxis = col_name_yaxis
        
    #-------------------------------------
    @property
    def rect_width(self):
        return self._rect_width
    
    @rect_width.setter
    def rect_width(self, rect_width):
        self._rect_width = rect_width
    
    #-------------------------------------
    @property
    def rect_height(self):
        return self._rect_height
    
    @rect_height.setter
    def rect_height(self, rect_height):
        self._rect_height = rect_height

    #-------------------------------------
    @property
    def rect_fill_alpha(self):
        return self._rect_fill_alpha
    
    @rect_fill_alpha.setter
    def rect_fill_alpha(self, rect_fill_alpha):
        self._rect_fill_alpha = rect_fill_alpha
    
    #-------------------------------------
    @property
    def rect_dodge_x(self):
        return self._rect_dodge_x
    
    @rect_dodge_x.setter
    def rect_dodge_x(self, rect_dodge_x):
        self._rect_dodge_x = rect_dodge_x
    
    #-------------------------------------
    @property
    def rect_dodge_y(self):
        return self._rect_dodge_y
    
    @rect_dodge_y.setter
    def rect_dodge_y(self, rect_dodge_y):
        self._rect_dodge_y = rect_dodge_y

    #-------------------------------------
    @property
    def legend_location(self):
        return self._legend_location
    
    @legend_location.setter
    def legend_location(self, legend_location):
        self._legend_location = legend_location

    #-------------------------------------
    @property
    def legend_position(self):
        return self._legend_position
    
    @legend_position.setter
    def legend_position(self, legend_position):
        self._legend_position = legend_position

    #-------------------------------------
    @property
    def legend_orientation(self):
        return self._legend_orientation
    
    @legend_orientation.setter
    def legend_orientation(self, legend_orientation):
        self._legend_orientation = legend_orientation

    #-------------------------------------
    @property
    def legend_spacing(self):
        return self._legend_spacing
    
    @legend_spacing.setter
    def legend_spacing(self, legend_spacing):
        self._legend_spacing = legend_spacing
        
    #-------------------------------------
    @property
    def legend_click_policy(self):
        return self._legend_click_policy
    
    @legend_click_policy.setter
    def legend_click_policy(self, legend_click_policy):
        self._legend_click_policy = legend_click_policy
