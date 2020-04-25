import bpy
import bmesh

from mathutils import Vector, Matrix

# create collection under parent collection
# return:
# coll: bpy.types.collection, created collection
# parameter:
# parent_collection:    bpy.types.collection
# collection_name:      str
def createCollection(parent_collection, collection_name):
    # bpy.ops.collection.create(name=collection_name)
    bpy.data.collections.new(name=collection_name)
    coll = bpy.data.collections[collection_name]
    parent_collection.children.link(coll)
    return coll

def createCamera(collection, name, position):
    cam = bpy.data.cameras.new(name)
    cam.clip_end = 99999
    cam_ob = bpy.data.objects.new(name, cam)
    cam_ob.location = position
    collection.objects.link(cam_ob)

    return cam_ob


# return
# ob:   bpy.types.object
# parameter
# collection: this cube will create in this collection
# name: str
# position: Vector(x, y, z)
def createCube(collection, name, position, scale = 1.0):

    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    ob.location = position
    collection.objects.link(ob)

    verts = [
        (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5), (0.5, -0.5, -0.5),
        (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, -0.5, 0.5)]
    faces = [
        (0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
        (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]

    scale_verts = []
    for v in verts:
        scale_verts.append((scale * v[0], scale * v[1], scale * v[2]))


    me.from_pydata(scale_verts, [], faces)
    me.update(calc_edges = True)

    return ob

# return
# ob:   bpy.types.object
# parameter
# collection: this cube will create in this collection
# name: str
# head_pos: position of head is Vector(x, y, z)
# tail_pos: position of tail is Vector(x, y, z)
def createLine(collection, name, head_pos, tail_pos, ob=None):


    if(ob == None):
        me = bpy.data.meshes.new(name)
        ob = bpy.data.objects.new(name, me)
    ob.location = head_pos
    collection.objects.link(ob)

    bm = bmesh.new()   # create an empty BMesh
    bm.from_mesh(me)   # fill it in from a Mesh

    head = bm.verts.new((0.0, 0.0, 0.0))
    tail = bm.verts.new((tail_pos - head_pos))
    bm.edges.new((head, tail))

    bm.to_mesh(me)
    bm.free()  # free and prevent further access

    me.update(calc_edges = True)

    return ob
#   .   -
#  /|\  1
# /_|_\ -
#|--1--|
def createPyramid(collection, name, head_pos, tail_pos):
    
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    ob.location = head_pos
    collection.objects.link(ob)

    verts = [
        (-0.5, -0.5, 0), (0.5, -0.5, 0), (0.5, 0.5, 0), (-0.5, 0.5, 0), (0, 0, 1)]
    faces = [
        (3, 2, 1, 0), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]

    up = tail_pos - head_pos
    world_front = Vector([0, 1, 0])

    z = up.normalized().xyz
    x = world_front.cross(z.xyz)
    y = z.cross(x)
    rotation = Matrix((x, y, z)).transposed()
    
    transform_verts = []

    for v in verts:
        transform_verts.append((rotation @ Vector([v[0], v[1], up.length * v[2]])))

    me.from_pydata(transform_verts, [], faces)
    me.update(calc_edges = True)

    return ob



# return
# curve_ob:   bpy.types.object
# parameter
# collection: this cube will create in this collection
# name: str
# points:   list[Vector]
def createPolyCurve(context, collection, name, points):
    # create the Curve Datablock
    curve_data = bpy.data.curves.new(name, type='CURVE')
    curve_data.dimensions = '3D'
    #curveData.resolution_u = 3

    # map coords to spline
    polyline = curve_data.splines.new('POLY')  
    polyline.points.add(len(points)-1)  

    for i, point in enumerate(points):
        x,y,z = point
        polyline.points[i].co = (x, y, z, 1)
    
    # create Object
    curve_ob = bpy.data.objects.new(name, curve_data)
    curve_data.bevel_depth = 0.01

    # attach to scene and validate context
    collection.objects.link(curve_ob)
    context.view_layer.objects.active = curve_ob

    return curve_ob

# return
# b_point:  Vecotr
# parameter
# t:        float, parameter[0, 1]
# c_points: list[Vecotr], 4 control point

def createPointCloud(context, collection, name, points, dim='3D'):
    bm = bmesh.new()
    if (dim == '2D'):
        vs = [bm.verts.new(v.to_2d().to_3d()) for v in points]
    elif (dim == '3D'):
        vs = [bm.verts.new(v.to_3d()) for v in points]
    #[bm.edges.new([vs[i1], vs[i2]]) for i1, i2 in edges_new]
    #bm.faces.new([vs[face[0]], vs[face[1]], vs[face[2]]])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    context.view_layer.objects.active = ob

    return ob

def createFace(context, collection, name, verts, face, loop=True):
    bm = bmesh.new()
    # vs = [bm.verts.new(Vector(v).to_3d()) for v in verts]

    # vss = []
    # for f in face:
    #     vss += [vs[f]]
    # vss = [vs[f] for f in face]
    vs = [verts[f] for f in face]
    vs = [bm.verts.new(Vector(v).to_3d()) for v in vs]
    vss = [vs[i] for i in range(len(vs))]
    if (loop):
        vss.pop()
    
    bm.faces.new((vss[:]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)

    context.view_layer.objects.active = ob

    return ob


# warnning: name must be unique
# default_value can = float, list, bpy.object, string
def createCustomProperty(context, ob, name, default_value, description, soft_max = 1.0, soft_min = 0.0):
    # refer: bpy.ops.wm.properties_add(data_path="object")
    from rna_prop_ui import rna_idprop_ui_create

    o = context.active_object
    context.view_layer.objects.active = ob

    data_path = "object"
    item = eval("context.%s" % data_path)

    rna_idprop_ui_create(
        item, name,
        default     =default_value,
        description =description,
        soft_min    =soft_max,
        soft_max    =soft_min, )

    # reset
    context.view_layer.objects.active = o