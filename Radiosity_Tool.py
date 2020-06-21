import bpy
import bmesh
from mathutils import Vector, Matrix, Quaternion, geometry
import math

from .Create_Blender_Thing import (
    createCollection,
    createLine,
    createFace,
    createCustomProperty,
    createPointCloud
)

from .delaunay_voronoi import(
    computeVoronoiDiagram,
)

def rayCastingObject(ob, ray_origin, ray_direction, culling=False):
    bm = bmesh.new()
    bm.from_object(ob, bpy.context.view_layer.depsgraph)
    bm.transform(ob.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    
    ray_direction.normalize()
    
    points = {}
    
    for face in bm.faces:
        if (culling and ray_direction.dot(face.normal) > 0.0):
            continue
        
        intersection = geometry.intersect_ray_tri(face.verts[0].co, face.verts[1].co, face.verts[2].co, ray_direction, ray_origin)
        if (intersection):
            distance = (ray_origin - intersection).length_squared
            points[distance] = intersection
            
    if (points):
        min_distance = min(points)
        return min_distance, points[min_distance]
    else:
        return None, None

def rayCastingMeshObjects(obs, ignore_obs, ray_origin, ray_direction, culling=False):
    intersection_points = {}
    for ob in obs:
        if(ob in ignore_obs or ob.hide_get()):
            continue
        if(ob.type == 'MESH'):
            dis, pos = rayCastingObject(ob, ray_origin, ray_direction, culling)
            if(dis):
                intersection_points[dis] = (pos, ob)
                    
    if(intersection_points):
        point = intersection_points[min(intersection_points)]
        return point

    return (None, None)

def createVoronoiDiagramByCircle(context, collection, points, name, circle_location=(0, 0, 0), circle_radius=1):
    vo_verts, vo_faces = computeVoronoiDiagram(points, 500.0, 500.0, polygonsOutput = True, formatOutput = True)

    obs = {}
    for idx, face in vo_faces.items():
        if(face[0] == face[-1]):
            face.pop()
        face_ob = createFace(context, collection, name + str(idx), verts=vo_verts, face=face, loop=False)
        obs[idx] = face_ob

    bpy.ops.object.select_all(action='DESELECT')

    # create circle
    bpy.ops.mesh.primitive_circle_add(enter_editmode=False, location=circle_location, radius=circle_radius)
    circle = context.active_object

    #refine by circle
    circle.select_set(True)
    temp = context.active_object
    for ob in obs.values():
        context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.knife_project(cut_through=True)
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        # delete outside polygon
        if (len(ob.data.polygons)>1):
            bpy.ops.object.mode_set(mode = 'EDIT')
            # edit mode to FACE
            context.tool_settings.mesh_select_mode = [False, False, True]
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='FACE')
            bpy.ops.object.mode_set(mode = 'OBJECT')

        ob.select_set(False)

    circle.select_set(False)

    verts = []
    for v in vo_verts:
        if(Vector(v).length_squared > 1.0):
            continue
        verts += [Vector(v).to_3d()]

    me = circle.data
    bm = bmesh.new()   # create an empty BMesh
    bm.from_mesh(me)

    for v in bm.verts:
        verts += [v.co.copy()]

    # delete circle
    circle.select_set(True)
    bpy.ops.object.delete(use_global=False)

    return obs, verts



def validateVPL(VPL, SPL):
    world_direction = SPL.location - VPL.location
    VPL_SPL_length = world_direction.length
    world_to_SPL_rotation = SPL.matrix_world.to_quaternion().to_matrix().inverted()
    SPL_direction = world_to_SPL_rotation @ -world_direction
    SPL_direction.normalize()

    # over spotlight angle range
    if (math.acos(SPL_direction @ Vector((0.0, 0.0, -1.0))) >= SPL.data.spot_size * 0.5):
        return None

    intersection, intersect_ob = rayCastingMeshObjects(
        bpy.data.objects, [VPL["Hit_Object"]], VPL.location, world_direction, culling=True)

    # occlusion between VPL and SPL
    if(intersection and (intersection - VPL.location).length < VPL_SPL_length):
        return None

    return SPL_direction


    


