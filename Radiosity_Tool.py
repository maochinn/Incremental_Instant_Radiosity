import bpy
import bmesh
from mathutils import Vector, Matrix, Quaternion, geometry

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
        if(ob in ignore_obs):
            continue
        if(ob.type == 'MESH'):
            dis, pos = rayCastingObject(ob, ray_origin, ray_direction, culling)
            if(dis):
                intersection_points[dis] = (pos, ob)
                    
    if(intersection_points):
        point = intersection_points[min(intersection_points)]
        return point

    return None, None

def createVoronoiDiagramByCircle(context, collection, points, name, circle_location=(0, 0, 0), circle_radius=1):
    # create circle
    bpy.ops.mesh.primitive_circle_add(enter_editmode=False, location=circle_location, radius=circle_radius)
    circle = context.active_object

    #
    vo_verts, vo_faces = computeVoronoiDiagram(points, 100.0, 100.0, polygonsOutput = True, formatOutput = True)

    obs = {}
    for idx, face in vo_faces.items():
        face_ob = createFace(context, collection, name + str(idx), verts=vo_verts, face=face, loop=True)
        obs[idx] = face_ob

    bpy.ops.object.select_all(action='DESELECT')
    #refine by circle
    circle.select_set(True)
    temp = context.active_object
    for ob in obs.values():
        context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.knife_project()
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
    # delete circle
    circle.select_set(True)
    bpy.ops.object.delete(use_global=False)


    return obs, vo_verts



def validateVPL(VPL, SPL):
    direction = (SPL.location - VPL.location).normalized()
    
    # avoid hit on vertices and no hit on face
    # direction[0] += 0.001
    # direction[1] += 0.001
    # direction[2] += 0.001

    intersection, intersect_ob = rayCastingMeshObjects(
        bpy.data.objects, [VPL["Hit_Object"]], VPL.location, direction, culling=True)
    
    if(intersection):
        if (intersect_ob.parent is SPL):
            return intersection

    return None


    


