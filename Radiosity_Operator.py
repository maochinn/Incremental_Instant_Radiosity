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
from mathutils import Vector, Matrix, Quaternion, geometry
from .Create_Blender_Thing import (
    createCollection,
    createLine,
    createFace,
    createCustomProperty,
    createPointCloud
)
from .Radiosity_Tool import (
    rayCastingObject,
    validateVPL
)
from .delaunay_voronoi import(
    computeVoronoiDiagram
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

        samples = {}
        for vert in hs_verts:
            v = spot_light.matrix_world @ vert

            intersection_points = {}
            for ob in bpy.data.objects:
                if(ob.parent and ob.parent.type == 'LIGHT'):
                    continue
                if(ob.type == 'MESH'):
                    dis, pos = rayCastingObject(ob, spot_light.location, v - spot_light.location)
                    if(dis):
                        intersection_points[dis] = pos
                        
            if(intersection_points):
                min_distance = min(intersection_points)

                ray = createLine(ray_collection, "ray", v, intersection_points[min_distance])

                bpy.ops.object.light_add(
                    type='POINT', radius=1, align='WORLD', location=intersection_points[min_distance])
                VPL = bpy.context.active_object
                point_light_collection.objects.link(VPL)
                bpy.context.collection.objects.unlink(VPL)
                createCustomProperty(context, VPL, "Type", 'VPL', "virtiual point light for indirect illumination")
                createCustomProperty(context, VPL, "Ray", ray, "virtiual point light ray")

                samples[VPL] = vert

        createPointCloud(context, Voronoi_collection, name="SPL_Points", points=hs_verts, dim='2D')
        createPointCloud(context, Voronoi_collection, name="Sample_Points", points=samples.values(), dim='2D')
        vo_verts, vo_faces = computeVoronoiDiagram(samples.values(), 100.0, 100.0, polygonsOutput = True, formatOutput = True) 

        for i in range(len(vo_verts)):
            v = Vector(vo_verts[i])
            if(v.length > 1.0):
                vo_verts[i] = v.normalized().xy.to_tuple()

        for idx, face in vo_faces.items():
            createFace(context, Voronoi_collection, "Voronoi_face", verts=vo_verts, face=face, loop=True)


        return {'FINISHED'}


class InstantRadiosityUpdate():
    bl_idname = "radiosity.update"
    bl_label = "instant radiosity update"
    bl_description = "instant radiosity custom initialize"
    bl_options = {'REGISTER', 'UNDO'}

    # seeds = []

    @classmethod
    def poll(cls, context):
        return 'Type' in context.active_object.keys() and context.active_object['Type'] == 'SPL'
            
    def invoke(self, context, event):
        return self.execute(context)
        
    def execute(self, context):
        spot_light = bpy.context.active_object
        lights = bpy.context.collection

        intersection_list = []
        vaild_list = []
        # determine the validity of each VPL
        for light in lights.all_objects.values():
            intersection = validateVPL(light, spot_light)
            if (intersection):
                intersection = spot_light.matrix_world.inverted() @ intersection
                intersection_list += [intersection.to_2d().to_3d()]
            else:
                invalid_list += [light]
        # Remove all invalid VPLs and Possibly a number of valid ones to imporvement the distribution
        for invalid_lights in invalid_list:
            invalid_lights.hide_viewport = False
        # Create new VPLs accroding to allotted budget.
        vo_verts, vo_faces = computeVoronoiDiagram(intersection_list, 100.0, 100.0, polygonsOutput = True, formatOutput = True) 

        for i in range(len(vo_verts)):
            v = Vector(vo_verts[i])
            if(v.length > 1.0):
                vo_verts[i] = v.normalized().xy.to_tuple()

        distances = {}
        for v in vo_verts:
            s = 0.0
            for inter in intersection_list:
                s += (inter-Vector(v)).length
            distances[s] = v

        sort_vo_verts = [distances[k] for k in sorted(distances.keys())] 

        i = 0
        while(1):
            VPL = invalid_lights[i]
            if (i >= len(invalid_lights)):
                break
            if (sort_vo_verts == []):
                break
        # for VPL in invalid_lights:
            vert = sort_vo_verts.pop()
            v = Vector(vert.x, vert.x, sqrt(1.0 - vert.length_squared))
            v = spot_light.matrix_world @ v

            intersection_points = {}
            for ob in bpy.data.objects:
                if(ob.parent and ob.parent.type == 'LIGHT'):
                    continue
                if(ob.type == 'MESH'):
                    dis, pos = rayCastingObject(ob, spot_light.location, v - spot_light.location)
                    if(dis):
                        intersection_points[dis] = pos
            if(intersection_points):
                intersection = intersection_points[min(intersection_points)]

                VPL.location = intersection
                ray = VPL["Ray"]
                createLine(bpy.data.collection['Rays'], ray.name, v, intersection)
                i+=1
            

        # Compute intensities for VPLs.
