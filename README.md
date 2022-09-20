# Blender Tools for Digimon Story: Cyber Sleuth
This repository provides a work-in-progress addon for Blender 2.8 that can (to some degree) import model files from the PC version of Digimon Story: Cyber Sleuth. It provides new options in `File > Import` and `File > Export` named "DSCS Model", which should be pointed towards 'name' files in the game data. The file format is mostly understood; but some bugs remain and there are some Blender issues yet to be understood. There is also experimental support for the PS4 version and for Megido72.

Refer to the [Wiki](https://github.com/Pherakki/Blender-Tools-for-DSCS/wiki) for guidance on using the tools to export new models.

The tools appear to be valid for Blender versions 2.80 - 2.91. Some compatibility issues have been reported with 2.93 and versions >3.0.

Progress reports are hosted in the [discussions](https://github.com/Pherakki/Blender-Tools-for-DSCS/discussions/1) and documentation is in-progress in the [wiki](https://github.com/Pherakki/Blender-Tools-for-DSCS/wiki).

## Preparation
1. Get some files to work with by unpacking the game files with [DSCSTools](https://github.com/SydMontague/DSCSTools), following the instructions in the readme. Alternatively, install [SimpleDSCSModManager](https://github.com/Pherakki/SimpleDSCSModManager) and click 'Extract DSDB'.
2. If you have cloned the `Blender Tools for DSCS` code from the repository, unpack the zip file and put the contents into a folder. Then, re-pack the folder into a zip archive.
_i.e._ the zip structure starts off looking like
```
-BlenderIO
-CollatedData
-CustomExceptions
-etc.
```
and you should repackage it to look like
```
-some_folder_name
    |-BlenderIO
    |-CollatedData
    |-CustomExceptions
    |-...
```
If you are instead downloading a release version, skip ahead to step 3.

3. Install the zip archive for `Blender Tools for DSCS` like any other Blender addon:
    * In Blender, open `Edit > Preferences`
    * Click 'Add-ons' on the left-hand pane of the pop-up
    * Click 'Install' at the top of the right-hand pane
    * Navigate to the location of the `Blender Tools for DSCS` zip archive in the file browser pop-up, select it, and click 'Install Add-on'.
    * Tick the box next to the newly-added add-on in the Blender add-ons window to activate the plugin. You should now have the options to Import and Export DSCS models.
    
    If the addon does not appear, you may need to re-pack the files into a folder within the zip archive before installation. Check the "Potential Fixes for Common 'Bugs'" section for further guidance. 

## Import Usage
1. The model files are split into name, skel, and geom files. These must all be in the same directory in order for the import to be successful.
2. Textures are expected to be located in a directory named 'images' in the same directory as the name, skel, and geom files.
3. Open Blender, navigate to `File > Import > Import DSCS` and open the appropriate name, skel, or geom file (all three will currently be simultaneously imported). By default, only the name files are present in the search results.
4. Import animations alongside the model by ticking "Import Animations" box in the importer. This will import all heuristically-identified animation files for the model.

Note: If you point the import function towards the unpacked game files, all the files will be already in a location understandable by the import script.

## Export Usage
1. To export, **select** any part of the model in **object mode** and navigate to `File > Export > Export DSCS`.
2. Tick the "Export Animations" box if you want to export animations. Note that the animations will be identified by finding NLA Tracks associated with the Armature of your model, and each track must contain a single NLA strip.
3. The tools will, by default, attempt to generate a shader name for your meshes that will allow them to render properly in-game by identifying the number of vertex groups used by each mesh. This may generate a name for a shader that does not exist within the game, and you will have to create this shader yourself in order for the affected mesh(es) to display. To turn off this behaviour, switch the "Fix Vertex Weights" option to "Never". This may cause rendering issues with the model.

## Putting models into the game files
[SimpleDSCSModManager](https://github.com/Pherakki/SimpleDSCSModManager) makes the installation of exported models easy, as well as many other game edits. Follow the guide for making mods in the SimpleDSCSModManager user guide, located in the SimpleDSCSModManager documentation folder. For successful install, your mod requires:
1. The name, skel, and geom files in the "modfiles" folder of your mod. Both the skel and geom **must** be present or the game will crash.
2. Any animations also go in the "modfiles" folder. Optional if you are replacing a model. For the successful install of new models, follow the naming convention of another model in the same category (_e.g._ chr, mob, pc, _etc._).
3. Images must be exported in a DDS format with the extension renamed to ".img". These go into an "images" folder within the "modfiles" folder.
4. Any shaders your model uses must be manually copied into a "shaders" folder from the game files. To check which shaders your model uses, look in the custom properties of each material and locate the "shader_hex" property, which contains the filename of the shader to use. If this property is not present, the material will be automatically assigned a basic shader.
5. For **new** models to show up, they'll need to be placed appropriately into the game world. The relevant MBE edits to do this are beyond the scope of these tools, and presently must be done manually. There is also a large variety of different edits that could be made, so including an exhaustive guide here is not practical. Once a tool to write these edits easily/automatically is released, it will be linked here. **Models that just replace pre-existing models do not require MBE edits**.
6. Advanced mod-writing rules, such as those for including a CYMIS installer with the mod to _e.g._ provide optional textures, take precedence over these guidelines but follow similar logic. Refer to the SimpleDSCSModManager documentation.

## Potential fixes for common "bugs"
1. If the import/export options do not appear, navigate to your Blender addons folder. On Windows, this folder is located in `<drive>\Users\<user>\AppData\Roaming\Blender Foundation\Blender\<version>\scripts\addons`, where quantities between `<>` are specific to your computer. You can navigate to `<user>\AppData\Roaming\` by typing `%appdata%` into the file address bar in File Explorer. Ensure that the addon code is in a folder, perhaps named something like "Blender-Tools-For-DSCS_master", and not in a bunch of folders like "FileReaders", "CollatedData" etc. If the code is not contained in a single folder in this manner, create a new folder and drag + drop all the code from this addon into the folder. The contents of this folder should now contain files and folders in the GitHub repository. Restart Blender, and re-load the addon.

## Future Plans
1. Readers for remaining filetypes: DETR, NAVI, NOTE, PHYS, SPRK
2. [An external program that can assign shaders to models.](https://github.com/Pherakki/DSCSModelDataEditor) **Currently WIP** but under heavy development; the repository may not be kept up-to-date during this period.

## Contact
e-mail: pherakki@gmail.com

reddit: [u/Pherakki](https://www.reddit.com/user/Pherakki)

## Notes
1. Images are stored in an 'img' format, which is a DDS **with mipmaps** in disguise. The main compressions used are DXT1, DXT3, and DXT5, with some textures uncompressed.

## Acknowledgements
This project would not have even got off the ground without the [DSCSTools program](https://github.com/SydMontague/DSCSTools) by [SydMontague](https://github.com/SydMontague). Also, the [CSGeom program](https://github.com/xdanieldzd/CSGeom) by [xdanieldzd](https://github.com/xdanieldzd) was very useful to compare against for the geom files, even though the file format has changed somewhat for the PC release.
