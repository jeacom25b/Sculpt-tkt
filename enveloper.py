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
import json
import bmesh
from mathutils import Vector
from . import envelopeloader


class ArmatureMesser:
    _ball_model = None

    def __init__(self, armature):
        if not armature.type == "ARMATURE":
            raise ValueError(str(armature) + " is not an armature objec")

        else:
            self.armature = armature

    @classmethod
    def __load_mesh_ball(cls):

        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), r"objects", r"ball.json")
        if not cls._ball_model:
            with open(path, "r") as ball_model:
                data = json.loads(ball_model.read())
            cls._ball_model = data
            return data
        else:
            return cls._ball_model

    def __get_balls(self, bone, step_size=0.1, min_step_num=10):
        current_step_size = step_size
        if bone.length / step_size < min_step_num:
            current_step_size = bone.length / min_step_num

        total_steps = int(bone.length / current_step_size)

        for i in range(total_steps + 1):

            factor = (1 / total_steps) * i
            if type(bone) == bpy.types.EditBone:
                ball_location = bone.head.lerp(bone.tail, factor)
            else:
                ball_location = bone.head_local.lerp(bone.tail_local, factor)

            ball_location.rotate(self.armature.matrix_world)
            ball_location += self.armature.location
            ball_radius = (bone.head_radius * (1 - factor)) + (bone.tail_radius * factor)

            yield ball_location, ball_radius

    def convert(self, step_size=0.1, min_step_num=10, resolution=0.2, radius_multiplier=1):

        bpy.ops.object.metaball_add(type="BALL", location=Vector((0, 0, 0)))
        bpy.context.active_object.name = self.armature.name + ".Mesh"
        meta = bpy.context.active_object.data
        meta.threshold = 0.00000000001
        meta.elements.remove(meta.elements[0])

        for bone in self.armature.data.bones:

            current_step_size = step_size
            if bone.length / step_size < min_step_num:
                current_step_size = bone.length / min_step_num

            total_steps = int(bone.length / current_step_size)

            for ball_location, ball_radius in self.__get_balls(bone, step_size, min_step_num):
                element = meta.elements.new()
                element.co = ball_location
                element.radius = ball_radius * radius_multiplier

        bpy.context.active_object.data.resolution = resolution
        bpy.ops.object.convert(target="MESH")

class ConvertEnvelopeToMesh(bpy.types.Operator):
    bl_idname = "sculptkt.convert_envelope_to_mesh"
    bl_label = "Convert Envelope To Mesh"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    delete_original = bpy.props.BoolProperty(
        name="Delete Original",
        description="delete original armature after converting",
        default=True

    )

    resolution = bpy.props.FloatProperty(
        name="Resolution",
        description="The metaball resolution",
        default=200
    )

    step_size = bpy.props.FloatProperty(
        name="Step Size",
        description="The amount of spacing between each sample.",
        default=0.02,
        min=0.01
    )

    min_steps = bpy.props.IntProperty(
        name="Minimun steps",
        description="The minimus amount od steps per bone.",
        default=10
    )

    radius_multiplier = bpy.props.FloatProperty(
        name="Radius Multiplier",
        description="Alter the overall thickness of the resulting mesh",
        default=1
    )

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object.type in ["ARMATURE", "MESH"]

    def execute(self, context):

        if not context.active_object.type == "ARMATURE":
            return {"CANCELLED"}

        armature = context.active_object
        converter = ArmatureMesser(armature)
        converter.convert(self.step_size, self.min_steps, 1 / self.resolution * max(armature.dimensions), self.radius_multiplier)

        last_cursor_pos = context.scene.cursor_location
        context.scene.cursor_location = armature.location
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        context.scene.cursor_location = last_cursor_pos

        if self.delete_original:
            bpy.data.armatures.remove(armature.data)
            bpy.data.objects.remove(armature)

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class AddEnvelopeArmature(bpy.types.Operator):
    bl_idname = "sculptkt.add_envelope_armature"
    bl_label = "Add Envelope Armature"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    use_mirror_x = bpy.props.BoolProperty(
        name="Use X mirror",
        description="Enable X mirror in armature"
    )

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.object.armature_add()
        context.active_object.name = "Envelope_thing"
        context.active_object.data.use_mirror_x = self.use_mirror_x
        context.active_object.data.draw_type = "ENVELOPE"
        context.active_object.is_envelope_builder = True
        return {"FINISHED"}


class AddEnvelopeHuman(bpy.types.Operator):
    bl_idname = "sculptkt.add_envelope_human"
    bl_label = "Add Envelope Human"
    bl_description = "Adds a armature human figure for creating basemeshes"
    bl_options = {"REGISTER", "UNDO"}

    gender = bpy.props.EnumProperty(
        name="Gender",
        description="Choose the gender of the base armature",
        items=[
            ("MALE", "Male", "Male"),
            ("NEUTRAL", "Neutral", "Neutral"),
            ("FEMALE", "Female", "Female"),
            ("HERO", "Hero", "Hero")
        ],
        default="NEUTRAL"
    )

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), r"objects", "human_fig.blend")
        object_name = "Envelope_Human_{}".format(self.gender)

        with bpy.types.BlendDataLibraries.load(path) as (data_from, data_to):
            data_to.objects.append(object_name)
        data_to.objects[0].location = context.scene.cursor_location

        data_to.objects[0].name = "Envelope_Human"
        data_to.objects[0].is_envelope_builder = True

        bpy.context.scene.objects.link(data_to.objects[0])
        bpy.context.scene.objects.active = data_to.objects[0]

        return {"FINISHED"}
