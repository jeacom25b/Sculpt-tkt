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

bl_info = {
    "name": "SculpTKt",
    "description": "Sculpting and Boolean utils",
    "author": "Jean Da Costa Machado",
    "version": (1, 0, 4),
    "blender": (2, 79, 0),
    "wiki_url": "",
    "category": "Sculpt",
    "location": "3D View > Tool shelf > Sculptkt \  Alt + W"}

import bpy

# load and reload submodules
##################################

modules = [
    "booleans",
    "remesh_optimized",
    "enveloper",
    "ui_panels",
    "ui_menus",
    "lightloader",
    "envelopeloader",
    "mask_tools",
    "display_operators",
    "utils",
]

import importlib

imported_modules = []

for module in modules:
    if module in locals():
        importlib.reload(locals()[module])
    else:
        exec("from . import %s" % module)
        imported_modules.append(locals()[module])
import bpy


# menus
#################################

def add_envelope_armature(self, context):
    self.layout.operator("sculptkt.add_envelope_armature",
                         text="Envelope Bone", icon="BONE_DATA")
    self.layout.operator("sculptkt.add_envelope_human",
                         text="Envelope Human Base", icon="BONE_DATA")


# register
##################################


import traceback

keymaps = []


def register():
    try:
        bpy.utils.register_module(__name__)

        for module in imported_modules:
            try:
                module.register()
            except AttributeError:
                pass

        bpy.types.INFO_MT_armature_add.prepend(add_envelope_armature)

        bpy.types.Scene.slash_cut_thickness = bpy.props.FloatProperty(
            name="Cut Thickness",
            description="The spacing of the cut though the mesh",
            default=0.001,
            min=0.000001
        )

        bpy.types.Scene.slash_cut_distance = bpy.props.FloatProperty(
            name="Cut Distance",
            description="The distance the cut spams over the stroke location",
            default=50,
            min=0.000001
        )

        bpy.types.Scene.slash_boolean_solver = bpy.props.EnumProperty(
            name="Solver",
            description="Which method to use, Carve fails less often but is slower",
            items=[("BMESH", "Bmesh", "Bmesh"), ("CARVE", "Carve", "Carve")],
            default="CARVE"
        )

        bpy.types.Scene.multi_boolean_solver = bpy.props.EnumProperty(
            name="Solver",
            description="Which method to use, Carve fails less often but is slower",
            items=[("BMESH", "Bmesh", "Bmesh"), ("CARVE", "Carve", "Carve")],
            default="BMESH"
        )

        bpy.types.Scene.use_slash_ciclic = bpy.props.BoolProperty(
            name="Closed Ends",
            description="Make closed ends. (Usefull for digging holes on meshes)",
            default=False

        )

        bpy.types.Scene.lightloader_preset = bpy.props.EnumProperty(
            name="Preset",
            description="Which solid lighting preset to choose from",
            items=lightloader.list_presets_callback,
            update=lambda self, context: lightloader.load_unpack(
                context.scene.lightloader_preset)
        )

        bpy.types.Scene.decimate_factor = bpy.props.FloatProperty(
            name="Ratio",
            description="How much to recuce",
            default=0.7,
            min=0.0000001,
            max=1.0
        )

        bpy.types.Scene.remesh_depth = bpy.props.IntProperty(
            name="Octree Depth",
            description="resolution of the new mesh",
            default=4,
            min=0
        )

        bpy.types.Scene.envelope_preset = bpy.props.EnumProperty(
            name="Envelope Preset",
            description="The base armature.",
            items=lambda self, context: [(item, item, "") for item in envelopeloader.get_filenames()]
        )

        bpy.types.Object.is_envelope_builder = bpy.props.BoolProperty(default=False)

        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="3D View", space_type="VIEW_3D")
        keymaps.append(km)

        kmi = km.keymap_items.new("wm.call_menu_pie", type="W", alt=True, value="PRESS")
        kmi.properties.name = "OBJECT_MT_flow_tools"
    except:
        traceback.print_exc()


def unregister():
    try:
        for module in imported_modules:
            try:
                module.unregister()
            except AttributeError:
                pass

        bpy.utils.unregister_module(__name__)
        del bpy.types.Scene.slash_cut_thickness
        del bpy.types.Scene.slash_cut_distance
        del bpy.types.Scene.slash_boolean_solver
        del bpy.types.Scene.multi_boolean_solver
        del bpy.types.Scene.lightloader_preset
        del bpy.types.Scene.decimate_factor
        del bpy.types.Scene.use_slash_ciclic
        del bpy.types.Scene.remesh_depth
        del bpy.types.Object.is_envelope_builder

        for km in keymaps:
            bpy.context.window_manager.keyconfigs.addon.keymaps.remove(km)

        bpy.types.INFO_MT_add.remove(add_envelope_armature)
    except:
        traceback.print_exc()
