import bpy
import bmesh
import os
from mathutils import Vector


class Extract(bpy.types.Operator):
    bl_idname = "sculptkt.extract"
    bl_label = "Extract Mask"
    bl_description = "Extrude masked areas as a new object and apply Smooth"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if len(context.selected_objects) == 1:
                return context.active_object.type == "MESH" and context.active_object.mode == "SCULPT"

    def invoke(self, context, event):
        for md in context.active_object.modifiers:
            if md.type == "MULTIRES":
                self.report(type={"ERROR"}, message="Could not extract object with multires modifier.")
                return {"CANCELLED"}

        self.counter = 0
        self.button_released = False
        self.last_mouse_y = event.mouse_y

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.ed.undo_push()
        ob = context.active_object

        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        mask = bm.verts.layers.paint_mask.verify()

        try:

            for vert in bm.verts:
                if vert[mask] < 0.5:
                    bm.verts.remove(vert)

        except Exception:
            return {"CANCELLED"}

        bm.verts.ensure_lookup_table()

        smooth_list = []
        dissolve_list = []
        for vert in bm.verts:
            if len(vert.link_faces) < 2:
                dissolve_list.append(vert)

            elif len(vert.link_faces) == 2:
                vert.select = True
                smooth_list.append(vert)

        bmesh.ops.smooth_vert(bm, verts=smooth_list, factor=1, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        bmesh.ops.dissolve_verts(bm, verts=dissolve_list)

        bpy.ops.object.duplicate()
        extracted = context.active_object
        self.extracted = extracted
        bm.to_mesh(extracted.data)
        bm.free()

        self.modifier = extracted.modifiers.new(type="SOLIDIFY", name="SOLID_")
        self.modifier.offset = 1

        context.window_manager.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def modal(self, context, event):

        if event.type == "MOUSEMOVE":
            mouse_delta = self.last_mouse_y - event.mouse_y
            self.last_mouse_y = event.mouse_y

            if self.counter == 0:
                self.modifier.thickness += mouse_delta / (50 if not event.shift else 500)
                if self.modifier.thickness < 0.00000000001:
                    self.modifier.thickness = 0.00000000001

            elif self.counter == 1:
                self.modifier.factor -= mouse_delta / (300 if not event.shift else 1000)
                if self.modifier.factor < 0.00000000001:
                    self.modifier.factor = 0.00000000001
                elif self.modifier.factor > 2:
                    self.factor = 2

        if event.type in ("LEFTMOUSE", "RIGHT_MOUSE", "RET", "NUMPAD_RETURN", "ESC"):

            if self.counter == 0:
                self.execute(context)
                self.counter += 1
                return {"RUNNING_MODAL"}

            elif self.counter == 1 and event.value == "PRESS" and self.button_released:
                return self.finish(context)

            if event.value == "RELEASE":
                self.button_released = True

        return {"RUNNING_MODAL"}

    def execute(self, context):
        bpy.ops.object.modifier_apply(modifier=self.modifier.name)
        self.modifier = self.extracted.modifiers.new(type="SMOOTH", name="SMOOTH_")
        self.modifier.iterations = 20
        self.modifier.factor = 0
        return {"RUNNING_MODAL"}

    def finish(self, context):
        bpy.ops.object.modifier_apply(modifier=self.modifier.name)
        bpy.ops.object.mode_set(mode="OBJECT")
        return {"FINISHED"}


class MaskDecimate(bpy.types.Operator):
    bl_idname = "sculptkt.decimate"
    bl_label = "Mask Decimate"
    bl_description = "Decimate the unmasked areas of the mesh."
    bl_options = {"REGISTER", "UNDO"}

    invoked = False

    popup = bpy.props.BoolProperty(default=False)

    ratio = bpy.props.FloatProperty(
        name="Ratio",
        description="How much to recuce",
        default=0.5,
        min=0.0000001,
        max=1.0
    )

    use_mask = bpy.props.BoolProperty(
        name="Use Mask",
        description="Take in account the sculpt mask",
        default=True
    )

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if not context.active_object.mode == "EDIT":
                return context.active_object.type == "MESH"

    def invoke(self, context, event):
        self.last_mode = context.active_object.mode
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.ed.undo_push()
        self.bm = bmesh.new()
        self.bm.from_mesh(context.active_object.data)
        if self.popup:
            wm = context.window_manager
            return wm.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def execute(self, context):

        print(self.use_mask)
        if self.use_mask:
            ob = context.active_object
            bm = self.bm
            bm.to_mesh(ob.data)

            layer = bm.verts.layers.paint_mask.verify()
            vg = ob.vertex_groups.new(name="paint_vertex_group_mask")
            vg.add([v.index for v in bm.verts], 1.0, "REPLACE")

            for vert in bm.verts:
                mask_val = vert[layer]
                vg.add([vert.index], 1 - mask_val, "REPLACE")

            md = ob.modifiers.new(type="DECIMATE", name="Decmater")
            md.ratio = self.ratio
            md.vertex_group = vg.name
            bpy.ops.object.modifier_apply(modifier=md.name)

            bm = bmesh.new()
            bm.from_mesh(ob.data)
            layer = bm.verts.layers.paint_mask.verify()

            for vert in bm.verts:
                vert[layer] = 1 - vg.weight(vert.index)

            ob.vertex_groups.remove(vg)

            bm.to_mesh(ob.data)
            bm.free()

        else:
            ob = context.active_object
            md = ob.modifiers.new(type="DECIMATE", name="Decimater")
            md.ratio = self.ratio
            bpy.ops.object.modifier_apply(modifier=md.name)

        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "ratio", slider=True)


class MaskSplit(bpy.types.Operator):
    bl_idname = "sculptkt.mask_split"
    bl_label = "Mask Split"
    bl_description = "Separate unmasked from masked areas in separate objects"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if len(context.selected_objects) == 1:
                return context.active_object.type == "MESH" and context.active_object.mode == "SCULPT"

    def invoke(self, context, event):
        bpy.ops.ed.undo_push()
        bpy.ops.object.mode_set(mode="OBJECT")
        return self.execute(context)

    def execute(self, context):

        ob = context.active_object

        for md in ob.modifiers:
            if md.type == "MULTIRES":
                self.report(type={"ERROR"}, message="Could not split object with multires modifier.")
                return {"CANCELLED"}

        bm = bmesh.new()
        bm.from_mesh(ob.data)
        mask = bm.verts.layers.paint_mask.verify()
        one_side = False
        other_side = False
        for face in bm.faces:
            avg_val = sum([vert[mask] for vert in face.verts]) / len(face.verts)
            if avg_val < 0.5:
                one_side = True
                face.select = True
            else:
                other_side = True
                face.select = False

        if not one_side and other_side:
            return {"CANCELLED"}

        bm.faces.ensure_lookup_table()
        bm.to_mesh(ob.data)
        bpy.ops.object.duplicate()
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.delete(type='FACE')
        self.dissolve_corner_verts()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.quads_convert_to_tris(ngon_method='CLIP')
        bpy.ops.object.mode_set(mode="OBJECT")

        context.scene.objects.active = ob
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.delete(type='FACE')
        self.dissolve_corner_verts()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.quads_convert_to_tris(ngon_method='CLIP')
        bpy.ops.object.mode_set(mode="OBJECT")
        return {"FINISHED"}

    def dissolve_corner_verts(self):
        bpy.ops.object.mode_set(mode="OBJECT")
        bm = bmesh.new()
        bm.from_mesh(bpy.context.active_object.data)

        dissolve = []
        for vert in bm.verts:
            if len(vert.link_edges) < 3:
                dissolve.append(vert)
        bmesh.ops.dissolve_verts(bm, verts=dissolve)

        bm.to_mesh(bpy.context.active_object.data)
        bpy.ops.object.mode_set(mode="EDIT")


class MaskDeformManipulator(bpy.types.Operator):
    bl_idname = "sculptkt.mask_deform_add"
    bl_label = "Add Mask Deform"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object.type == "MESH" and context.active_object.get("tagged_manipulators") is None \
               and context.active_object.mode == "SCULPT" if context.active_object else False

    def invoke(self, context, event):
        bpy.ops.ed.undo_push()
        bpy.ops.object.mode_set(mode="OBJECT")
        return self.execute(context)

    def execute(self, context):
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), r"objects", r"deform_rig.blend")
        ob = context.active_object
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        mask = bm.verts.layers.paint_mask.verify()

        vg = ob.vertex_groups.new(name="mask")

        sum_co = Vector()
        sum_val = 0
        for vert in bm.verts:
            weight = 1 - vert[mask]
            vg.add([vert.index], weight, "REPLACE")
            sum_co += vert.co * weight
            sum_val += weight

        avg_co = sum_co / sum_val
        avg_co.x *= ob.scale.x
        avg_co.y *= ob.scale.y
        avg_co.z *= ob.scale.z
        avg_co.rotate(ob.matrix_world)
        avg_co += ob.location

        with bpy.types.BlendDataLibraries.load(path) as (data_from, data_to):
            data_to.objects.append("Deform_rig")
            data_to.objects.append("Manipulator")
            data_to.objects.append("Lattice")

        for dt_ob in data_to.objects:
            context.scene.objects.link(dt_ob)
        data_to.objects[0].location = avg_co
        lattice = data_to.objects[2]
        latt_mod = ob.modifiers.new(type="LATTICE", name="Mask Lattice")
        latt_mod.object = lattice
        latt_mod.vertex_group = vg.name

        if ob.get("tag_manipulators") is not None:
            ob["tagged_manipulators"].extend(data_to.objects)
        else:
            ob["tagged_manipulators"] = data_to.objects

        return {"FINISHED"}


class MaskDeformManipulatorRemove(bpy.types.Operator):
    bl_idname = "sculptkt.mask_deform_remove"
    bl_label = "Remove Mask Deform"
    bl_description = ""
    bl_options = {"REGISTER"}

    only_delete = bpy.props.BoolProperty(
        name="Only delete",
        description="Will just remove the deformer without applyiing the modifier.",
        default=False
    )

    @classmethod
    def poll(cls, context):
        return context.active_object.get("tagged_manipulators") is not None if context.active_object else False

    def execute(self, context):
        ob = context.active_object

        for md in ob.modifiers:
            if not md.type == "LATTICE":
                continue

            if not md.object:
                continue

            if not md.vertex_group:
                continue

            if not md.object in ob["tagged_manipulators"]:
                continue

            vg = ob.vertex_groups[md.vertex_group]

            if self.only_delete:
                ob.modifiers.remove(md)
            else:
                print("apply")
                bpy.ops.object.modifier_apply(modifier=md.name)

            ob.vertex_groups.remove(vg)

        for remove_ob in ob["tagged_manipulators"]:
            if remove_ob.type == "MESH":
                bpy.data.meshes.remove(remove_ob.data)
            bpy.data.objects.remove(remove_ob)

        del ob["tagged_manipulators"]

        return {"FINISHED"}
