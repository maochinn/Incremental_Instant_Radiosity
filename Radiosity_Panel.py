import bpy


class InstantRadiosityPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_INSTANT_RADIOSITY"
    bl_label = "Instant_Radiosity"
    bl_category = "Instant Radiosity Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator('radiosity.initialize', text="initialize")
        row = layout.row()
        row.operator('radiosity.update', text="update")
