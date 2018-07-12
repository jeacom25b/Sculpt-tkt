import bpy
import bmesh
import random


class Field:
    def __init__(self, mesh):
        self.mesh = mesh
        self.field = {}
        self.bm = bmesh.new()
        self.bm.from_mesh(mesh)
        self.build_field()

    def build_field(self):
        ## Get the curvature field for following Bmesh
        for vert in self.bm.verts:
            normals = sorted([edge.other_vert(vert).normal for edge in vert.link_edges],
                             key=lambda vector: vector.dot(vert.normal))
            self.field[vert.index] = normals[0].cross(vert.normal)

    def stroke_seams(self, seed_distance=0.1, seed_num=10):

    def preview(self, out):
        ## Temporary preview method for testing
        self.bm.verts.ensure_lookup_table()
        bm = bmesh.new()
        for i, vec in self.field.items():
            v1 = bm.verts.new(self.bm.verts[i].co)
            v2 = bm.verts.new(v1.co + vec)
            bm.edges.new((v1, v2))

        bm.to_mesh(out.data)

    class Field_remesh(bpy.types.Operator):
        bl_idname = "sculptkt.field_remesh"
        bl_label = "Field Remesh"
        bl_description = ""
        bl_options = {"REGISTER", "UNDO"}

        @classmethod
        def poll(cls, context):
            return context.active_object.type == "MESH"

        def execute(self, context):
            mesh = context.active_object
            out = context.scene.objects["out"]
            my_field = Field(mesh.data)
            my_field.preview(out)
            return {"FINISHED"}
