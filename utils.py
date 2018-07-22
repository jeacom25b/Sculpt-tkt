'''
Copyright (C) 2018 Jean Da Costa machado.
Jean3dimensional@gmail.com

Created by Jean Da Costa machado

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import bpy

# A decorator that enables a operator to work with dyntopo.
def dyntopo_compatible_execute (func):
    
    def execute (self, context):
        
        dyntopo = False
        if bpy.context.active_object.mode == "SCULPT":
            if bpy.context.active_object.use_dynamic_topology_sculpting:
                dyntopo = True
                bpy.ops.sculpt.dynamic_topology_toggle()
        
        return_value = func (self, context)
        
        if dyntopo:
            bpy.ops.sculpt.dynamic_topology_toggle()
        
        return return_value
    return execute


def sculptmode_compatible(func):
    
    def execute (self, context):
        
        sculpt = False
        
        if context.active_object.mode == "SCULPT":
            bpy.ops.object.mode_set(mode="OBJECT")
            sculpt = True
        
        return_value = func(self, context)
        
        if sculpt:
            bpy.ops.object.mode_set(mode="SCULPT")
        
        return return_value
    return execute
