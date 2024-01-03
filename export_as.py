#! /usr/bin/env python

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Author: Jan Pavelka https://www.phoca.cz
# Version: 1.0

# Inspired by, based on:

# https://github.com/giacmir/Inkscape-JPEG-export-extension
# Author: Giacomo Mirabassi <giacomo@mirabassi.it>
# Version: 0.2

#https://github.com/Moini/Inkscape-JPEG-export-extension-webp
# Authors: Giacomo Mirabassi <giacomo@mirabassi.it>, Maren Hachmann <marenhachmann@yahoo.com>
# Version: 0.3


import sys
import os
import re
import subprocess
import math
import inkex
import tempfile
from distutils.spawn import find_executable
from subprocess import PIPE, Popen
from inkex.command import call
inkex.localization.localize

class ExportAs(inkex.Effect):

    def __init__(self):
        inkex.Effect.__init__(self)

        self.arg_parser.add_argument("--tab")
        self.arg_parser.add_argument("--path",                  action="store", type=str,             dest="path",                  default="")
        self.arg_parser.add_argument("--quality",               action="store", type=int,             dest="quality",               default="100")
        self.arg_parser.add_argument("--resize",                action="store", type=int,             dest="resize",                default="100")
        self.arg_parser.add_argument("--dpi",                   action="store", type=int,             dest="dpi",                   default="96")
        self.arg_parser.add_argument("--bg_color",              action="store", type=inkex.Color,     dest="bg_color",              default='rgba(0, 0, 0, 0)')
        self.arg_parser.add_argument("--format",                action="store", type=str,             dest="format",                default="jpg")
        #self.arg_parser.add_argument("--export_area",          action="store", type=inkex.Boolean,   dest="export_area",           default=False)
        self.arg_parser.add_argument("--x",                     action="store", type=float,           dest="x",                     default="")
        self.arg_parser.add_argument("--y",                     action="store", type=float,           dest="y",                     default="")
        self.arg_parser.add_argument("--w",                     action="store", type=float,           dest="w",                     default="")
        self.arg_parser.add_argument("--h",                     action="store", type=float,           dest="h",                     default="")
        self.arg_parser.add_argument("--units",                 action="store",                       dest="units",                 default="1.")
        self.arg_parser.add_argument("--export_area_type",      action="store", type=int,             dest="export_area_type",      default=1)
        self.arg_parser.add_argument("--bg_transparent_color",  action="store", type=inkex.Boolean,   dest="bg_transparent_color",  default=False)

    def effect(self):
       
        opt                         = self.options
        self.options.temp_file      = tempfile.gettempdir() + "/phocaExportAs.png"
        self.options.source_file    = opt.input_file
        self.options.dest_file      = opt.path

        # Set background color
        bg_color_rgba = inkex.Color(opt.bg_color).to_rgba()

        # Transparent background color was selected
        if str(bg_color_rgba) == "rgba(0, 0, 0, 0)" or str(bg_color_rgba) == "rgba(0,0,0,0)" or str(bg_color_rgba) == "ffffff00" or str(bg_color_rgba) == "#ffffff00" :
            self.options.bg_transparent_color = True

            # If transparent background color but format is jpg then force white as background color
            if opt.format == 'jpg':
                self.options.bg_transparent_color = False
                self.options.bg_color = '#ffffff'
        
        # Standard color (no transparent) was selected
        else:
            self.options.bg_color = str(inkex.Color(opt.bg_color).to_rgb())


        if not self.options.path: 
            inkex.errormsg(_('Please set filename with full path'))
            sys.exit()
        
        if not os.path.basename(self.options.path):
            inkex.errormsg(_('Please select a filename'))
            sys.exit()
        
        if not os.path.dirname(self.options.path):
            inkex.errormsg(_('Please select a directory other than your system\'s base directory'))
            sys.exit()

        # Test if the directory exists:
        if not os.path.exists(os.path.dirname(self.options.path)):
            inkex.errormsg(_('Directory "{}" does not exist').format(os.path.dirname(self.options.path)))
            sys.exit()

        # Test if color is valid
        if not self.options.bg_transparent_color:
            _rgbhexstring = re.compile(r'#[a-fA-F0-9]{6}$')
            if not _rgbhexstring.match(self.options.bg_color):
                inkex.errormsg(_('Please select background color'))
                sys.exit()

        self.export()


    def custom_area(self):
        
        opt = self.options
        scale = eval(opt.units)

        x0 = y0 = y1 = x0 = None

        #h = math.ceil(self.svg.height / scale)
        #w = math.ceil(self.svg.width / scale)
        
        x0 = math.ceil(opt.x / scale)
        y0 = math.ceil(opt.y / scale)
        x1 = x0 + math.ceil(opt.w / scale)
        y1 = y0 + math.ceil(opt.h / scale)

        '''
        if (x0 > w):
            x0 = w
        if (x1 > w):
            x1 = w
        if (y0 > h):
            y0 = h
        if (y1 > h):
            y1 = h
        '''
        points = [x0, y0, x1, y1]
        return points


    def objects_to_paths(self, elements, replace=True):
        for node in list(elements.values()):
            elem = node.to_path_element() 
            if replace:
                node.replace_with(elem)
                elem.set('id', node.get('id'))
            elements[elem.get('id')] = elem
              

    def select_area(self):

        opt = self.options
        x0 = y0 = y1 = x0 = None
        scale       = self.svg.unittouu('1px')
        # convert objects to path to not wrongly count the selection.bounding.box()
        self.objects_to_paths(self.svg.selected, True)
        bbox        = self.svg.selection.bounding_box()
    
        x0 = math.ceil(bbox.left/scale)
        x1 = math.ceil(bbox.right/scale)
        y0 = math.ceil(bbox.top/scale)
        y1 = math.ceil(bbox.bottom/scale)
        points = [x0, y0, x1, y1]
        return points
    
    def export(self):

        # https://gitlab.com/inkscape/inkscape/-/issues/4163
        os.environ["SELF_CALL"] = "true"

        opt = self.options
        filename, file_extension = os.path.splitext(opt.dest_file)

        # Create PNG with inkscape
        cmd = ['inkscape']
        cmd.append("-C")

        # Add background parameter or not
        if not opt.bg_transparent_color:
            cmd.append("-b")
            cmd.append("\"{}\"".format(opt.bg_color))

        # which area to export
        if opt.export_area_type == 3:
            c = self.custom_area()
            cmd.append("--export-area ")
            cmd.append("{}:{}:{}:{}".format(c[0], c[1], c[2], c[3]))
        
        elif opt.export_area_type == 2:

            if len(self.svg.selected) == 0:
                inkex.errormsg(_('Please select some object or change parameter'))
                sys.exit()

            c = self.select_area()
            cmd.append("--export-area ")
            cmd.append("{}:{}:{}:{}".format(c[0], c[1], c[2], c[3]))

        '''
        # Create directly png
        if opt.format == "png":

            # Correct extension
            opt.dest_file = filename + '.png'

            command = "inkscape{} -C -d {} --export-filename \"{}\"{} \"{}\"".format(parameter_area, opt.dpi, opt.dest_file, parameter_background, opt.source_file)

            p = subprocess.Popen(command, shell=True)
            p.wait()
            sys.exit()
        
        # Create temp image for jpg, webp, ...
        else:
            inkex.utils.debug("x:" + str(x))
        '''

        cmd.append("-d")
        cmd.append(str(opt.dpi))
        cmd.append("--export-filename")
        cmd.append("\"{}\"".format(opt.temp_file))
        cmd.append("\"{}\"".format(opt.source_file))
        cmd = ' '.join(cmd)
        
        p = subprocess.Popen(cmd, shell=True)
        p.wait()

        '''
        p = subprocess.Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        rc = p.wait()
        f = p.stdout
        err = p.stderr
        f.close()
        err.close()
        '''
       
        cmd_export = []
        # Which command will be used
        if find_executable('magick'):
            cmd_export.append('magick')
        elif find_executable('convert'):
            if os.name == 'nt': # convert on windows is different program
                inkex.errormsg(_('Please check if Imagemagick library is installed on your system'))
                sys.exit()
            cmd_export.append('convert')
        else:
            inkex.errormsg(_('Please check if Imagemagick library is installed on your system'))
            sys.exit()

        if opt.format == 'png':
            
            # Doing PNG again because of different parameters in imagemagick
            # Correct extension
            opt.dest_file = filename + '.png'
            cmd_export.append("\"{}\"".format(opt.temp_file))
            cmd_export.append("-sampling-factor")
            cmd_export.append("4:4:4")
            cmd_export.append("-strip")
            cmd_export.append("-interlace")
            cmd_export.append("PNG")
            # cmd_export.append("-colorspace")
            # cmd_export.append("RGB")
            cmd_export.append("-resize")
            cmd_export.append("{}%".format(opt.resize))
            cmd_export.append("-quality")
            cmd_export.append(str(opt.quality))
            cmd_export.append("-density")
            cmd_export.append(str(opt.dpi))
            cmd_export.append("\"{}\"".format(opt.dest_file))

        elif opt.format == "jpg":
            
            # Correct extension
            opt.dest_file = filename + '.jpg'
            cmd_export.append("\"{}\"".format(opt.temp_file))
            cmd_export.append("-sampling-factor")
            cmd_export.append("4:4:4")
            cmd_export.append("-strip")
            cmd_export.append("-interlace")
            cmd_export.append("JPEG")
            # cmd_export.append("-colorspace")
            # cmd_export.append("RGB")
            cmd_export.append("-resize")
            cmd_export.append("{}%".format(opt.resize))
            cmd_export.append("-quality")
            cmd_export.append(str(opt.quality))
            cmd_export.append("-density")
            cmd_export.append(str(opt.dpi))
            cmd_export.append("\"{}\"".format(opt.dest_file))
           
        elif opt.format == "webp":
            
            # Correct extension
            opt.dest_file = filename + '.webp'
            cmd_export.append("\"{}\"".format(opt.temp_file))
            cmd_export.append("-define")
            cmd_export.append("webp:lossless=true")
            cmd_export.append("-resize")
            cmd_export.append("{}%".format(opt.resize))
            cmd_export.append("-quality")
            cmd_export.append(str(opt.quality))
            cmd_export.append("-density")
            cmd_export.append(str(opt.dpi))
            cmd_export.append("\"{}\"".format(opt.dest_file))

        elif opt.format == "avif":

            # Correct extension
            opt.dest_file = filename + '.avif'
            cmd_export.append("\"{}\"".format(opt.temp_file))
            cmd_export.append("-define")
            cmd_export.append("avif:lossless=true")
            cmd_export.append("-resize")
            cmd_export.append("{}%".format(opt.resize))
            cmd_export.append("-quality")
            cmd_export.append(str(opt.quality))
            cmd_export.append("-density")
            cmd_export.append(str(opt.dpi))
            cmd_export.append("\"{}\"".format(opt.dest_file))

        cmd_export = ' '.join(cmd_export)
        p = subprocess.Popen(cmd_export, shell=True)
        p.wait()

        inkex.errormsg("\n\n========================================\n")
        inkex.errormsg(_('Image "{}" exported').format(opt.dest_file))
        inkex.errormsg("\n========================================\n\n")
        sys.exit()



if __name__ == "__main__":
    ExportAs().run()
