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
        for vert in self.bm.verts:
            vector1 = sorted([face.normal for face in vert.link_faces],
                             key=lambda vector: vector.dot(vert.normal))[-1].cross(vert.normal)
            vector2 = vector1.cross(vert.normal)
            print(vector1)
            self.field[vert] = (vector1, vector2)

    def stroke_seams(self):
        # Todo implement splitting
        pass

    def preview(self, outmesh):
        bm = bmesh.new()
        for vert in self.field.keys():
            vectors = self.field[vert]
            v1 = bm.verts.new(vert.co)
            v2 = bm.verts.new(((vectors[0] * 0.5) + vert.co))
            v3 = bm.verts.new(((vectors[1] * 0.5) + vert.co))

            bm.edges.new((v1, v2))
            bm.edges.new((v1, v3))
        bm.to_mesh(outmesh)

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
        my_field.preview(context.scene.objects["out"].data)
        return {"FINISHED"}
