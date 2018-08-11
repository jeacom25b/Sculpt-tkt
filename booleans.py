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

from mathutils import Vector
import bpy
import bmesh
from bpy_extras import view3d_utils
from .utils import dyntopo_compatible_execute


class StrokeMesser:

    def __init__(self, context):
        if context.scene.grease_pencil:
            gp = context.scene.grease_pencil

            if not gp.palettes:
                palette = gp.palettes.new("Pallete")
            else:
                palette = gp.palettes.active

            if not "slash cut" in palette.colors:
                color = palette.colors.new()
                color.name = "slash cut"
                color.color = (1, 0.5, 0)

            self.layer = gp.layers.new("Slash boolean stroke")
            self.layer.line_change = 2
            frame = self.layer.frames.new(context.scene.frame_current)
            self.stroke = frame.strokes.new("slash cut")
            self.stroke.draw_mode = "3DSPACE"
            self.stroke.points.add()
        else:
            gp = bpy.data.grease_pencil.new("Grease Pencil")
            context.scene.grease_pencil = gp

            palette = gp.palettes.new("Pallete")
            color = palette.colors.new()
            color.name = "slash cut"
            color.color = (1, 0.5, 0)

            self.layer = gp.layers.new("Slash boolean stroke")
            self.layer.line_change = 2
            frame = self.layer.frames.new(context.scene.frame_current)
            self.stroke = frame.strokes.new("slash cut")
            self.stroke.draw_mode = "3DSPACE"
            self.stroke.points.add()
        self.gp = gp
        self.bm = bmesh.new()
        self.last_mouse_location = Vector()
        self.lmb = False

    def remove_stroke(self):
        self.gp.layers.remove(self.layer)

    def update(self, context, event):
        region = context.region
        region_3d = context.region_data
        co = event.mouse_region_x, event.mouse_region_y
        location_vec = Vector((event.mouse_region_x, event.mouse_region_y, 0))
        mouse_delta = (location_vec - self.last_mouse_location)
        delta_length = mouse_delta.length

        camera_origin = view3d_utils.region_2d_to_origin_3d(region, region_3d, co)
        ray = view3d_utils.region_2d_to_vector_3d(region, region_3d, co)
        cursor = context.scene.cursor_location
        far = (camera_origin - cursor).length

        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            self.lmb = True

        if event.type == "LEFTMOUSE" and event.value == "RELEASE":
            self.lmb = False

        if self.lmb:
            if delta_length > 5:
                self.stroke.points.add()
                self.last_mouse_location = location_vec

        self.stroke.points[-1].co = ray * far + camera_origin


    def create_mesh(self, context, ciclic = False):
        region = context.region
        region_3d = context.region_data
        end = context.space_data.clip_end
        start = context.space_data.clip_start
        bm = self.bm

        last_vert1 = None
        last_vert2 = None
        first_vert1 = None
        first_vert2 = None

        for point in self.stroke.points:
            screen_projection = view3d_utils.location_3d_to_region_2d(region, region_3d, point.co)
            view_origin = view3d_utils.region_2d_to_origin_3d(region, region_3d, screen_projection)
            point_vector = view3d_utils.region_2d_to_vector_3d(region, region_3d, screen_projection)

            vert1 = bm.verts.new((point_vector * start) + view_origin)
            vert2 = bm.verts.new((point_vector * end) + view_origin)

            if not first_vert1 and not first_vert2:
                first_vert1 = vert1
                first_vert2 = vert2
            if last_vert1 and last_vert2:
                bm.faces.new((last_vert1, last_vert2, vert2, vert1))
            last_vert1 = vert1
            last_vert2 = vert2

        if ciclic and len(self.stroke.points) > 2:
            bm.faces.new((last_vert1, last_vert2, first_vert2, first_vert1))

        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)

    def dump_to_mesh(self, obj):

        if obj.type == "MESH":
            self.bm.to_mesh(obj.data)
        else:
            raise Exception("Something went wrong with the stroke messer,", obj)


class SlashBoolean(bpy.types.Operator):
    bl_idname = "sculptkt.slash_bool"
    bl_label = "Slash Boolean"
    bl_description = "Cut the mesh by drawing strokes, (Might be slow on dense meshes)"
    bl_options = {"REGISTER", "UNDO"}

    cut_thickness = bpy.props.FloatProperty(
        name="Cut Thickness",
        description="The spacing of the cut though the mesh",
        default=0.001,
        min=0.000001
    )

    boolean_solver = bpy.props.EnumProperty(
        name="Boolean Solver",
        description="Which method to use, Carve fails less often but is slower",
        items=[("BMESH", "Bmesh", "Bmesh"), ("CARVE", "Carve", "Carve")],
        default="CARVE"
    )

    is_ciclic = bpy.props.BoolProperty(
        name="Ciclic",
        description="Make the cut wrap around (Circular cuts)",
        default=False
    )

    keep_objects = bpy.props.BoolProperty(
        name="Keep Objects",
        description="Delete or not the original objects.",
        default=True
    )

    cut_using_mesh = bpy.props.BoolProperty(
        name="Cut using active",
        description="Delete or not the original objects.",
        default=False
    )

    delete_small_pieces = bpy.props.BoolProperty(
        name="Delete Small Pieces",
        description="Delete the pieces that are smaller and only keep the bigger side of the"
                    " resulting cut (Based on total volume)",
        default = True
    )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "cut_thickness")
        layout.prop(self, "boolean_solver")
        layout.prop(self, "is_ciclic")
        if self.cut_using_mesh:
            layout.prop(self, "keep_objects")
        else:
            layout.prop(self, "delete_small_pieces")

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if context.area.type == "VIEW_3D":
                return context.active_object.type == "MESH" and not context.active_object.mode == "EDIT"

    def invoke(self, context, event):
        if self.cut_using_mesh:
            return self.execute(context)
        else:
            self.stroke_messer = StrokeMesser(context)
            self._handler = context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}

    def modal(self, context, event):
        self.stroke_messer.update(context, event)
        context.area.header_text_set("Left Click/Drag: Draw,   Left CLick: Creates sharp corners"
                              "  Right Click or Return/Enter: Finish Cut   Esc: Cancel")
        if event.type == "ESC":
            self.stroke_messer.remove_stroke()
            context.area.header_text_set()
            return {"CANCELLED"}
        elif event.type == "LEFTMOUSE":
            return {"RUNNING_MODAL"}

        elif event.type in {"RIGHTMOUSE", "RETURN"}:
            context.area.header_text_set()
            return self.execute(context)

        context.area.tag_redraw()

        return {"PASS_THROUGH"}

    @dyntopo_compatible_execute
    def execute(self, context):

        if context.scene.grease_pencil and not self.cut_using_mesh:
            for ob in context.selected_objects:
                if not ob == context.active_object:
                    ob.select = False

            cutter_data = bpy.data.meshes.new("Cutter_mesh")
            cutter_object = bpy.data.objects.new("cutter", cutter_data)

            self.stroke_messer.create_mesh(context, self.is_ciclic)
            self.stroke_messer.dump_to_mesh(cutter_object)

            md_sldf = cutter_object.modifiers.new(type="SOLIDIFY", name="thin_solid")
            md_sldf.offset = 0.0
            md_sldf.thickness = self.cut_thickness

            active_ob = context.active_object
            md_bool = active_ob.modifiers.new(type="BOOLEAN", name="cut")
            md_bool.operation = "DIFFERENCE"
            md_bool.solver = self.boolean_solver
            md_bool.object = cutter_object
            bpy.ops.object.modifier_apply(modifier=md_bool.name)

            bpy.data.meshes.remove(cutter_data)
            bpy.data.objects.remove(cutter_object)

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.separate(type="LOOSE")
            bpy.ops.object.mode_set(mode="OBJECT")

            self.stroke_messer.remove_stroke()

            if self.delete_small_pieces:
                bigger_volume = -9999999999999
                bigger = None
                for ob in context.selected_objects:
                    bm = bmesh.new()
                    bm.from_mesh(ob.data)
                    vol = bm.calc_volume()
                    if vol > bigger_volume:
                        bigger_volume = vol
                        bigger = ob
                for ob in context.selected_objects:
                    if not ob == bigger:
                        data = ob.data
                        bpy.data.meshes.remove(data)
                        bpy.data.objects.remove(ob)
                context.scene.objects.active = bigger


        if self.cut_using_mesh:

            cutter_object = context.active_object
            cuttends = [ob for ob in context.selected_objects if not ob == cutter_object and ob.type == "MESH"]

            md_sldf = cutter_object.modifiers.new(type="SOLIDIFY", name="thin_solid")
            md_sldf.offset = 0.0
            md_sldf.thickness = self.cut_thickness

            for ob in cuttends:
                md_bool = ob.modifiers.new(type="BOOLEAN", name="cut")
                md_bool.operation = "DIFFERENCE"
                md_bool.solver = self.boolean_solver
                md_bool.object = cutter_object
                context.scene.objects.active = ob
                bpy.ops.object.modifier_apply(modifier=md_bool.name)
                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.mesh.separate(type="LOOSE")
                bpy.ops.object.mode_set(mode="OBJECT")

            if not self.keep_objects:
                bpy.data.meshes.remove(cutter_object.data)
                bpy.data.objects.remove(cutter_object)

        return {"FINISHED"}


class MultiObjectBoolean(bpy.types.Operator):
    bl_idname = "sculptkt.multi_object_boolean"
    bl_label = "Multi Object Boolean"
    bl_description = "Apply a boolean operation from selected objects to the active."
    bl_options = {"REGISTER", "UNDO"}

    solver = bpy.props.EnumProperty(
        name="Boolean Solver",
        description="Which method to use, Carve fails less often but is slower",
        items=[("BMESH", "Bmesh", "Bmesh"), ("CARVE", "Carve", "Carve")],
        default="CARVE"
    )

    operation = bpy.props.EnumProperty(
        name="Operation",
        description="Apply a boolean operation from selected_objects to active.",
        items=[
            ("UNION", "Union", "Union"),
            ("INTERSECT", "Intersect", "Intersect"),
            ("DIFFERENCE", "Difference", "Difference"),
        ]
    )

    keep_objects = bpy.props.BoolProperty(
        name="Keep Objects",
        description="Delete or not the original objects.",
        default=True
    )

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if context.active_object.type == "MESH":
                return True

    def execute(self, context):

        meshes = [ob for ob in context.selected_objects if ob.type == "MESH"]
        meshes.remove(context.active_object)

        for mesh in meshes:

            name = "BooLean_modifier_to_apply_like_a_So_BIg_name_THat_WIll_Ever_eXist"
            md = context.active_object.modifiers.new(type="BOOLEAN", name=name)
            md.object = mesh
            md.name = name
            md.operation = self.operation
            md.solver = self.solver
            bpy.ops.object.modifier_apply(modifier=md.name)
            if self.keep_objects:
                ob_data = mesh.data
                bpy.data.meshes.remove(ob_data)
                bpy.data.objects.remove(mesh)

        return {"FINISHED"}
