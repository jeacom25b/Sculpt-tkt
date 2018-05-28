import bpy
from bpy import context
from . import lightloader




class DrawingOptions(bpy.types.Panel):
    bl_idname = "sculptkt.draw_options"
    bl_label = "Drawing Options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "SculpTKt"

    def draw(self, context):
        layout = self.layout
        
        layout.label("Drawing Options")
        
        split = layout.split(0.6)
        split.prop(context.space_data, "show_floor", text = "Grid Floor")
        row = split.row(align = True)
        row.prop(context.space_data, "show_axis_x", text = "X", toggle = True)
        row.prop(context.space_data, "show_axis_y", text = "Y", toggle = True)
        row.prop(context.space_data, "show_axis_z", text = "Z", toggle = True)
        layout.prop(context.space_data, "lens")
        
        layout.separator()
        layout.operator("sculptkt.toggle_wire")
        
        layout.separator()
        col = layout.column(align = True)
        col.operator("sculptkt.random_colors")
        col.operator("sculptkt.clear_colors")
        


class FlowToolsBool(bpy.types.Panel):
    bl_idname = "sculptkt.boolean_panel"
    bl_label = "Boolean Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "SculpTKt"

    def draw(self, context):
        layout = self.layout
        
        layout.label("Booleans")
        
        layout.prop(context.scene, "multi_boolean_solver")
        
        row = layout.row(align = True)
        
        op = row.operator("sculptkt.multi_object_boolean", text="Add", icon="MOD_ARRAY")
        op.operation = "UNION"
        op.solver = context.scene.multi_boolean_solver
        
        op = row.operator("sculptkt.multi_object_boolean", text="Sub", icon="MOD_BOOLEAN")
        op.operation = "DIFFERENCE"
        op.solver = context.scene.multi_boolean_solver
        
        op = row.operator("sculptkt.multi_object_boolean", text="Intersect", icon="MOD_MULTIRES")
        op.operation = "INTERSECT"
        op.solver = context.scene.multi_boolean_solver
        
        
        layout.label("Slash Cutting")
        
        col = layout.column(align=True)

        col.prop(bpy.context.scene, "slash_boolean_solver", text = "")
        col.prop(bpy.context.scene, "slash_cut_thickness")
        col.prop(bpy.context.scene, "slash_cut_distance")
        col.prop(bpy.context.scene, "use_slash_ciclic", toggle = True)
        col.separator()
        
        slash_operator = col.operator(
            "sculptkt.slash_bool", text="Draw Slash", icon="SCULPTMODE_HLT")
            
        slash_operator.cut_thickness = bpy.context.scene.slash_cut_thickness
        slash_operator.cut_distance = bpy.context.scene.slash_cut_distance
        slash_operator.boolean_solver = bpy.context.scene.slash_boolean_solver
        slash_operator.cut_using_mesh = False
        slash_operator.is_ciclic = bpy.context.scene.use_slash_ciclic
        slash_operator.draw_mode = "DRAW"
        
        slash_operator = col.operator(
            "sculptkt.slash_bool", text="Line Slash", icon="SCULPTMODE_HLT")
        
        slash_operator.cut_thickness = bpy.context.scene.slash_cut_thickness
        slash_operator.cut_distance = bpy.context.scene.slash_cut_distance
        slash_operator.boolean_solver = bpy.context.scene.slash_boolean_solver
        slash_operator.cut_using_mesh = False
        slash_operator.is_ciclic = bpy.context.scene.use_slash_ciclic
        slash_operator.draw_mode = "DRAW_STRAIGHT"
        
        slash_operator = col.operator(
            "sculptkt.slash_bool", text="Polygon Slash", icon="SCULPTMODE_HLT")
        
        slash_operator.cut_thickness = bpy.context.scene.slash_cut_thickness
        slash_operator.cut_distance = bpy.context.scene.slash_cut_distance
        slash_operator.boolean_solver = bpy.context.scene.slash_boolean_solver
        slash_operator.cut_using_mesh = False
        slash_operator.is_ciclic = bpy.context.scene.use_slash_ciclic
        slash_operator.draw_mode = "DRAW_POLY"
        
        slash_operator = col.operator(
            "sculptkt.slash_bool", text="Mesh cutter Slash", icon="MESH_DATA")
        
        slash_operator.cut_thickness = bpy.context.scene.slash_cut_thickness
        slash_operator.cut_distance = bpy.context.scene.slash_cut_distance
        slash_operator.boolean_solver = bpy.context.scene.slash_boolean_solver
        slash_operator.cut_using_mesh = True
        slash_operator.keep_objects = False


        
class MaskTools(bpy.types.Panel):
    bl_idname = "sculptkt.mask_tools"
    bl_label = "Sculpt Mask Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "SculpTKt"

    def draw(self, context):
        
        layout = self.layout
        col = layout.column(align=True)
        
        col.label("Sculpt Mask Extract")
        col.operator("sculptkt.extract", icon="MOD_DISPLACE")
        col.operator("sculptkt.mask_split", icon="MOD_DISPLACE")
        
        col.label("Deform")
        col.operator("sculptkt.mask_deform_add", icon="MOD_LATTICE")
        col.operator("sculptkt.mask_deform_remove", icon="MOD_LATTICE")
        
        col.label("decimate")
        
        op = col.operator("sculptkt.decimate", icon="MOD_DECIM")
        op.ratio = context.scene.decimate_factor
        op.use_mask = True
        
        col.prop(context.scene, "decimate_factor")


class FlowToolsRemesh(bpy.types.Panel):
    bl_idname = "sculptkt.remesh_pannel"
    bl_label = "Remesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "SculpTKt"

    def draw(self, context):
        
        layout = self.layout
        col = layout.column(align=True)
        col.label("Remeshing")
        
        op = col.operator("sculptkt.decimate", text = "Decimate", icon="MOD_DECIM")
        op.ratio = context.scene.decimate_factor
        op.use_mask = False
        col.prop(context.scene, "decimate_factor")
        
        col.separator()
        col.operator("sculptkt.simple_optimized_remesh", icon="MOD_REMESH").octree_depth = context.scene.remesh_depth
        col.operator("sculptkt.optimized_remesh", icon="MOD_REMESH").octree_depth = context.scene.remesh_depth
        col.prop(context.scene, "remesh_depth")
        
        col.separator()


class EnvelopeBuilder(bpy.types.Panel):
    bl_idname = "sculptkt.envelope_builder"
    bl_label = "Envelope Builder"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "SculpTKt"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label("Envelope Builder")
        col.operator("sculptkt.add_envelope_human", icon="MOD_ARMATURE")
        col.operator("sculptkt.add_envelope_armature", icon="BONE_DATA")
        col.operator("sculptkt.convert_envelope_to_mesh", icon="MESH_DATA")


class ViewportShader(bpy.types.Panel):
    bl_idname = "sculptkt.lights"
    bl_label = "Solid Lights"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "SculpTKt"

    def draw(self, context):
        layout = self.layout

        layout.label("Presets")
        col = layout.column()
        row = col.row(align=True)
        row.operator("sculptkt.import_light_preset", text="", icon="FILESEL")
        row.operator("sculptkt.export_light_preset", text="", icon="FILE_PARENT")
        row = col.row(align=True)
        row.prop(context.scene, "lightloader_preset", text="")
        row.operator("sculptkt.save_light_preset", text="", icon="ZOOMIN")
        row.operator("sculptkt.delete_light_preset", text="", icon="ZOOMOUT").name = context.scene.lightloader_preset

        for light in context.user_preferences.system.solid_lights:
            layout.separator()
            row = layout.row()
            row.prop(light, "use", icon="OUTLINER_OB_LAMP", text="")

            col = row.column()
            col.prop(light, "direction", text="")
            row = col.row(align=True)
            row.prop(light, "diffuse_color", text="")
            row.prop(light, "specular_color", text="")
            row = col.row(align=True)
            row.label("Diffuse")
            row.label("Specular")
        layout.separator()