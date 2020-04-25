import bpy
import bmesh
from mathutils import Vector, Matrix, Quaternion, geometry

def rayCastingObject(ob, ray_origin, ray_direction):
    bm = bmesh.new()
    bm.from_object(ob, bpy.context.view_layer.depsgraph)
    bm.transform(ob.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    
    ray_direction.normalize()
    
    points = {}
    
    for face in bm.faces:
        intersection = geometry.intersect_ray_tri(face.verts[0].co, face.verts[1].co, face.verts[2].co, ray_direction, ray_origin)
        if (intersection):
            distance = (ray_origin - intersection).length_squared
            points[distance] = intersection
            
    if (points):
        min_distance = min(points)
        return min_distance, points[min_distance]
    else:
        return None, None

# def reproject():


#     hs_verts = []

#     for light in lights.all_objects.values():
#     #    ray_casting_object(spot_light.children[0], lights.location, dir)
#     dir = (spot_light.location - light.location).normalized()
#     points = {}
#     for ob in bpy.data.objects:
#         if(ob.type == 'MESH'):
#             dis, pos = ray_casting_object(ob, light.location, dir)
#             if(dis):
#                 points[dis] = (pos, ob)
                    
#         if(points):
#             min_distance = min(points)
            
#             if(points[min_distance][1].parent and points[min_distance][1].parent.type == 'LIGHT'):
#                 spot = points[min_distance][1].parent
#                 v = spot.matrix_world.inverted() @ points[min_distance][0]
#                 hs_verts += [v]


def validateVPL(VPL, SPL):
    direction = (SPL.location - VPL.location).normalized()

    points = {}
    for ob in bpy.data.objects:
        if(ob.type == 'MESH'):
            dis, pos = rayCastingObject(ob, VPL.location, direction)
            if(dis):
                points[dis] = (pos, ob)

    if(points):
        min_distance = min(points)
        intersection, ob = points[min_distance]
        if (ob.parent is SPL):
            # return SPL.matrix_world.inverted() @ intersection
            return intersection

    return None


    


