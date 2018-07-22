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
import bmesh
from .utils import dyntopo_compatible_execute


class MeshMesser:

    def __init__(self, object):

        if not object.type == "MESH":
            raise ValueError("Passed object is not a mesh object")

        self.mesh = object.data
        self.object = object
        self.bm = bmesh.new()
        self.bm.from_mesh(object.data)
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()

    def back_to_mesh(self):
        self.bm.to_mesh(self.mesh)

    def _check_mergeable_face(self, face):
        mergeable = True
        tirade = False
        for edge in face.edges:
            for edge_face in edge.link_faces:
                if not face == edge_face:
                    found_triade_verts = 0

                    for vert in edge_face.verts:
                        if len(vert.link_edges):
                            if vert not in face.verts:
                                found_triade_verts += 1
                                if found_triade_verts >= 2:
                                    triade = True
                                else:
                                    return True

        if tirade:
            delta = vert_with_3_edges[0].co - vert_with_3_edges[1].co
            dx = delta.x
            dy = delta.y
            dz = delta.z

            bigger_axis = "NoAxis"
            if dx > dy and dx > dx:
                bigger_axis = "X"
            elif dy > dx and dy > dz:
                bigger_axis = "Y"
            elif dz > dx and dz > dy:
                bigger_axis = "Z"

            if not bigger_axis == main_axis:
                mergeable = False
            elif bigger_axis == "NoAxis":
                print("Something went wrong with major axis detection:")
                print("3-edge verts", vert_with_3_edges)
                print(face)

        return mergeable

    def convoluted_clean(self, main_axis="Z"):

        bm = self.bm
        to_merge = []
        for face in bm.faces:

            if len(face.verts) == 4:
                vert_with_3_edges = []
                hexagonal_pattern = 0

                for vert in face.verts:
                    if len(vert.link_edges) == 3:
                        vert_with_3_edges.append(vert)
                    elif len(vert.link_edges) == 6:
                        hexagonal_pattern += 1

                if len(vert_with_3_edges) == 2:

                    join_verts_now = True

                    if hexagonal_pattern >= 2:
                        join_verts_now = self._check_mergeable_face(face)

                    if join_verts_now:
                        # location = vert_with_3_edges[0].co + vert_with_3_edges[1].co
                        location = face.calc_center_median()
                        vert_with_3_edges[0].co = location
                        vert_with_3_edges[1].co = location
                        to_merge.extend(vert_with_3_edges)

        bmesh.ops.remove_doubles(bm, verts=list(set(to_merge)), dist=0.00000001)
        bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=1, use_axis_x=True, use_axis_y=True, use_axis_z=True)


class OptimizedRemesh(bpy.types.Operator):
    bl_idname = "sculptkt.optimized_remesh"
    bl_label = "Advanced Remesh"
    bl_description = "Recreates the mesh into quads and adds a multires modifier (Use Alt + S to scale the spheres)"
    bl_options = {"REGISTER", "UNDO"}

    octree_depth = bpy.props.IntProperty(
        name="Octree Depth",
        description="resolution of the new mesh",
        default=4,
        min=0
    )

    cleaning_iterations = bpy.props.IntProperty(
        name="Cleaning Iterations",
        description="How many times the cleaner will analize the mesh, bigger = slower",
        default=3,
        min=0
    )

    use_multires = bpy.props.BoolProperty(
        name="Use Multires",
        description="Add a multiresolution modifier",
        default=False
    )

    multires_res = bpy.props.IntProperty(
        name="Multiresolution",
        description="the subdivision level of the Multiresolution",
        default=2,
        min=0
    )

    smooth_shading = bpy.props.BoolProperty(
        name="Smooth Shading",
        default=False
    )

    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) > 1:
            return
        if context.active_object:
            return context.active_object.type == "MESH" and not context.object.mode == "EDIT"

    def invoke(self, context, event):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.ed.undo_push()
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    @dyntopo_compatible_execute
    def execute(self, context):

        was_sculpt = False
        if context.object.mode == "SCULPT":
            bpy.ops.object.mode_set(mode="OBJECT")
            was_sculpt = True

        ob = context.active_object
        bpy.ops.object.duplicate()
        new_ob = context.active_object

        md = new_ob.modifiers.new(type="REMESH", name="Messed_remesh")
        md.mode = "SMOOTH"
        md.octree_depth = self.octree_depth
        md.use_remove_disconnected = False
        bpy.ops.object.convert(target="MESH")

        bm_messer = MeshMesser(new_ob)

        for _ in range(self.cleaning_iterations):
            bm_messer.convoluted_clean()
            bm_messer.back_to_mesh()

            sk_md = new_ob.modifiers.new(type="SHRINKWRAP", name="new_shrink")
            sk_md.wrap_method = "PROJECT"
            sk_md.use_negative_direction = True
            sk_md.target = ob
            bpy.ops.object.modifier_apply(modifier=sk_md.name)

        if self.use_multires:
            md = new_ob.modifiers.new(type="MULTIRES", name="Multiresolution")
            for _ in range(self.multires_res):
                bpy.ops.object.multires_subdivide(modifier=md.name)
                sk_md = new_ob.modifiers.new(type="SHRINKWRAP", name="new_shrink")
                sk_md.target = ob
                sk_md.wrap_method = "PROJECT"
                sk_md.use_negative_direction = True
                bpy.ops.object.modifier_apply(modifier=sk_md.name)

        ob_name = ob.name
        bpy.data.meshes.remove(ob.data)
        bpy.data.objects.remove(ob)
        new_ob.name = ob_name

        if was_sculpt:
            bpy.ops.object.mode_set(mode="SCULPT")

        if self.smooth_shading:
            bpy.ops.object.shade_smooth()

        return {"FINISHED"}


class SimpleOptimizedRemesh(bpy.types.Operator):
    bl_idname = "sculptkt.simple_optimized_remesh"
    bl_label = "Simple Remesh"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    octree_depth = bpy.props.IntProperty(
        name="Octree Depth",
        description="resolution of the new mesh",
        default=4,
        min=0
    )

    poll = OptimizedRemesh.poll

    def execute(self, context):
        bpy.ops.sculptkt.optimized_remesh(octree_depth=self.octree_depth)
        return {"FINISHED"}
