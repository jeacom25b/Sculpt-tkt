import bpy

class FlowToolsSymmetrize(bpy.types.Operator):
    bl_idname = "sculptkt.symmetrize"
    bl_label = "SculpTKt Symmetrize"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    
    direction = bpy.props.EnumProperty(
        name = "Direction",
        items = [
            ("NEGATIVE_X", "-x to +x", "-x to +x"),
            ("POSITIVE_X", "+x to -x", "+x to -x"),
            ("NEGATIVE_Y", "-y to +y", "-y to +y"),
            ("POSITIVE_Y", "+y to -y", "+y to -y"),
            ("NEGATIVE_Z", "-z to +z", "-z to +z"),
            ("POSITIVE_Z", "+z to -z", "+z to -z"),
        ]
    )
    
    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object.mode == "SCULPT"
    
    def invoke(self, context, event):
        bpy.ops.ed.undo_push()
        return self.execute(context)
    
    def execute(self, context):
        
        if context.active_object.use_dynamic_topology_sculpting:
            context.tool_settings.sculpt.symmetrize_direction = self.direction
            bpy.ops.sculpt.symmetrize()
            
        else:
            bpy.ops.sculpt.dynamic_topology_toggle()
            bpy.ops.sculpt.symmetrize()

            
            
        return {"FINISHED"}
        

def armature_tools(pie):
    pie.operator("sculptkt.convert_envelope_to_mesh", icon = "MESH_DATA")
    pie.operator("sculptkt.add_envelope_armature", text="Add Envelope Bone", icon="BONE_DATA")
    pie.operator("sculptkt.add_envelope_human", text="Add Envelope Human Base", icon="MOD_ARMATURE")
    
def add_tools(pie):
    pie.operator("sculptkt.add_envelope_armature", text="Add Envelope Bone", icon="BONE_DATA")
    pie.operator("sculptkt.add_envelope_human", text="Add Envelope Human Base", icon="MOD_ARMATURE")    

def object_tools(pie):
    pie.menu("OBJECT_MT_booleans", icon = "MOD_BOOLEAN")
    pie.menu("OBJECT_MT_slash", icon = "SCULPTMODE_HLT")
    pie.operator("object.mode_set", text = "Sculpt", icon = "SCULPTMODE_HLT").mode = "SCULPT"
    pie.operator("object.mode_set", text = "Edit", icon = "EDITMODE_HLT").mode = "EDIT"
    pie.operator("sculptkt.add_envelope_armature", text="Add Envelope Bone", icon="BONE_DATA")
    pie.operator("sculptkt.add_envelope_human", text="Add Envelope Human Base", icon="MOD_ARMATURE")
    pie.operator("sculptkt.optimized_remesh", icon="MOD_REMESH")
    pie.operator("sculptkt.decimate", text = "Decimate", icon="MOD_DECIM").popup = True

def sculpting_tools(pie):
    
    separation = 7
    
    row = pie.row()
    col = row.column()
    col.scale_x = 0.7
    sub_sculpt_brush_tools(col)
    sub_sculpt_dyntopo_tools(col)
    
    for i in range(separation):
        row.separator()
    
    row = pie.row()
    for i in range(separation):
        row.separator()
        
    col = row.column()
    sub_sculpt_texture_tools(col)
    
    pie.operator("object.mode_set", text = "Object Mode", icon = "OBJECT_DATAMODE").mode = "OBJECT"
    
    row = pie.row()
    sub_sculpt_mask_tools(row)
    
    pie.separator()
    pie.separator()
    
#    pie.operator("sculptkt.optimized_remesh", text = "Remesh", icon="MOD_REMESH")
#    pie.operator("sculptkt.decimate", text = "Decimate", icon="MOD_DECIM").popup = True
#    pie.operator("sculptkt.extract", icon="MOD_DISPLACE")
    box = pie.box()
    box.menu("SCULPT_MT_symmetry_options", text = "Brush Symmetry", icon = "MOD_MIRROR")
    box = pie.box()
    box.label("Dyntopo Symmetry")
    sub_sculpt_symmetry(box)
    
def edit_tools(pie):
    pie.operator("object.mode_set", text = "Sculpt", icon = "SCULPTMODE_HLT").mode = "SCULPT"
    pie.operator("object.mode_set", text = "Object", icon = "OBJECT_DATA").mode = "OBJECT"

def sub_sculpt_dyntopo_tools(layout):
    col = layout.column()
    box = col.box()
    box.label("Dynamic Topology")

    dyntopo_on = bpy.context.active_object.use_dynamic_topology_sculpting
    tool_settings = bpy.context.tool_settings
    
    box.operator("sculpt.dynamic_topology_toggle", text = "Toggle Dyntopo OFF" if dyntopo_on else "Toggle Dyntopo ON", icon = "MESH_DATA")
    
    if dyntopo_on:
        detail_type = tool_settings.sculpt.detail_type_method
        
        col = box.column(align = True)
        detail_row = col.row(align = True)
        
        if detail_type == "BRUSH":
            detail_row.prop(tool_settings.sculpt, "detail_percent")
            detail_row.operator("sculpt.sample_detail_size", text = "", icon = "EYEDROPPER")
            
        elif detail_type == "CONSTANT":
            detail_row.prop(tool_settings.sculpt, "constant_detail_resolution")
            detail_row.operator("sculpt.sample_detail_size", text = "", icon = "EYEDROPPER")
            
        elif detail_type == "RELATIVE":
            detail_row.prop(tool_settings.sculpt, "detail_size")
        
        col.prop(tool_settings.sculpt, "detail_refine_method", text = "")
        col.prop(tool_settings.sculpt, "detail_type_method", text = "")
        col.separator()
        col.prop(tool_settings.sculpt, "use_smooth_shading")
        col.separator()
        
        col.operator("sculpt.optimize")
        if detail_type == "CONSTANT":
            col.operator("sculpt.detail_flood_fill")

def sub_sculpt_mask_tools(layout):
    col = layout.column()
    row = col.row()
    row.scale_x = 0.9
    box = row.box()
    
    box.label("Sculpt Mask Extract")
    box.operator("sculptkt.extract", icon="MOD_DISPLACE")
    box.operator("sculptkt.mask_split", icon="MOD_DISPLACE")
    
    box = row.box()
    box.label("Deform")
    box.operator("sculptkt.mask_deform_add", icon="MOD_LATTICE")
    box.operator("sculptkt.mask_deform_remove", icon="MOD_LATTICE")
    
    box = row.box()
    box.label("decimate")
    box.operator("sculptkt.decimate", icon="MOD_DECIM").ratio = bpy.context.scene.decimate_factor
    box.prop(bpy.context.scene, "decimate_factor")
    
    row = col.row()
    
    box = row.box()
    box.label("Remesh")
    box.operator("sculptkt.optimized_remesh", icon="MOD_REMESH")


def sub_sculpt_brush_tools(layout):
    
    col = layout.column()
    box = col.box()
    box.label("Brush")
    
    tool_settings = bpy.context.tool_settings
    box.template_ID_preview(tool_settings.sculpt, "brush", new = "brush.add", cols = 5, rows = 5)
    

def sub_sculpt_texture_tools(layout):
    
    col = layout.column()
    box = col.box()
    box.label("Brush Texture")
    
    tool_settings = bpy.context.tool_settings
    box.template_ID_preview(tool_settings.sculpt.brush, "texture", new = "texture.new", cols = 5, rows = 5)
    box.prop(tool_settings.sculpt.brush.texture_slot, "map_mode")
    box.prop(tool_settings.sculpt.brush.texture_slot, "angle")
    col = box.column(align = True)
    col.prop(tool_settings.sculpt.brush.texture_slot, "use_rake")
    col.prop(tool_settings.sculpt.brush.texture_slot, "use_random")

def sub_sculpt_curve_tools(layout):
    
    col = layout.column()
    box = col.box()
    box.label("curve")
    tool_settings = bpy.context.tool_settings
    
    box.template_curve_mapping(tool_settings.sculpt.brush, "curve")

def sub_sculpt_symmetry(layout):
    
    tool_settings = bpy.context.tool_settings
    layout.prop(tool_settings.sculpt, "symmetrize_direction")
    layout.operator("sculpt.symmetrize")

class FlowTools2(bpy.types.Menu):
    bl_idname = "OBJECT_MT_flow_tools"
    bl_label = "SculpTKt"
    
    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        
        if not context.active_object:
            add_tools(pie)
            return
        
        ob_type = context.active_object.type
        object_mode = context.active_object.mode == "OBJECT"
        sculpt_mode = context.active_object.mode == "SCULPT"
        edit_mode = context.active_object.mode == "EDIT"
        paint_mode = context.active_object.mode == "TEXTURE_PAINT"
        dyntopo_on = context.active_object.use_dynamic_topology_sculpting
        
        if object_mode:
            if ob_type != "ARMATURE":
                object_tools(pie)
                
            else:
                armature_tools(pie)
        
        elif sculpt_mode:
            sculpting_tools(pie)
            
        elif edit_mode:
            edit_tools(pie)

class SymmetryOptions(bpy.types.Menu):
    bl_idname = "SCULPT_MT_symmetry_options"
    bl_label = "Symmetry Options"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.tool_settings.sculpt, "use_symmetry_x")
        layout.prop(context.tool_settings.sculpt, "use_symmetry_y")
        layout.prop(context.tool_settings.sculpt, "use_symmetry_z")

class Booleans(bpy.types.Menu):
    bl_idname = "OBJECT_MT_booleans"
    bl_label = "Boolean Operations"

    def draw(self, context):
        layout = self.layout
        layout.operator("sculptkt.multi_object_boolean", text="Add", icon="MOD_ARRAY").operation = "UNION"
        layout.operator("sculptkt.multi_object_boolean", text="Sub", icon="MOD_BOOLEAN").operation = "DIFFERENCE"
        layout.operator("sculptkt.multi_object_boolean", text="Intersect", icon="MOD_MULTIRES").operation = "INTERSECT"


class Slash(bpy.types.Menu):
    bl_idname = "OBJECT_MT_slash"
    bl_label = "Slash Stroke"
    
    def draw(self, context):
        layout = self.layout
        
        slash_operator = layout.operator(
            "sculptkt.slash_bool", text="Draw Slash", icon="SCULPTMODE_HLT")
            
        slash_operator.cut_thickness = bpy.context.scene.slash_cut_thickness
        slash_operator.cut_distance = bpy.context.scene.slash_cut_distance
        slash_operator.boolean_solver = bpy.context.scene.slash_boolean_solver
        slash_operator.cut_using_mesh = False
        slash_operator.is_ciclic = bpy.context.scene.use_slash_ciclic
        slash_operator.draw_mode = "DRAW"
        
        slash_operator = layout.operator(
            "sculptkt.slash_bool", text="Line Slash", icon="SCULPTMODE_HLT")
        
        slash_operator.cut_thickness = bpy.context.scene.slash_cut_thickness
        slash_operator.cut_distance = bpy.context.scene.slash_cut_distance
        slash_operator.boolean_solver = bpy.context.scene.slash_boolean_solver
        slash_operator.cut_using_mesh = False
        slash_operator.is_ciclic = bpy.context.scene.use_slash_ciclic
        slash_operator.draw_mode = "DRAW_STRAIGHT"
        
        slash_operator = layout.operator(
            "sculptkt.slash_bool", text="Polygon Slash", icon="SCULPTMODE_HLT")
        
        slash_operator.cut_thickness = bpy.context.scene.slash_cut_thickness
        slash_operator.cut_distance = bpy.context.scene.slash_cut_distance
        slash_operator.boolean_solver = bpy.context.scene.slash_boolean_solver
        slash_operator.cut_using_mesh = False
        slash_operator.is_ciclic = bpy.context.scene.use_slash_ciclic
        slash_operator.draw_mode = "DRAW_POLY"
        
        slash_operator = layout.operator(
            "sculptkt.slash_bool", text="Mesh cutter Slash", icon="MESH_DATA")
        
        slash_operator.cut_thickness = bpy.context.scene.slash_cut_thickness
        slash_operator.cut_distance = bpy.context.scene.slash_cut_distance
        slash_operator.boolean_solver = bpy.context.scene.slash_boolean_solver
        slash_operator.cut_using_mesh = True
        slash_operator.keep_objects = False

        layout.menu("VIEW3D_MT_slash_options", icon = "MODIFIER")

class SlashOptions(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_slash_options"
    bl_label = "Slash Options"

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.context.scene, "slash_cut_thickness")
        layout.prop(bpy.context.scene, "slash_cut_distance")
        layout.prop(bpy.context.scene, "use_slash_ciclic")
        layout.prop(bpy.context.scene, "slash_boolean_solver", text = "")