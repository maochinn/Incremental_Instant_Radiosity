import bpy

from bpy.types import Operator
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    PointerProperty,
    IntProperty,
    StringProperty,
)
from mathutils import Vector, Matrix, Quaternion, geometry, Color
from .Create_Blender_Thing import (
    createCollection,
    createLine,
    createFace,
    createCustomProperty,
    createPointCloud
)
from .Radiosity_Tool import (
    rayCastingObject,
    rayCastingMeshObjects,
    validateVPL,
    createVoronoiDiagramByCircle
)
from .delaunay_voronoi import(
    computeVoronoiDiagram,
    
)

# surface_adaption_strength = FloatProperty(
#     name="Surface Adaption",
#     description="Surface Adaption Strength",
#     default =0.0,
#     soft_min=0.0,soft_max=1.0,
#     # options={'HIDDEN'},
# )
# phototropism_response_strength = FloatProperty(
#     name="Phototropism Response",
#     description="Phototropism Response Strength",
#     soft_min=0.0,soft_max=1.0,
#     # options={'HIDDEN'},
# )
# plant_depth = IntProperty(
#     name="Plant depth",
#     description="plant particle depth",
#     soft_min=0, soft_max=999
# )
# plant_type = EnumProperty(
#     name="Plant Type",
#     description="only for climbing plant object type",
#     items=(
#         ('SEED', "seed", "plant seed"),
#         ('PLANT', "plant", "plant particle")),
#     default='SEED',
#     options={'HIDDEN'},
# )
# Plant_object = PointerProperty(
#     type=bpy.types.ID,
#     name="Plant object",
#     description="climbing plant object",

# )

# #####
# # object bpy.types.Object
# #####
# def createParticleProperty(
#     context, particle, sa_strength, pr_strength, depth, plant_type, childs=[], parent=None):
#     context.view_layer.objects.active = particle
#     if parent == None:
#         parent = particle
#      # refer: bpy.ops.wm.properties_add(data_path="object")
#     from rna_prop_ui import rna_idprop_ui_create

#     data_path = "object"
#     item = eval("context.%s" % data_path)

#     rna_idprop_ui_create(
#         item, "Surface Adaption",
#         default     =sa_strength,
#         description =surface_adaption_strength[1]['description'],
#         soft_min    =surface_adaption_strength[1]['soft_min'],
#         soft_max    =surface_adaption_strength[1]['soft_max'], )
#     rna_idprop_ui_create(
#         item, "Phototropism Response",
#         default     =pr_strength,
#         description =phototropism_response_strength[1]['description'],
#         soft_min    =phototropism_response_strength[1]['soft_min'],
#         soft_max    =phototropism_response_strength[1]['soft_max'], )
#     rna_idprop_ui_create(
#         item, "Plant Depth",
#         default     =depth,
#         description =plant_depth[1]['description'],
#         soft_min    =plant_depth[1]['soft_min'],
#         soft_max    =plant_depth[1]['soft_max'], )
#     rna_idprop_ui_create(
#         item, "Plant type",
#         default     =plant_type)
#     rna_idprop_ui_create(
#         item, "childs",
#         default     =[])
#     rna_idprop_ui_create(
#         item, "parent",
#         default     =parent)



# class PlantSeeding(Operator):
#     bl_idname = "plant.seeding"
#     bl_label = "dynamic plant seeding"
#     bl_description = "seed plant root"
#     bl_options = {'REGISTER', 'UNDO'}

    
#     sa_strength :surface_adaption_strength
#     pr_strength :phototropism_response_strength
#     depth       :plant_depth
#     plant_type  :plant_type
#     location    :FloatVectorProperty(name="Location", default=(0, 0, 0))

#     @classmethod
#     def poll(cls, context):
#         return True
            
#     def invoke(self, context, event):
#         wm = context.window_manager

#         return wm.invoke_props_dialog(self)

#     def execute(self, context):
#         bpy.ops.mesh.primitive_uv_sphere_add(location=self.location)
#         seed = context.active_object
#         seed.name = "Seed"

#         createParticleProperty(
#             context, 
#             seed, 
#             self.sa_strength, 
#             self.pr_strength,
#             self.depth,
#             self.plant_type)
#         return {'FINISHED'}

class InstantRadiosityInitialize(Operator):
    bl_idname = "radiosity.initialize"
    bl_label = "instant radiosity"
    bl_description = "instant radiosity custom initialize"
    bl_options = {'REGISTER', 'UNDO'}

    # seeds = []

    @classmethod
    def poll(cls, context):
        return (
            context.active_object and context.active_object.children and context.active_object.type == 'LIGHT')
            
    def invoke(self, context, event):
        # wm = context.window_manager

        # return wm.invoke_props_dialog(self)
        return self.execute(context)
        
    def execute(self, context):
        spot_light = bpy.context.active_object
        hemi_sphere = spot_light.children[0]
        
        createCustomProperty(context, spot_light, "Type", 'SPL', "spotlight for instant radiosity")
        createCustomProperty(context, hemi_sphere, "Type", 'SPL_SIZE', "virtual spotlight ray size")

        point_light_collection  = createCollection(bpy.context.collection, "Indirect Lights")
        ray_collection          = createCollection(bpy.context.collection, "Rays")
        Voronoi_collection      = createCollection(bpy.context.collection, "Voronoi Diagram")

        hs_verts = []
        for vert in hemi_sphere.data.vertices.values():
            hs_verts += [Vector((vert.co[0], vert.co[1], vert.co[2]))]

        samples = []
        VPLs = []
        for vert in hs_verts:
            # transform to world space
            world_vert = spot_light.matrix_world @ vert

            intersection, intersect_ob = rayCastingMeshObjects(
                bpy.data.objects, spot_light.children, spot_light.location, world_vert - spot_light.location)
            if(intersection):
                # add ray
                ray = createLine(ray_collection, "ray", world_vert, intersection)
                # add VPL
                bpy.ops.object.light_add(type='POINT', radius=10, align='WORLD', location=intersection)
                VPL = bpy.context.active_object
                point_light_collection.objects.link(VPL)
                bpy.context.collection.objects.unlink(VPL)
                createCustomProperty(context, VPL, "Type", 'VPL', "virtiual point light for indirect illumination")
                createCustomProperty(context, VPL, "Ray", ray, "virtiual point light ray")
                createCustomProperty(context, VPL, "Hit_Object", intersect_ob, "ray hit this object")

                # samples[VPL] = vert
                samples += [vert]
                VPLs    += [VPL]

        createPointCloud(context, Voronoi_collection, name="SPL_Points", points=hs_verts, dim='2D')
        createPointCloud(context, Voronoi_collection, name="Sample_Points", points=samples, dim='2D')

        # create Voronoi Diagram and intersect by a circle
        voronoi_faces, vo_verts= createVoronoiDiagramByCircle(context, Voronoi_collection, samples, "Voronoi_face")
        for face in voronoi_faces.values():
            createCustomProperty(context, face, "Type", 'Voronoi_Face', "face of Voronoi Diagram")

        # link and compute area
        for sample_idx in range(len(VPLs)):
            createCustomProperty(context, VPLs[sample_idx], "Area", voronoi_faces[sample_idx], "Voronoi Face")
        
        # compute VPL intensity
        area_sum = 0.0
        for VPL in VPLs:
            area_sum += VPL['Area'].data.polygons[0].area
        
        SPL_color = Color(spot_light.data.color)
        SPL_energy = spot_light.data.energy
        for VPL in VPLs:
            ob_color = Color(VPL['Hit_Object'].material_slots[0].material.diffuse_color[0:3])
            VPL.data.color = [SPL_color.r * ob_color.r, SPL_color.g * ob_color.g, SPL_color.b * ob_color.b]
            VPL.data.energy = SPL_energy * (VPL['Area'].data.polygons[0].area / area_sum)

        # keyframe insert
        current = context.scene.frame_current = 1 
        
        # bpy.ops.anim.keyframe_insert_menu(type='Location')
        for VPL in VPLs:
            VPL.keyframe_insert(data_path='location', frame = current)
            VPL.data.keyframe_insert(data_path='color', frame = current)
            VPL.data.keyframe_insert(data_path='energy', frame = current)

        return {'FINISHED'}


class InstantRadiosityUpdate(Operator):
    bl_idname = "radiosity.update"
    bl_label = "instant radiosity update"
    bl_description = "instant radiosity update 1 frame"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return 'Type' in context.active_object.keys() and context.active_object['Type'] == 'SPL'
            
    def invoke(self, context, event):
        return self.execute(context)
        
    def execute(self, context):
        SPL = bpy.context.active_object
        # lights = bpy.data.collections['Indirect Lights']

        Voronoi_collection = bpy.data.collections["Voronoi Diagram"]

        samples = []
        VPLs = []
        invalid_VPLs = []
        face_obs = []

        for ob in bpy.data.objects:
            if ('Type' in ob.keys() ):
                if (ob['Type'] == 'VPL'):
                    VPLs += [ob]
                elif (ob['Type'] == 'Voronoi_Face'):
                    face_obs += [ob]

        # determine the validity of each VPL
        for VPL in VPLs:
            intersection = validateVPL(VPL, SPL)
            if (intersection):
                intersection = SPL.matrix_world.inverted() @ intersection
                samples += [intersection.to_2d().to_3d()]
            else:
                invalid_VPLs += [VPL]
                VPL.hide_viewport = True
                
        # Remove all invalid VPLs and Possibly a number of valid ones to imporvement the distribution
        for iVPLs in invalid_VPLs:
            VPLs.remove(iVPLs)

        if (invalid_VPLs != []):
            return {'FINISHED'}

        # Create new VPLs accroding to allotted budget.

        # delete all old Voronoi face
        bpy.ops.object.select_all(action='DESELECT')
        for face in Voronoi_collection.all_objects:
            face.select_set(True)
        bpy.ops.object.delete()
        # create new Voronoi face
        voronoi_faces, vo_verts= createVoronoiDiagramByCircle(context, Voronoi_collection, samples, "Voronoi_face")
        # search min distance in all voronoi vertices
        distances = {}
        for v in vo_verts:
            s = 0.0
            for sample in samples:
                s += (sample.to_2d()-Vector(v)).length
            distances[s] = v
        sort_vo_verts = [distances[k] for k in sorted(distances.keys())] 
        # maximum number for try to add 
        add_VPL_max = 10
        for i in range(add_VPL_max):
            if (i >= len(invalid_lights)):
                break
            if (sort_vo_verts == []):
                break

            VPL = invalid_VPLs[i]

            vert = sort_vo_verts.pop()
            local_v = Vector(vert.x, vert.x, sqrt(1.0 - vert.length_squared))
            world_v = spot_light.matrix_world @ local_v

            intersection, intersect_ob = rayCastingMeshObjects(
                bpy.data.objects, SPL.children, SPL.location, world_v - SPL.location)

            if(intersection):
                # valid
                VPL.hide_viewport = False
                # modify ray
                ray = editLine(VPL["Ray"], world_v, intersection)
                # modify VPL
                VPL.location = intersection
                VPL["Hit_Object"] = intersect_ob

                samples += [vert]
                VPLs    += [VPL]
        

        # delete all old Voronoi face
        bpy.ops.object.select_all(action='DESELECT')
        for face in Voronoi_collection.all_objects:
            face.select_set(True)
        bpy.ops.object.delete()
        # recompute Voronoi Diagram and intersect by a circle
        voronoi_faces = createVoronoiDiagramByCircle(context, Voronoi_collection, samples, "Voronoi_face")
        editPointCloud(bpy.data.objects['Sample_Points'], samples)

        for face in voronoi_faces:
            createCustomProperty(context, face, "Type", 'Voronoi_Face', "face of Voronoi Diagram")

        # link and recompute area
        for sample_idx in range(len(VPLs)):
            VPLs[sample_idx]["Area"] = voronoi_faces[sample_idx]
            # createCustomProperty(context, VPLs[sample_idx], "Area", voronoi_faces[sample_idx], "Voronoi Face")

        # Compute intensities for VPLs.
        area_sum = 0.0
        for VPL in VPLs:
            area_sum += VPL['Area'].data.polygons[0].area
        
        SPL_color = Color(SPL.data.color)
        SPL_energy = SPL.data.energy
        for VPL in VPLs:
            ob_color = Color(VPL['Hit_Object'].material_slots[0].material.diffuse_color[0:3])
            VPL.data.color = [SPL_color.r * ob_color.r, SPL_color.g * ob_color.g, SPL_color.b * ob_color.b]
            VPL.data.energy = SPL_energy * (VPL['Area'].data.polygons[0].area / area_sum)

        # keyframe insert
        current = context.scene.frame_current + 1
        
        for VPL in VPLs:
            VPL.keyframe_insert(data_path='location', frame = current)
            VPL.data.keyframe_insert(data_path='color', frame = current)
            VPL.data.keyframe_insert(data_path='energy', frame = current)


        context.scene.frame_current = current

        return {'FINISHED'}
