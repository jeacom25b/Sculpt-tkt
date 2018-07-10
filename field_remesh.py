import bpy
import bmesh

class Field:
    def __init__(self, mesh):
        self.mesh = mesh
        self.field = {}
        self.bm = bmesh.new()
        self.bm.from_mesh(mesh)
        self.build_field()

    def build_field(self):
        # Todo implement field building
        pass

    def stroke_seams(self):
        # Todo implement splitting
        pass

class Field_remesh(bpy.types.Operator):
    bl_idname = "sculptkt.field_remesh"
    bl_label = "Field Remesh"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object.type == "MESH"

    def execute(self, context):
        mesh = context.active_object.data
        my_field = Field(mesh)
        return {"FINISHED"}