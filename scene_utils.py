from bpy import context

def get_selected_objects():
    return context.selected_objects

def get_active_object():
    return context.active_object

def get_objects():
    return context.scene.objects
