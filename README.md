# add_mesh_changable_primitives
Blender Addon that creates primitives that can be changed after they are created and moved/scaled/etc.

## What
Creates Changable Primitives which are primitives that can be changed even after they are moved, rotated, scaled, etc.  
Great for starting rough models.  
### Features
* Currently supports mesh types  
  * Plane
  * Cube
  * Circle
  * Cylinder 
  * Cone  
  * UV Sphere  
  * Icosphere  
  * Torus  
* Supports Linked Objects  
Changable Primitives duplicated with Linked Duplicate will share properties.
* Supports Modifiers  
You can add modifiers to Changable Primitives to change their shape while still being able to change their properties.

## Installation  
### Requirements  
Works on Windows, Mac, and Linux.  
Meant for Blender 2.8 Beta
### How to Install  
Download the repository, Clone or Download > Download ZIP (put it in a place where you can easily find it, like your desktop)  
In Blender's settings, go to the addons tab  
At the bottom, click "Install from File"  
Find where you put the ZIP file, select it, and click "Install from File" 

## Using
You can add a Changable Primitive from...
* 3D View > Add Menu > Changable Primtives
* 3D View > Operator Search > Create \*Changable Primitive name\*  

After it is created, you can find the Changable Primitive's properties in...  
* Properties window > Mesh Data tab > Changable Primitive Settings  
* 3D View > Sidebar > Changable Primitive Settings  
## Notes
Not feature complete yet.  

Do not edit the Changable Primtive's mesh in Edit mode.  
Any changes made to the mesh in Edit mode will be lost when any of the Changable Primitive's properties is changed.  
If you need to make changes to the shape while being able to customize the properties, use a Lattice.

Sometimes entering Edit mode after creating a Changable Primitive will cause odd shading to happen.  
Leaving and entering Edit mode again usually corrects the shading.  
