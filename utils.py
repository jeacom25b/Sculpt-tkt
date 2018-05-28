import bpy

# A decorator that enables a operator to work with dyntopo.
def dyntopo_compatible_execute (func):
    
    def execute (self, context):
        
        dyntopo = False
        if bpy.context.active_object.mode == "SCULPT":
            if bpy.context.active_object.use_dynamic_topology_sculpting:
                dyntopo = True
                bpy.ops.sculpt.dynamic_topology_toggle()
        
        return_value = func (self, context)
        
        if dyntopo:
            bpy.ops.sculpt.dynamic_topology_toggle()
        
        return return_value
    return execute


def sculptmode_compatible(func):
    
    def execute (self, context):
        
        sculpt = False
        
        if context.active_object.mode == "SCULPT":
            bpy.ops.object.mode_set(mode="OBJECT")
            sculpt = True
        
        return_value = func(self, context)
        
        if sculpt:
            bpy.ops.object.mode_set(mode="SCULPT")
        
        return return_value
    return execute
