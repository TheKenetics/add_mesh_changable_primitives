bl_info = {
	"name": "Changable Primitive",
	"author": "Kenetics",
	"version": (0, 1),
	"blender": (2, 80, 0),
	"location": "View3D > Toolshelf > Add Objects",
	"description": "Add primitives whose properties can be changed after creation",
	"warning": "",
	"wiki_url": "",
	"category": "Add Mesh"
}

import bpy, bmesh
from bpy.props import EnumProperty, IntProperty, IntVectorProperty, FloatVectorProperty, BoolProperty, FloatProperty, StringProperty
from bpy.types import PropertyGroup, Menu, Panel, Operator
from mathutils import Matrix
from math import radians

"""
Plan
Objects
Plane
Cube
Cylinder
Sphere
Icosphere
Torus
Cone

Complex Objects
Tube
Arc

General Properties
Location
rotation
Scale

Plane Properties
X Y subdivs

Cube Properties
X Y Z subdivs

Cylinder
Sides
Radius
Length
Cap type
How to do subdivs?

Sphere
Radius
Subdivs

Icosphere
Radius
Resolution

Torus
Major radius
Minor radius
Subdivs

Cone
Sides
Radius
Height

Tube
Cylinder Props
Offset
Thickness

Arc
Cube Props
Center
Angle
"""

## Helper Functions

def create_and_link_mesh_object(context, name):
	"""Creates and links a mesh object to the active scene and collection, and returns it."""
	obj_data = context.blend_data.meshes.new(name)
	obj = context.blend_data.objects.new(name, obj_data)
	
	# link to active collection
	context.collection.objects.link(obj)
	
	return obj

def update_changable_primitive(self, context):
	"""UI Helper function to update changable primitive after settings change."""
	if not context.active_object.data.changable_primitive_settings.enabled:
		print("Can't update meshes that aren't changable primitives!")
		return
	
	if context.active_object.data.changable_primitive_settings.type == "PLANE":
		bpy.ops.object.cp_ot_update_plane()
	elif context.active_object.data.changable_primitive_settings.type == "CUBE":
		bpy.ops.object.cp_ot_update_cube()
	elif context.active_object.data.changable_primitive_settings.type == "CIRCLE":
		bpy.ops.object.cp_ot_update_circle()
	elif context.active_object.data.changable_primitive_settings.type == "CYLINDER":
		bpy.ops.object.cp_ot_update_cylinder()
	elif context.active_object.data.changable_primitive_settings.type == "CONE":
		bpy.ops.object.cp_ot_update_cone()
	elif context.active_object.data.changable_primitive_settings.type == "UVSPHERE":
		bpy.ops.object.cp_ot_update_uvsphere()
	elif context.active_object.data.changable_primitive_settings.type == "ICOSPHERE":
		bpy.ops.object.cp_ot_update_icosphere()
	elif context.active_object.data.changable_primitive_settings.type == "TORUS":
		bpy.ops.object.cp_ot_update_torus()
	else:
		print("You haven't implemented " + context.active_object.data.changable_primitive_settings.type + " in master update yet!")

def edge_verts_distance(edge_verts, axis_index):
	"""Returns distance between two edge_verts along an axis."""
	return abs(edge_verts[0].co[axis_index] - edge_verts[1].co[axis_index])

def enable_smooth_shading(obj):
	"""Enables smooth shading for object data"""
	
	for poly in obj.data.polygons:
		poly.use_smooth = True

## Structs

class CP_changable_primitive_settings(PropertyGroup):
	"""Holds settings for changable primitive, used to update mesh"""
	enabled : BoolProperty(
		name="Enabled",
		default=False
	)
	
	# TODO: Set icons to correct mesh type
	type : EnumProperty(
		items=[
			("PLANE","Plane","","MESH_PLANE",0),
			("CUBE","Cube","","MESH_CUBE",1),
			("CIRCLE","Circle","","MESH_CUBE",2),
			("CYLINDER","Cylinder","","MESH_CUBE",3),
			("UVSPHERE","UV Sphere","","MESH_CUBE",4),
			("ICOSPHERE","Icosphere","","MESH_CUBE",5),
			("TORUS","Torus","","MESH_CUBE",6),
			("CONE","Cone","","MESH_CUBE",7),
			("TUBE","Tube","","MESH_CUBE",8),
			("ARC","Arc","","MESH_CUBE",9),
			],
		name="Type"
	)
	
	"""
	Note about subdivision properties:
	x is also used for circular segments
	y is also used for circular u subdivisions, ie: the subdivisions from inside to outside of a cylinder
	z is also used for circular v subdivisions, ie: the subdivisions going up and down a cylinder
	"""
	x_subdivisions : IntProperty(
		name="X Subdivisions",
		min=1,
		default=2,
		update=update_changable_primitive
	)
	y_subdivisions : IntProperty(
		name="Y Subdivisions",
		min=2,
		default=2,
		update=update_changable_primitive
	)
	z_subdivisions : IntProperty(
		name="Z Subdivisions",
		min=2,
		default=2,
		update=update_changable_primitive
	)
	
	cap_type : EnumProperty(
		items=[
			("NONE","No Cap","","",0),
			("TRI","Triangle Cap","","",1),
			("FACE","Face Cap","","",2),
		],
		name="Cap Type",
		update=update_changable_primitive
	)
	
	radius : FloatProperty(
		name="Radius",
		default=1,
		update=update_changable_primitive,
		unit='LENGTH'
	)
	
	diameter1 : FloatProperty(
		name="Diameter 1",
		default=1,
		update=update_changable_primitive,
		unit='LENGTH'
	)
	
	diameter2 : FloatProperty(
		name="Diameter 2",
		default=1,
		update=update_changable_primitive,
		unit='LENGTH'
	)
	
	# Also used for plane size, cube size
	height : FloatProperty(
		name="Height",
		default=1,
		update=update_changable_primitive,
		unit='LENGTH'
	)
	
	use_smooth_shading : BoolProperty(
		name="Smooth Shading",
		description="Enables smooth shading when mesh is updated.",
		default=False,
		update=update_changable_primitive
	)


## Operators

class CP_OT_create_plane(Operator):
	"""Creates a new Changable Plane"""
	bl_idname = "object.cp_ot_create_plane"
	bl_label = "Create Changable Plane"
	bl_options = {'REGISTER','UNDO'}
	
	# Properties
	subdivisions : IntVectorProperty(
		name = "Subdivisions",
		size=2,
		default=(2,2),
		min=1
	)
	
	size : FloatProperty(
		name="Size",
		default=1.0,
		unit='LENGTH'
	)
	
	align_rot_to_cursor : BoolProperty(
		name="Align Rotation to 3D Cursor",
		default=False
	)

	@classmethod
	def poll(cls, context):
		return context.mode == "OBJECT"

	def execute(self, context):
		# Deselect all objects
		for obj in context.selected_objects:
			obj.select_set(False)
		
		# Create mesh and object
		obj = create_and_link_mesh_object(context, "ChangablePlane")
		obj.location = context.scene.cursor.location.copy()
		if self.align_rot_to_cursor:
			obj.rotation_euler = context.scene.cursor.rotation_euler.copy()
		
		# Change drawing options
		obj.show_wire = True
		obj.show_all_edges = True
		
		# Set created object as active
		obj.select_set(True)
		context.view_layer.objects.active = obj
		
		# Initialize Changable Primitive Settings
		settings = obj.data.changable_primitive_settings
		settings.enabled = True
		settings.x_subdivisions = self.subdivisions[0]
		settings.y_subdivisions = self.subdivisions[1]
		settings.z_subdivisions = 2
		settings.height = self.size
		
		# Create mesh
		bpy.ops.object.cp_ot_update_plane()
		
		return {'FINISHED'}


class CP_OT_update_plane(Operator):
	"""Updates a changable plane"""
	bl_idname = "object.cp_ot_update_plane"
	bl_label = "Update Changable Plane"
	bl_options = {'REGISTER','UNDO','INTERNAL'}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == "MESH"

	def execute(self, context):
		x_subdivisions = context.active_object.data.changable_primitive_settings.x_subdivisions
		y_subdivisions = context.active_object.data.changable_primitive_settings.y_subdivisions
		size = context.active_object.data.changable_primitive_settings.height
		use_smooth_shading = context.active_object.data.changable_primitive_settings.use_smooth_shading
		
		bm = bmesh.new()
		bm.from_mesh(context.active_object.data)
		
		if bm.verts:
			bmesh.ops.delete(bm, geom=bm.verts, context="VERTS")
		bmesh.ops.create_grid(bm, x_segments=x_subdivisions, y_segments=y_subdivisions, size=size, calc_uvs=True)
		
		bm.to_mesh(context.active_object.data)
		bm.free()
		
		if use_smooth_shading:
			enable_smooth_shading(context.active_object)
		
		context.active_object.update_tag()
		
		return {'FINISHED'}


class CP_OT_create_cube(Operator):
	"""Creates a new Changable Cube"""
	bl_idname = "object.cp_ot_create_cube"
	bl_label = "Create Changable Cube"
	bl_options = {'REGISTER','UNDO'}
	
	# Properties
	subdivisions : IntVectorProperty(
		name = "Subdivisions",
		size=3,
		default=(2,2,2),
		min=2
	)
	
	size : FloatProperty(
		name="Size",
		default=1.0,
		unit='LENGTH'
	)
	
	align_rot_to_cursor : BoolProperty(
		name="Align Rotation to 3D Cursor",
		default=False
	)

	@classmethod
	def poll(cls, context):
		return context.mode == "OBJECT"

	def execute(self, context):
		# Deselect all objects
		for obj in context.selected_objects:
			obj.select_set(False)
		
		# Create mesh and object
		obj = create_and_link_mesh_object(context, "ChangableCube")
		obj.location = context.scene.cursor.location.copy()
		if self.align_rot_to_cursor:
			obj.rotation_euler = context.scene.cursor.rotation_euler.copy()
		
		# Change draw options
		obj.show_wire = True
		obj.show_all_edges = True
		
		# Set created object as active
		obj.select_set(True)
		context.view_layer.objects.active = obj
		
		# Initialize Changable Primitive Settings
		settings = obj.data.changable_primitive_settings
		settings.enabled = True
		settings.type = "CUBE"
		settings.x_subdivisions = self.subdivisions[0]
		settings.y_subdivisions = self.subdivisions[1]
		settings.z_subdivisions = self.subdivisions[2]
		settings.height = self.size
		
		# Create mesh
		bpy.ops.object.cp_ot_update_cube()
		
		return {'FINISHED'}


class CP_OT_update_cube(Operator):
	"""Updates a Changable Cube"""
	bl_idname = "object.cp_ot_update_cube"
	bl_label = "Update Changable Cube"
	bl_options = {'REGISTER','UNDO', 'INTERNAL'}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == "MESH"

	def execute(self, context):
		x_subdivisions = context.active_object.data.changable_primitive_settings.x_subdivisions
		y_subdivisions = context.active_object.data.changable_primitive_settings.y_subdivisions
		z_subdivisions = context.active_object.data.changable_primitive_settings.z_subdivisions
		size = context.active_object.data.changable_primitive_settings.height
		use_smooth_shading = context.active_object.data.changable_primitive_settings.use_smooth_shading
		
		bm = bmesh.new()
		bm.from_mesh(context.active_object.data)
		
		# Delete old mesh
		if bm.verts:
			bmesh.ops.delete(bm, geom=bm.verts, context="VERTS")
		bmesh.ops.create_cube(bm, size=size, calc_uvs=True)
		
		# Subdivide X edges
		if x_subdivisions > 2:
			x_edges = [edge for edge in bm.edges if edge_verts_distance(edge.verts, 0) > 0]
			bmesh.ops.subdivide_edges(bm, edges=x_edges, cuts=x_subdivisions-2)
		
		# Subdivide Y edges
		if y_subdivisions > 2:
			y_edges = [edge for edge in bm.edges if edge_verts_distance(edge.verts, 1) > 0]
			bmesh.ops.subdivide_edges(bm, edges=y_edges, cuts=y_subdivisions-2)
		
		# Subdivide Z edges
		if z_subdivisions > 2:
			z_edges = [edge for edge in bm.edges if edge_verts_distance(edge.verts, 2) > 0]
			bmesh.ops.subdivide_edges(bm, edges=z_edges, cuts=z_subdivisions-2)
		
		bm.to_mesh(context.active_object.data)
		bm.free()
		
		if use_smooth_shading:
			enable_smooth_shading(context.active_object)
		
		context.active_object.update_tag()
		
		return {'FINISHED'}



class CP_OT_create_circle(Operator):
	"""Creates a new Changable Circle"""
	bl_idname = "object.cp_ot_create_circle"
	bl_label = "Create Changable Circle"
	bl_options = {'REGISTER','UNDO'}
	
	# Properties
	segments : IntProperty(
		name = "Segments",
		default=32,
		min=3
	)
	
	u_subdivisions : IntProperty(
		name = "U Subdivisions",
		default=2,
		min=2
	)
	
	radius : FloatProperty(
		name="Radius",
		default=1.0,
		unit='LENGTH'
	)
	
	cap_type : EnumProperty(
		items=[
			("NONE","No Cap","","",0),
			("TRI","Triangle Cap","","",1),
			("FACE","Face Cap","","",2),
		],
		name="Cap Type"
	)
	
	align_rot_to_cursor : BoolProperty(
		name="Align Rotation to 3D Cursor",
		default=False
	)

	@classmethod
	def poll(cls, context):
		return context.mode == "OBJECT"

	def execute(self, context):
		# Deselect all objects
		for obj in context.selected_objects:
			obj.select_set(False)
		
		# Create mesh and object
		obj = create_and_link_mesh_object(context, "ChangableCircle")
		obj.location = context.scene.cursor.location.copy()
		if self.align_rot_to_cursor:
			obj.rotation_euler = context.scene.cursor.rotation_euler.copy()
		
		# Change draw options
		obj.show_wire = True
		obj.show_all_edges = True
		
		# Set created object as active
		obj.select_set(True)
		context.view_layer.objects.active = obj
		
		# Initialize Changable Primitive Settings
		settings = obj.data.changable_primitive_settings
		settings.enabled = True
		settings.type = "CIRCLE"
		settings.x_subdivisions = self.segments
		settings.y_subdivisions = self.u_subdivisions
		settings.cap_type = self.cap_type
		settings.radius = self.radius
		
		# Create Mesh
		bpy.ops.object.cp_ot_update_circle()
		
		return {'FINISHED'}


class CP_OT_update_circle(Operator):
	"""Updates a changable cube"""
	bl_idname = "object.cp_ot_update_circle"
	bl_label = "Update Changable Circle"
	bl_options = {'REGISTER','UNDO', 'INTERNAL'}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == "MESH"

	def execute(self, context):
		segments = context.active_object.data.changable_primitive_settings.x_subdivisions
		u_subdivisions = context.active_object.data.changable_primitive_settings.y_subdivisions
		cap_type = context.active_object.data.changable_primitive_settings.cap_type
		radius = context.active_object.data.changable_primitive_settings.radius
		use_smooth_shading = context.active_object.data.changable_primitive_settings.use_smooth_shading
		
		bm = bmesh.new()
		bm.from_mesh(context.active_object.data)
		
		# Delete old mesh
		if bm.verts:
			bmesh.ops.delete(bm, geom=bm.verts, context="VERTS")
		
		# Create Circle
		if cap_type == "NONE":
			bmesh.ops.create_circle(bm, segments=segments, radius=radius, calc_uvs=True)
		elif cap_type == "FACE":
			bmesh.ops.create_circle(bm, segments=segments, radius=radius, cap_ends=True, calc_uvs=True)
		else:
			bmesh.ops.create_circle(bm, segments=segments, radius=radius, cap_ends=True, cap_tris=True, calc_uvs=True)
		
		if u_subdivisions > 2 and cap_type == "TRI":
			center_vert = None
			
			for vert in bm.verts:
				if vert.co[0] == 0.0 and vert.co[1] == 0.0:
					center_vert = vert
					break
			
			bmesh.ops.subdivide_edges(bm, edges=center_vert.link_edges, cuts=u_subdivisions-2)
		
		bm.to_mesh(context.active_object.data)
		bm.free()
		
		if use_smooth_shading:
			enable_smooth_shading(context.active_object)
		
		context.active_object.update_tag()
		
		return {'FINISHED'}


class CP_OT_create_cylinder(Operator):
	"""Creates a new Changable Cylinder"""
	bl_idname = "object.cp_ot_create_cylinder"
	bl_label = "Create Changable Cylinder"
	bl_options = {'REGISTER','UNDO'}
	
	# Properties
	segments : IntProperty(
		name = "Segments",
		default=32,
		min=3
	)
	
	u_subdivisions : IntProperty(
		name = "Segments",
		default=2,
		min=2
	)
	
	v_subdivisions : IntProperty(
		name = "Segments",
		default=2,
		min=2
	)
	
	diameter : FloatProperty(
		name="Diameter",
		default=1.0,
		unit='LENGTH'
	)
	
	height : FloatProperty(
		name="Height",
		default=1.0,
		unit='LENGTH'
	)
	
	cap_type : EnumProperty(
		items=[
			("NONE","No Cap","","",0),
			("TRI","Triangle Cap","","",1),
			("FACE","Face Cap","","",2),
		],
		name="Cap Type"
	)
	
	align_rot_to_cursor : BoolProperty(
		name="Align Rotation to 3D Cursor",
		default=False
	)

	@classmethod
	def poll(cls, context):
		return context.mode == "OBJECT"

	def execute(self, context):
		# Deselect all objects
		for obj in context.selected_objects:
			obj.select_set(False)
		
		# Create mesh and object
		obj = create_and_link_mesh_object(context, "ChangableCylinder")
		obj.location = context.scene.cursor.location.copy()
		if self.align_rot_to_cursor:
			obj.rotation_euler = context.scene.cursor.rotation_euler.copy()
		
		# Change draw options
		obj.show_wire = True
		obj.show_all_edges = True
		
		# Set created object as active
		obj.select_set(True)
		context.view_layer.objects.active = obj
		
		# Initialize Changable Primitive Settings
		settings = obj.data.changable_primitive_settings
		settings.enabled = True
		settings.type = "CYLINDER"
		settings.x_subdivisions = self.segments
		settings.y_subdivisions = self.u_subdivisions
		settings.z_subdivisions = self.v_subdivisions
		settings.height = self.height
		settings.diameter1 = self.diameter
		settings.cap_type = self.cap_type
		
		# Create Mesh
		bpy.ops.object.cp_ot_update_cylinder()
		
		return {'FINISHED'}


class CP_OT_update_cylinder(Operator):
	"""Updates a changable cylinder"""
	bl_idname = "object.cp_ot_update_cylinder"
	bl_label = "Update Changable Cylinder"
	bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == "MESH"

	def execute(self, context):
		segments = context.active_object.data.changable_primitive_settings.x_subdivisions
		u_subdivisions = context.active_object.data.changable_primitive_settings.y_subdivisions
		v_subdivisions = context.active_object.data.changable_primitive_settings.z_subdivisions
		cap_type = context.active_object.data.changable_primitive_settings.cap_type
		height = context.active_object.data.changable_primitive_settings.height
		diameter = context.active_object.data.changable_primitive_settings.diameter1
		use_smooth_shading = context.active_object.data.changable_primitive_settings.use_smooth_shading
		
		bm = bmesh.new()
		bm.from_mesh(context.active_object.data)
		
		# Delete old mesh
		if bm.verts:
			bmesh.ops.delete(bm, geom=bm.verts, context="VERTS")
		
		# Create Cylinder
		if cap_type == "NONE":
			bmesh.ops.create_cone(bm, segments=segments, diameter1=diameter, diameter2=diameter, depth=height, calc_uvs=True)
		elif cap_type == "FACE":
			bmesh.ops.create_cone(bm, segments=segments, diameter1=diameter, diameter2=diameter, depth=height, cap_ends=True, calc_uvs=True)
		else:
			bmesh.ops.create_cone(bm, segments=segments, diameter1=diameter, diameter2=diameter, depth=height, cap_ends=True, cap_tris=True, calc_uvs=True)
		
		# Subdivide U edges
		if u_subdivisions > 2 and cap_type == "TRI":
			u_edges = []
			
			for vert in bm.verts:
				if vert.co[0] == 0.0 and vert.co[1] == 0.0:
					u_edges += vert.link_edges
					
			
			bmesh.ops.subdivide_edges(bm, edges=u_edges, cuts=u_subdivisions-2)
		
		# Subdivide V edges
		if v_subdivisions > 2:
			v_edges = [edge for edge in bm.edges if edge_verts_distance(edge.verts, 2) > 0]
			bmesh.ops.subdivide_edges(bm, edges=v_edges, cuts=v_subdivisions-2)
		
		bm.to_mesh(context.active_object.data)
		bm.free()
		
		if use_smooth_shading:
			enable_smooth_shading(context.active_object)
		
		context.active_object.update_tag()
		
		return {'FINISHED'}


class CP_OT_create_cone(Operator):
	"""Creates a new Changable Cone"""
	bl_idname = "object.cp_ot_create_cone"
	bl_label = "Create Changable Cone"
	bl_options = {'REGISTER','UNDO'}
	
	# Properties
	segments : IntProperty(
		name = "Segments",
		default=32,
		min=3
	)
	
	u_subdivisions : IntProperty(
		name = "Segments",
		default=2,
		min=2
	)
	
	v_subdivisions : IntProperty(
		name = "Segments",
		default=2,
		min=2
	)
	
	diameter1 : FloatProperty(
		name="Diameter 1",
		default=1.0,
		unit='LENGTH'
	)
	
	diameter2 : FloatProperty(
		name="Diameter 2",
		default=0.0,
		unit='LENGTH'
	)
	
	height : FloatProperty(
		name="Height",
		default=1.0,
		unit='LENGTH'
	)
	
	cap_type : EnumProperty(
		items=[
			("NONE","No Cap","","",0),
			("TRI","Triangle Cap","","",1),
			("FACE","Face Cap","","",2),
		],
		name="Cap Type"
	)
	
	align_rot_to_cursor : BoolProperty(
		name="Align Rotation to 3D Cursor",
		default=False
	)

	@classmethod
	def poll(cls, context):
		return context.mode == "OBJECT"

	def execute(self, context):
		# Deselect all objects
		for obj in context.selected_objects:
			obj.select_set(False)
		
		# Create mesh and object
		obj = create_and_link_mesh_object(context, "ChangableCone")
		obj.location = context.scene.cursor.location.copy()
		if self.align_rot_to_cursor:
			obj.rotation_euler = context.scene.cursor.rotation_euler.copy()
		
		# Change draw options
		obj.show_wire = True
		obj.show_all_edges = True
		
		# Set created object as active
		obj.select_set(True)
		context.view_layer.objects.active = obj
		
		# Initialize Changable Primitive Settings
		settings = obj.data.changable_primitive_settings
		settings.enabled = True
		settings.type = "CONE"
		settings.x_subdivisions = self.segments
		settings.y_subdivisions = self.u_subdivisions
		settings.z_subdivisions = self.v_subdivisions
		settings.height = self.height
		settings.diameter1 = self.diameter1
		settings.diameter2 = self.diameter2
		settings.cap_type = self.cap_type
		
		# Create Mesh
		bpy.ops.object.cp_ot_update_cone()
		
		return {'FINISHED'}


class CP_OT_update_cone(Operator):
	"""Updates a changable cone"""
	bl_idname = "object.cp_ot_update_cone"
	bl_label = "Update Changable Cone"
	bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == "MESH"

	def execute(self, context):
		segments = context.active_object.data.changable_primitive_settings.x_subdivisions
		u_subdivisions = context.active_object.data.changable_primitive_settings.y_subdivisions
		v_subdivisions = context.active_object.data.changable_primitive_settings.z_subdivisions
		cap_type = context.active_object.data.changable_primitive_settings.cap_type
		height = context.active_object.data.changable_primitive_settings.height
		diameter1 = context.active_object.data.changable_primitive_settings.diameter1
		diameter2 = context.active_object.data.changable_primitive_settings.diameter2
		use_smooth_shading = context.active_object.data.changable_primitive_settings.use_smooth_shading
		
		bm = bmesh.new()
		bm.from_mesh(context.active_object.data)
		
		# Delete old mesh
		if bm.verts:
			bmesh.ops.delete(bm, geom=bm.verts, context="VERTS")
		
		# Create Cylinder
		if cap_type == "NONE":
			bmesh.ops.create_cone(bm, segments=segments, diameter1=diameter1, diameter2=diameter2, depth=height, calc_uvs=True)
		elif cap_type == "FACE":
			bmesh.ops.create_cone(bm, segments=segments, diameter1=diameter1, diameter2=diameter2, depth=height, cap_ends=True, calc_uvs=True)
		else:
			bmesh.ops.create_cone(bm, segments=segments, diameter1=diameter1, diameter2=diameter2, depth=height, cap_ends=True, cap_tris=True, calc_uvs=True)
		
		# Subdivide U edges
		if u_subdivisions > 2 and cap_type == "TRI":
			u_edges = []
			
			for vert in bm.verts:
				if vert.co[0] == 0.0 and vert.co[1] == 0.0:
					u_edges += vert.link_edges
					
			
			bmesh.ops.subdivide_edges(bm, edges=u_edges, cuts=u_subdivisions-2)
		
		# Subdivide V edges
		if v_subdivisions > 2:
			v_edges = [edge for edge in bm.edges if edge_verts_distance(edge.verts, 2) > 0]
			bmesh.ops.subdivide_edges(bm, edges=v_edges, cuts=v_subdivisions-2)
		
		bm.to_mesh(context.active_object.data)
		bm.free()
		
		if use_smooth_shading:
			enable_smooth_shading(context.active_object)
		
		context.active_object.update_tag()
		
		return {'FINISHED'}


class CP_OT_create_uvsphere(Operator):
	"""Creates a new Changable UV Sphere"""
	bl_idname = "object.cp_ot_create_uvsphere"
	bl_label = "Create Changable UV Sphere"
	bl_options = {'REGISTER','UNDO'}
	
	# Properties
	u_subdivisions : IntProperty(
		name = "Segments",
		default=32,
		min=3
	)
	
	v_subdivisions : IntProperty(
		name = "Rings",
		default=16,
		min=3
	)
	
	diameter : FloatProperty(
		name="Diameter",
		default=1.0,
		unit='LENGTH'
	)
	
	align_rot_to_cursor : BoolProperty(
		name="Align Rotation to 3D Cursor",
		default=False
	)

	@classmethod
	def poll(cls, context):
		return context.mode == "OBJECT"

	def execute(self, context):
		# Deselect all objects
		for obj in context.selected_objects:
			obj.select_set(False)
		
		# Create mesh and object
		obj = create_and_link_mesh_object(context, "ChangableUVSphere")
		obj.location = context.scene.cursor.location.copy()
		if self.align_rot_to_cursor:
			obj.rotation_euler = context.scene.cursor.rotation_euler.copy()
		
		# Change draw options
		obj.show_wire = True
		obj.show_all_edges = True
		
		# Set created object as active
		obj.select_set(True)
		context.view_layer.objects.active = obj
		
		# Initialize Changable Primitive Settings
		settings = obj.data.changable_primitive_settings
		settings.enabled = True
		settings.type = "UVSPHERE"
		settings.y_subdivisions = self.u_subdivisions
		settings.z_subdivisions = self.v_subdivisions
		settings.diameter1 = self.diameter
		
		# Create Mesh
		bpy.ops.object.cp_ot_update_uvsphere()
		
		return {'FINISHED'}


class CP_OT_update_uvsphere(Operator):
	"""Updates a changable UV Sphere"""
	bl_idname = "object.cp_ot_update_uvsphere"
	bl_label = "Update Changable UV Sphere"
	bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == "MESH"

	def execute(self, context):
		u_subdivisions = context.active_object.data.changable_primitive_settings.y_subdivisions
		v_subdivisions = context.active_object.data.changable_primitive_settings.z_subdivisions
		diameter = context.active_object.data.changable_primitive_settings.diameter1
		use_smooth_shading = context.active_object.data.changable_primitive_settings.use_smooth_shading
		
		bm = bmesh.new()
		bm.from_mesh(context.active_object.data)
		
		# Delete old mesh
		if bm.verts:
			bmesh.ops.delete(bm, geom=bm.verts, context="VERTS")
		
		# Create UV Sphere
		bmesh.ops.create_uvsphere(bm, u_segments=u_subdivisions, v_segments=v_subdivisions, diameter=diameter, calc_uvs=True)
		
		bm.to_mesh(context.active_object.data)
		bm.free()
		
		if use_smooth_shading:
			enable_smooth_shading(context.active_object)
		
		context.active_object.update_tag()
		
		return {'FINISHED'}


class CP_OT_create_icosphere(Operator):
	"""Creates a new Changable Icosphere"""
	bl_idname = "object.cp_ot_create_icosphere"
	bl_label = "Create Changable Icosphere"
	bl_options = {'REGISTER','UNDO'}
	
	# Properties
	subdivisions : IntProperty(
		name = "Subdivisions",
		default=2,
		min=1
	)
	
	diameter : FloatProperty(
		name="Diameter",
		default=1.0,
		unit='LENGTH'
	)
	
	align_rot_to_cursor : BoolProperty(
		name="Align Rotation to 3D Cursor",
		default=False
	)

	@classmethod
	def poll(cls, context):
		return context.mode == "OBJECT"

	def execute(self, context):
		# Deselect all objects
		for obj in context.selected_objects:
			obj.select_set(False)
		
		# Create mesh and object
		obj = create_and_link_mesh_object(context, "ChangableIcosphere")
		obj.location = context.scene.cursor.location.copy()
		if self.align_rot_to_cursor:
			obj.rotation_euler = context.scene.cursor.rotation_euler.copy()
		
		# Change draw options
		obj.show_wire = True
		obj.show_all_edges = True
		
		# Set created object as active
		obj.select_set(True)
		context.view_layer.objects.active = obj
		
		# Initialize Changable Primitive Settings
		settings = obj.data.changable_primitive_settings
		settings.enabled = True
		settings.type = "ICOSPHERE"
		settings.x_subdivisions = self.subdivisions
		settings.diameter1 = self.diameter
		
		# Create Mesh
		bpy.ops.object.cp_ot_update_icosphere()
		
		return {'FINISHED'}


class CP_OT_update_icosphere(Operator):
	"""Updates a changable Icosphere"""
	bl_idname = "object.cp_ot_update_icosphere"
	bl_label = "Update Changable Icosphere"
	bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == "MESH"

	def execute(self, context):
		subdivisions = context.active_object.data.changable_primitive_settings.x_subdivisions
		diameter = context.active_object.data.changable_primitive_settings.diameter1
		use_smooth_shading = context.active_object.data.changable_primitive_settings.use_smooth_shading
		
		bm = bmesh.new()
		bm.from_mesh(context.active_object.data)
		
		# Delete old mesh
		if bm.verts:
			bmesh.ops.delete(bm, geom=bm.verts, context="VERTS")
		
		# Create UV Sphere
		bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, diameter=diameter, calc_uvs=True)
		
		bm.to_mesh(context.active_object.data)
		bm.free()
		
		if use_smooth_shading:
			enable_smooth_shading(context.active_object)
		
		context.active_object.update_tag()
		
		return {'FINISHED'}


class CP_OT_create_torus(Operator):
	"""Creates a new Changable Torus"""
	bl_idname = "object.cp_ot_create_torus"
	bl_label = "Create Changable Torus"
	bl_options = {'REGISTER','UNDO'}
	
	# Properties
	major_segments : IntProperty(
		name = "Major Segments",
		default=48,
		min=3
	)
	
	minor_segments : IntProperty(
		name = "Minor Segments",
		default=12,
		min=3
	)
	
	major_radius : FloatProperty(
		name="Major Radius",
		default=2.0,
		unit='LENGTH'
	)
	
	minor_radius : FloatProperty(
		name="Minor Radius",
		default=0.5,
		unit='LENGTH'
	)
	
	align_rot_to_cursor : BoolProperty(
		name="Align Rotation to 3D Cursor",
		default=False
	)

	@classmethod
	def poll(cls, context):
		return context.mode == "OBJECT"

	def execute(self, context):
		# Deselect all objects
		for obj in context.selected_objects:
			obj.select_set(False)
		
		# Create mesh and object
		obj = create_and_link_mesh_object(context, "ChangableTorus")
		obj.location = context.scene.cursor.location.copy()
		if self.align_rot_to_cursor:
			obj.rotation_euler = context.scene.cursor.rotation_euler.copy()
		
		# Change draw options
		obj.show_wire = True
		obj.show_all_edges = True
		
		# Set created object as active
		obj.select_set(True)
		context.view_layer.objects.active = obj
		
		# Initialize Changable Primitive Settings
		settings = obj.data.changable_primitive_settings
		settings.enabled = True
		settings.type = "TORUS"
		settings.x_subdivisions = self.major_segments
		settings.y_subdivisions = self.minor_segments
		settings.diameter1 = self.major_radius
		settings.diameter2 = self.minor_radius
		
		# Create Mesh
		bpy.ops.object.cp_ot_update_torus()
		
		return {'FINISHED'}


class CP_OT_update_torus(Operator):
	"""Updates a changable Torus"""
	bl_idname = "object.cp_ot_update_torus"
	bl_label = "Update Changable Torus"
	bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == "MESH"

	def execute(self, context):
		major_segments = context.active_object.data.changable_primitive_settings.x_subdivisions
		minor_segments = context.active_object.data.changable_primitive_settings.y_subdivisions
		major_radius = context.active_object.data.changable_primitive_settings.diameter1
		minor_radius = context.active_object.data.changable_primitive_settings.diameter2
		use_smooth_shading = context.active_object.data.changable_primitive_settings.use_smooth_shading
		
		bm = bmesh.new()
		bm.from_mesh(context.active_object.data)
		
		# Delete old mesh
		if bm.verts:
			bmesh.ops.delete(bm, geom=bm.verts, context="VERTS")
		
		# Create Torus
		bmesh.ops.create_circle(bm, segments=minor_segments, radius=minor_radius, calc_uvs=False)
		bmesh.ops.rotate(bm, cent=(0,0,0), verts=bm.verts, matrix=Matrix.Rotation(radians(90), 4, 'X'))
		
		translate_x = major_radius
		bmesh.ops.translate(bm, verts=bm.verts, vec=(translate_x,0,0))
		
		bmesh.ops.spin(bm, geom=bm.edges, cent=(0,0,0), axis=(0,0,1), angle=radians(360), steps=major_segments)
		
		double_verts = tuple(vert for vert in bm.verts if vert.co[1] < 0.00001)
		
		bmesh.ops.remove_doubles(bm, verts=double_verts, dist=0.0001)
		
		bm.to_mesh(context.active_object.data)
		bm.free()
		
		if use_smooth_shading:
			enable_smooth_shading(context.active_object)
		
		context.active_object.update_tag()
		
		return {'FINISHED'}


class CP_OT_make_permenant(Operator):
	"""Makes a Changable Primitive's current shape permanent. (Not able to be updated via UI anymore)"""
	bl_idname = "object.cp_ot_make_permanent"
	bl_label = "Make Changable Primitive Permanent"
	bl_options = {'REGISTER','UNDO'}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == "MESH"

	def execute(self, context):
		context.active_object.data.changable_primitive_settings.enabled = False
		
		return {'FINISHED'}

## Shared UI Functions

def changable_primitive_settings_shared_draw(self, context):
	layout = self.layout
	layout.use_property_split = True

	obj = context.object
	
	# TODO: Change icons to the right mesh type
	
	if obj.data.changable_primitive_settings.type == "PLANE":
		layout.label(text="Plane", icon="MESH_PLANE")
		
		layout.prop(obj.data.changable_primitive_settings, "x_subdivisions")
		layout.prop(obj.data.changable_primitive_settings, "y_subdivisions")
		layout.prop(obj.data.changable_primitive_settings, "height", text="Size")
		layout.prop(obj.data.changable_primitive_settings, "use_smooth_shading")
		layout.operator(CP_OT_make_permenant.bl_idname, text="Make Permenant")
	elif obj.data.changable_primitive_settings.type == "CUBE":
		layout.label(text="Cube", icon="MESH_PLANE")
		
		layout.prop(obj.data.changable_primitive_settings, "x_subdivisions")
		layout.prop(obj.data.changable_primitive_settings, "y_subdivisions")
		layout.prop(obj.data.changable_primitive_settings, "z_subdivisions")
		layout.prop(obj.data.changable_primitive_settings, "height", text="Size")
		layout.prop(obj.data.changable_primitive_settings, "use_smooth_shading")
		layout.operator(CP_OT_make_permenant.bl_idname, text="Make Permenant")
	elif obj.data.changable_primitive_settings.type == "CIRCLE":
		layout.label(text="Circle", icon="MESH_PLANE")
		
		layout.prop(obj.data.changable_primitive_settings, "x_subdivisions", text="Segments")
		layout.prop(obj.data.changable_primitive_settings, "y_subdivisions", text="U Subdivisions")
		layout.prop(obj.data.changable_primitive_settings, "cap_type")
		layout.prop(obj.data.changable_primitive_settings, "radius")
		layout.prop(obj.data.changable_primitive_settings, "use_smooth_shading")
		layout.operator(CP_OT_make_permenant.bl_idname, text="Make Permenant")
	elif obj.data.changable_primitive_settings.type == "CYLINDER":
		layout.label(text="Cylinder", icon="MESH_PLANE")
		
		layout.prop(obj.data.changable_primitive_settings, "x_subdivisions", text="Segments")
		layout.prop(obj.data.changable_primitive_settings, "y_subdivisions", text="U Subdivisions")
		layout.prop(obj.data.changable_primitive_settings, "z_subdivisions", text="V Subdivisions")
		layout.prop(obj.data.changable_primitive_settings, "cap_type")
		layout.prop(obj.data.changable_primitive_settings, "diameter1", text="Diameter")
		layout.prop(obj.data.changable_primitive_settings, "height")
		layout.prop(obj.data.changable_primitive_settings, "use_smooth_shading")
		layout.operator(CP_OT_make_permenant.bl_idname, text="Make Permenant")
	elif obj.data.changable_primitive_settings.type == "CONE":
		layout.label(text="Cone", icon="MESH_PLANE")
		
		layout.prop(obj.data.changable_primitive_settings, "x_subdivisions", text="Segments")
		layout.prop(obj.data.changable_primitive_settings, "y_subdivisions", text="U Subdivisions")
		layout.prop(obj.data.changable_primitive_settings, "z_subdivisions", text="V Subdivisions")
		layout.prop(obj.data.changable_primitive_settings, "cap_type")
		layout.prop(obj.data.changable_primitive_settings, "diameter1")
		layout.prop(obj.data.changable_primitive_settings, "diameter2")
		layout.prop(obj.data.changable_primitive_settings, "height")
		layout.prop(obj.data.changable_primitive_settings, "use_smooth_shading")
		layout.operator(CP_OT_make_permenant.bl_idname, text="Make Permenant")
	elif obj.data.changable_primitive_settings.type == "UVSPHERE":
		layout.label(text="UV Sphere", icon="MESH_PLANE")
		
		layout.prop(obj.data.changable_primitive_settings, "y_subdivisions", text="Segments")
		layout.prop(obj.data.changable_primitive_settings, "z_subdivisions", text="Rings")
		layout.prop(obj.data.changable_primitive_settings, "diameter1", text="Diameter")
		layout.prop(obj.data.changable_primitive_settings, "use_smooth_shading")
		layout.operator(CP_OT_make_permenant.bl_idname, text="Make Permenant")
	elif obj.data.changable_primitive_settings.type == "ICOSPHERE":
		layout.label(text="Icosphere", icon="MESH_PLANE")
		
		layout.prop(obj.data.changable_primitive_settings, "x_subdivisions", text="Subdivisions")
		layout.prop(obj.data.changable_primitive_settings, "diameter1", text="Diameter")
		layout.prop(obj.data.changable_primitive_settings, "use_smooth_shading")
		layout.operator(CP_OT_make_permenant.bl_idname, text="Make Permenant")
	elif obj.data.changable_primitive_settings.type == "TORUS":
		layout.label(text="Torus", icon="MESH_PLANE")
		
		layout.prop(obj.data.changable_primitive_settings, "x_subdivisions", text="Major Segments")
		layout.prop(obj.data.changable_primitive_settings, "y_subdivisions", text="Minor Segments")
		layout.prop(obj.data.changable_primitive_settings, "diameter1", text="Major Radius")
		layout.prop(obj.data.changable_primitive_settings, "diameter2", text="Minor Radius")
		layout.prop(obj.data.changable_primitive_settings, "use_smooth_shading")
		layout.operator(CP_OT_make_permenant.bl_idname, text="Make Permenant")
	else:
		layout.label(text="This one hasn't been implemented in Panel yet! " + obj.data.changable_primitive_settings.type)

## UI

class CP_PT_changable_primitive_settings(Panel):
	"""Creates a Panel in the Mesh properties window"""
	bl_label = "Changable Primitive Settings"
	bl_idname = "MESH_PT_changable_primitive_settings"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "data"
	
	@classmethod
	def poll(self, context):
		return context.mode != "EDIT_MESH" and context.mesh and context.mesh.changable_primitive_settings.enabled
	
	def draw(self, context):
		changable_primitive_settings_shared_draw(self, context)


class CP_PT_changable_primitive_settings_view3d_sidebar(Panel):
	bl_idname = "CP_PT_changable_primitive_settings_view3d_sidebar"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Item"
	bl_label = "Changable Primitive Settings"
	
	@classmethod
	def poll(cls, context):
		return context.mode != "EDIT_MESH" and context.active_object and context.active_object.type == "MESH" and context.active_object.data.changable_primitive_settings.enabled
	
	def draw(self, context):
		changable_primitive_settings_shared_draw(self, context)


class CP_MT_changable_primitives_base(Menu):
	bl_label = "Changable Primitives"

	def draw(self, _context):
		layout = self.layout
		
		# TODO: Set icons to right mesh type
		layout.operator(CP_OT_create_plane.bl_idname, text="Plane")
		layout.operator(CP_OT_create_cube.bl_idname, text="Cube")
		layout.operator(CP_OT_create_circle.bl_idname, text="Circle")
		layout.operator(CP_OT_create_cylinder.bl_idname, text="Cylinder")
		layout.operator(CP_OT_create_cone.bl_idname, text="Cone")
		layout.operator(CP_OT_create_uvsphere.bl_idname, text="UV Sphere")
		layout.operator(CP_OT_create_icosphere.bl_idname, text="Icosphere")
		layout.operator(CP_OT_create_torus.bl_idname, text="Torus")


## Append to UI Functions

def add_changable_primitives_menu(self, context):
	self.layout.menu("CP_MT_changable_primitives_base", icon="SPHERE")

## Register

classes = (
	CP_changable_primitive_settings,
	CP_OT_create_plane,
	CP_OT_update_plane,
	CP_OT_create_cube,
	CP_OT_update_cube,
	CP_OT_create_circle,
	CP_OT_update_circle,
	CP_OT_create_cylinder,
	CP_OT_update_cylinder,
	CP_OT_create_cone,
	CP_OT_update_cone,
	CP_OT_create_uvsphere,
	CP_OT_update_uvsphere,
	CP_OT_create_icosphere,
	CP_OT_update_icosphere,
	CP_OT_create_torus,
	CP_OT_update_torus,
	CP_OT_make_permenant,
	CP_PT_changable_primitive_settings,
	CP_PT_changable_primitive_settings_view3d_sidebar,
	CP_MT_changable_primitives_base
)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	
	bpy.types.Mesh.changable_primitive_settings = bpy.props.PointerProperty(type=CP_changable_primitive_settings)
	
	bpy.types.VIEW3D_MT_add.append(add_changable_primitives_menu)

def unregister():
	bpy.types.VIEW3D_MT_add.remove(add_changable_primitives_menu)
	
	del bpy.types.Mesh.changable_primitive_settings
	
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

if __name__ == "__main__":
	register()
