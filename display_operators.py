import bpy
from random import random
from mathutils import Color


class ToggleWire(bpy.types.Operator):
    bl_idname = "sculptkt.toggle_wire"
    bl_label = "Toggle Wire"
    bl_description = "Toggle Wire display in the selected objects."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object.type == "MESH"

    def execute(self, context):

        wire_mode = context.active_object.show_wire

        for object in context.selected_objects:
            object.show_wire = not wire_mode
            object.show_all_edges = not wire_mode
        return {"FINISHED"}


class RandomColors(bpy.types.Operator):
    bl_idname = "sculptkt.random_colors"
    bl_label = "Random Colors"
    bl_description = "Random Object Colors (only works with Blender Render)"
    bl_options = {"REGISTER", "UNDO"}

    base_color = bpy.props.FloatVectorProperty(
        name="Base Color",
        subtype="COLOR",
        size=3,
        soft_max=1,
        soft_min=0,
        default=(1, .5, .5)
    )

    hue_variation = bpy.props.FloatProperty(
        name="Hue variation",
        description="The randomness of color",
        default=1,
        min=0,
        max=1,
    )

    saturation_variation = bpy.props.FloatProperty(
        name="Saturation variation",
        description="The randomness of saturation",
        default=0.2,
        min=0,
    )

    brightness_variation = bpy.props.FloatProperty(
        name="Brightness variation",
        description="The variation of brightness",
        min=0,
        max=1,
    )

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        new_material = None
        active = context.active_object
        for ob in context.selected_objects:
            if ob.type in ["MESH", "CURVE", "SURFACE", "META", "FONT"]:

                if len(ob.material_slots) == 0:

                    context.scene.objects.active = ob
                    bpy.ops.object.material_slot_add()

                    if not new_material:
                        new_material = bpy.data.materials.new(name="Material")
                        new_material["tag_generated"] = True
                    ob.material_slots[0].material = new_material

                elif len(ob.material_slots) == 1:
                    if not ob.material_slots[0].material:
                        if not new_material:
                            new_material = bpy.data.materials.new(name="Material")
                            new_material["tag_generated"] = True
                        ob.material_slots[0].material = new_material

                for mt_slot in ob.material_slots:
                    if mt_slot.material:
                        mt_slot.material.use_object_color = True
                h = self.hue_variation * random()
                s = self.saturation_variation * random()
                v = self.brightness_variation * random()

                color = Color(self.base_color)
                color.h += h
                color.s += s
                color.v += v

                ob.color = [color.r, color.g, color.b, 1]
                context.scene.objects.active = active

        return {"FINISHED"}


class ClearColors(bpy.types.Operator):
    bl_idname = "sculptkt.clear_colors"
    bl_label = "Clear Colors"
    bl_description = "Clear Randomized colors"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        new_mat = None
        for ob in context.selected_objects:
            if ob.type in ["MESH", "CURVE", "SURFACE", "META", "FONT"]:

                for mt_slot, index in zip(ob.material_slots, range(len(ob.material_slots))):
                    if mt_slot.material:
                        mt_slot.material.use_object_color = False
                        if mt_slot.material.get("tag_generated"):
                            context.scene.objects.active = ob
                            ob.active_material_index = index
                            bpy.ops.object.material_slot_remove()

        return {"FINISHED"}
