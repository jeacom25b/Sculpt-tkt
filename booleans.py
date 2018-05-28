from bpy import context
from mathutils import Vector
import bpy
import bmesh
from . utils import dyntopo_compatible_execute
      
        

class StrokeMesser():
    
    def __init__(self, stroke, ciclic = False, cut_distance = 50):
        self.stroke = stroke
        self.bm = bmesh.new()
        self.ciclic = ciclic
    
    def create_mesh(self):
        
        direction = Vector((0,0,1))
        direction.rotate(bpy.context.region_data.view_rotation)
        bm = self.bm
        
        normal = Vector()
        last_vector = None
            
        last_vert1 = None
        last_vert2 = None
        first_vert1 = None
        first_vert2 = None
        
        for point in self.stroke.points:
            vert1 = bm.verts.new((direction * -500) + point.co)
            vert2 = bm.verts.new((direction * 500) + point.co)
            if not first_vert1 and not first_vert2:
                first_vert1 = vert1
                first_vert2 = vert2
            if last_vert1 and last_vert2:
                bm.faces.new((last_vert1, last_vert2, vert2, vert1))
            last_vert1 = vert1
            last_vert2 = vert2
        
        if self.ciclic and len(self.stroke.points) > 2:
            bm.faces.new((last_vert1, last_vert2, first_vert2, first_vert1))
        
        bmesh.ops.recalc_face_normals(self.bm, faces = self.bm.faces)
    
    def dump_to_mesh(self, obj):
        
        if obj.type == "MESH":
            self.create_mesh()
            self.bm.to_mesh(obj.data)
        else:
            raise Exception("Something went wrong with the stroke messer,", obj)
        

class SlashBoolean(bpy.types.Operator):
    bl_idname = "sculptkt.slash_bool"
    bl_label = "Slash Boolean"
    bl_description = "Cut the mesh by drawing strokes, (Might be slow on dense meshes)"
    bl_options = {"REGISTER","UNDO"}
    
    drawing = False
    
    cut_thickness = bpy.props.FloatProperty(
        name = "Cut Thickness",
        description = "The spacing of the cut though the mesh",
        default = 0.001,
        min = 0.000001
    )
    
    cut_distance = bpy.props.FloatProperty(
        name = "Cut Distance",
        description = "The distance the cut spams over the stroke location",
        default = 50,
        min = 0.000001
    )
    
    boolean_solver = bpy.props.EnumProperty(
        name = "Boolean Solver",
        description = "Which method to use, Carve fails less often but is slower",
        items = [("BMESH", "Bmesh", "Bmesh"), ("CARVE", "Carve", "Carve")],
        default = "CARVE"
    )
    
    is_ciclic = bpy.props.BoolProperty(
        name = "Ciclic",
        description = "Make the cut wrap around (Clossed piece)",
        default = False
    )
    
    keep_objects = bpy.props.BoolProperty(
        name = "Keep Objects",
        description = "Delete or not the original objects.",
        default = True
    )
    
    cut_using_mesh = bpy.props.BoolProperty(
        name = "Cut using active",
        description = "Delete or not the original objects.",
        default = False
    )
    
    draw_mode = bpy.props.EnumProperty(
        name = "Mode",
        items = [
            ("NONE", "None", "None"),
            ("DRAW","Draw", "Draw"),
            ("DRAW_STRAIGHT", "Line", "Line"), 
            ("DRAW_POLY", "Poly", "Poly")],
        default = "NONE"
    )
    
    def draw(self, context):
        layout = self.layout
        
        layout.prop(self, "cut_thickness")
        layout.prop(self, "cut_distance")
        layout.prop(self, "boolean_solver")
        layout.prop(self, "is_ciclic")
        layout.prop(self, "keep_objects")
        layout.prop(self, "cut_using_mesh")
    
    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object.type == "MESH"
    
    def invoke(self, context, event):
        if context.tool_settings.grease_pencil_source == "OBJECT":
            self.report(type = {"ERROR"}, message = "Grease Pencil data source must be 'SCENE'\n Please change it on the Grease Pencil tab")
            return {"CANCELLED"}
        
        if self.draw_mode != "NONE":
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        return self.execute(context)
    
    def modal(self, context, event):
        
        if not self.drawing:
            bpy.ops.gpencil.draw('INVOKE_DEFAULT', mode=self.draw_mode)
            self.drawing = True
        
        if self.draw_mode in ("DRAW_STRAIGHT", "DRAW"):
            if event.type in "LEFTMOUSE" and event.value == "RELEASE":
                return self.execute(context)
        
        if event.type in ["RET", "NUMPAD_ENTER", "RIGHTMOUSE", "MIDDLEMOUSE"]:
            return self.execute(context)
        
        return {"RUNNING_MODAL"}
    
    @dyntopo_compatible_execute
    def execute(self, context):
            
        if context.scene.grease_pencil and not self.cut_using_mesh:
                
            cutter_data = bpy.data.meshes.new("Cutter_mesh")
            cutter_object = bpy.data.objects.new("cutter", cutter_data)
            
            if len(context.scene.grease_pencil.layers.active.active_frame.strokes) > 0:
                stroke = context.scene.grease_pencil.layers.active.active_frame.strokes[-1]
            else:
                return {"CANCELLED"}
            
            stroke_messer = StrokeMesser(stroke, self.is_ciclic, self.cut_distance)
            stroke_messer.dump_to_mesh(cutter_object)
            
            md_sldf = cutter_object.modifiers.new(type = "SOLIDIFY", name = "thin_solid")
            md_sldf.offset = 0.0
            md_sldf.thickness = self.cut_thickness
            
            active_ob = context.active_object
            md_bool = active_ob.modifiers.new(type = "BOOLEAN", name = "cut")
            md_bool.operation = "DIFFERENCE"
            md_bool.solver = self.boolean_solver
            md_bool.object = cutter_object
            bpy.ops.object.modifier_apply(modifier = md_bool.name)
            
            bpy.data.meshes.remove(cutter_data)
            bpy.data.objects.remove(cutter_object)
            
            bpy.ops.object.mode_set(mode = "EDIT")
            bpy.ops.mesh.select_all(action = "SELECT")
            bpy.ops.mesh.separate(type = "LOOSE")
            bpy.ops.object.mode_set(mode = "OBJECT")
            
            context.scene.grease_pencil.layers.active.active_frame.strokes.remove(stroke_messer.stroke)
            
        if self.cut_using_mesh:
            
            cutter_object = context.active_object
            cuttends = [ob for ob in context.selected_objects if not ob == cutter_object and ob.type == "MESH"]
            
            md_sldf = cutter_object.modifiers.new(type = "SOLIDIFY", name = "thin_solid")
            md_sldf.offset = 0.0
            md_sldf.thickness = self.cut_thickness
            
            for ob in cuttends:
                
                md_bool = ob.modifiers.new(type = "BOOLEAN", name = "cut")
                md_bool.operation = "DIFFERENCE"
                md_bool.solver = self.boolean_solver
                md_bool.object = cutter_object
                context.scene.objects.active = ob
                bpy.ops.object.modifier_apply(modifier = md_bool.name)
                bpy.ops.object.mode_set(mode = "EDIT")
                bpy.ops.mesh.separate(type = "LOOSE")
                bpy.ops.object.mode_set(mode = "OBJECT")
            
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
        name = "Operation",
        description = "Apply a boolean operation from selected_objects to active.",
        items = [
            ("UNION", "Union", "Union"),
            ("INTERSECT", "Intersect", "Intersect"),
            ("DIFFERENCE", "Difference", "Difference"),
        ]
    )
    
    keep_objects = bpy.props.BoolProperty(
        name = "Keep Objects",
        description = "Delete or not the original objects.",
        default = True
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
            md = context.active_object.modifiers.new(type = "BOOLEAN", name = name)
            md.object = mesh
            md.name = name
            md.operation = self.operation
            md.solver = self.solver
            bpy.ops.object.modifier_apply(modifier = md.name)
            if self.keep_objects:
                ob_data = mesh.data
                bpy.data.meshes.remove(ob_data)
                bpy.data.objects.remove(mesh)
            
        
        return {"FINISHED"}
        