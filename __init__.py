bl_info = {
    "name": "Incremental Instant Radiosity",
    "author": "maochinn",
    "version": (1, 1, 0),
    "blender": (2, 82, 0),
    "location": "",
    "description": "Simple Implement",
    "warning": "",
    "wiki_url": "",
    "support": 'TESTING',
    "category": "Object",
}



import bpy

from . Radiosity_Panel import InstantRadiosityPanel
from . Radiosity_Operator import InstantRadiosityInitialize

classes = (InstantRadiosityPanel, InstantRadiosityInitialize)

register, unregister = bpy.utils.register_classes_factory(classes)

