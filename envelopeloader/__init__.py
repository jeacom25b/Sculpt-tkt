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
import os

path = os.path.dirname(os.path.realpath(__file__))


def save_armature(name, armature):
    armature.name = name
    bpy.data.libraries.write(os.path.join(path, "{}.blend".format(name)), {armature}, fake_user=True)


def delete_armature(name):
    if name in get_filenames():
        os.remove(os.path.join(path, "{}.blend".format(name)))


def get_filenames():
    all_files = sorted(os.listdir(path))

    actual_presets = ["Choose a preset"]

    for item in all_files:
        if item.endswith(".blend"):
            if os.path.isfile(os.path.join(path, item)):
                actual_presets.append(item[:-len(".blend")])
    return actual_presets


class SaveArmature(bpy.types.Operator):
    bl_idname = "sculptkt.save_envelope_armature"
    bl_label = "Save Selected Armature"
    bl_description = ""
    bl_options = {"REGISTER"}

    name = bpy.props.StringProperty(
        name="Name",
        description="The preset name which you wanna save",
    )

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if context.active_object.type == "ARMATURE":
                return context.active_object.data.draw_type == "ENVELOPE"

    def execute(self, context):
        if self.name in get_filenames() or not self.name:
            return {"CANCELLED"}
        elif self.name == "Choose a preset":
            self.report({"ERROR"}, "Sorry, you cant save using this name, its used for internal stuff.")

        save_armature(self.name, context.active_object)
        return {"FINISHED"}


class LoadArmature(bpy.types.Operator):
    bl_idname = "sculptkt.load_envelope_armature"
    bl_label = "Load Envelope base"
    bl_description = "Load a saved Envelope Base"
    bl_options = {"REGISTER", "UNDO"}

    preset_name = bpy.props.EnumProperty(
        name="name",
        description="Which armature you wanna load",
        items=lambda self, context: [(item, item, "") for item in get_filenames()]
    )

    no_popup = bpy.props.BoolProperty(default=False)

    def invoke(self, context, event):
        if not self.no_popup:
            wm = context.window_manager
            return wm.invoke_props_popup(self, event)
        else:
            return self.execute(context)

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return True
        return True

    def execute(self, context):
        if self.preset_name == "Choose a prest":
            return {"CANCELLED"}

        filepath = os.path.join(path, "{}.blend".format(self.preset_name))
        if os.path.isfile(filepath):
            with bpy.data.libraries.load(filepath) as(data_from, data_to):
                data_to.objects = data_from.objects

            for ob in context.selected_objects:
                ob.select = False

            data_to.objects[0].location = context.scene.cursor_location
            data_to.objects[0].select = True
            context.scene.objects.link(data_to.objects[0])
            context.scene.objects.active = data_to.objects[0]
        else:
            return {"CANCELLED"}
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preset_name")


class DeleteArmature(bpy.types.Operator):
    bl_idname = "sculptkt.delete_envelope_armature"
    bl_label = "Delete Envelope Base"
    bl_description = ""
    bl_options = {"REGISTER"}

    preset_name = bpy.props.StringProperty(
        name="Name"
    )

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if self.preset_name in get_filenames():
            delete_armature(self.preset_name)
            return {"FINISHED"}
        else:
            return {"CANCELLED"}
