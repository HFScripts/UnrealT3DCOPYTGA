import bpy
import os
import re

def parse_copy_file(copy_file_path):
    parameters = {}
    base_path = os.path.dirname(copy_file_path).replace("\\", "/")
    with open(copy_file_path, 'r', encoding='ansi') as f:
        for line in f:
            print(f"Processing line: {line}")
            if "TextureParameterValues" in line:
                texture_param_line = line.strip()
                name_start_index = texture_param_line.find('Name="')
                if name_start_index >= 0:
                    name = texture_param_line[name_start_index + 6:].split('"')[0]
                    unreal_texture_path_index = texture_param_line.find('Texture2D\'"')
                    if unreal_texture_path_index >= 0:
                        unreal_texture_path = texture_param_line[unreal_texture_path_index + 11:].split('"')[0]
                        texture_name = os.path.splitext(unreal_texture_path.split('/')[-1])[0] + ".tga"
                        texture_path = os.path.join(base_path, texture_name).replace("\\", "/")
                        parameters[name] = texture_path
                    else:
                        print(f"Unreal texture path not found in line: {texture_param_line}")
                else:
                    print(f"Parameter name not found in line: {texture_param_line}")
            elif "ScalarParameterValues" in line or "VectorParameterValues" in line:
                continue
            else:
                try:
                    name_start_index = line.find('Name="')
                    if name_start_index >= 0:
                        name = line[name_start_index + 6:].split('"')[0]
                        value_start_index = line.find('ParameterValue=')
                        if value_start_index >= 0:
                            value = line[value_start_index + 15:].split(',')[0]
                            parameters[name] = float(value)
                        else:
                            print(f"Value not found in line: {line}")
                    else:
                        print(f"Parameter name not found in line: {line}")
                except (ValueError, IndexError) as e:
                    print(f"Error processing line: {line}")
                    print(f"Error message: {str(e)}")
                
    return parameters


def create_shader_nodes(material, texture_params):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Create shader nodes
    principled_node = nodes.new('ShaderNodeBsdfPrincipled')
    principled_node.location = (0, 0)

    output_node = nodes.new('ShaderNodeOutputMaterial')
    output_node.location = (400, 0)

    for name, texture_path in texture_params.items():
        if name in ["Color", "Emissive", "Normal", "ORM", "BaseColor+DetailMask", "SRAT Map", "Baked NormalMap", "Detail Normal Map"]:
            texture_node = nodes.new('ShaderNodeTexImage')
            texture_node.image = bpy.data.images.load(texture_path)
            texture_node.location = (-400, 200 * len(texture_params))
            texture_node.label = name

            if name == "Color" or name == "BaseColor+DetailMask":
                links.new(texture_node.outputs['Color'], principled_node.inputs['Base Color'])
            elif name == "Emissive":
                links.new(texture_node.outputs['Color'], principled_node.inputs['Emission'])
            elif name == "Normal" or name == "Baked NormalMap" or name == "Detail Normal Map":
                normal_map_node = nodes.new('ShaderNodeNormalMap')
                normal_map_node.location = (-200, 200 * len(texture_params))
                links.new(texture_node.outputs['Color'], normal_map_node.inputs['Color'])
                links.new(normal_map_node.outputs['Normal'], principled_node.inputs['Normal'])
            elif name == "ORM" or name == "SRAT Map":
                links.new(texture_node.outputs['Color'], principled_node.inputs['Specular'])
                links.new(texture_node.outputs['Alpha'], principled_node.inputs['Roughness'])

    links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])

# Replace the path to the folder containing the .COPY files
copy_files_folder = "C:/Users/MrRobot/Desktop/DragonGirl/Blender/"

# Iterate through all objects in the scene
for obj in bpy.context.scene.objects:
    # Check if the object has a mesh
    if obj.type == 'MESH':
        # Iterate through the object's materials
        for slot in obj.material_slots:
            material = slot.material
            if material:
                # Check if there is a .COPY file with the same name as the material
                material_name = material.name
                copy_file_name = f"{material_name}.COPY"
                copy_file_path = os.path.join(copy_files_folder, copy_file_name)

                if os.path.isfile(copy_file_path):
                    texture_params = parse_copy_file(copy_file_path)
                    create_shader_nodes(material, texture_params)
                else:
                    print(f"No .COPY file found for material '{material_name}'")
            else:
                print(f"Material not found in object '{obj.name}'")
