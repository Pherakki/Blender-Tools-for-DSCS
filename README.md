# Blender Tools for Digimon Story: Cyber Sleuth
This repository provides a work-in-progress addon for Blender 2.8 that can (to some degree) import model files from the PC version of Digimon Story: Cyber Sleuth. It provides new options in `File > Import` and `File > Export` named "DSCS Model", which should be pointed towards 'name' files in the game data. The file format is mostly understood; but some bugs remain and there are some Blender issues yet to be understood. There is also experimental support for the PS4 version.

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
4. There are three import options:
    * "Modelling" will import the model in the bind pose, with the base animation loaded on the model to put it into the rest pose. This mode is suitable for editing the base model and skeleton, because it does not import the animations (which may take a few minutes for some models).
    * "Animation" will import the model in the rest pose and load all animations. This mode is suitable for editing animations, because the model is in a position where any animation will be correctly applied to to the rest pose without any interference from the base animation.
    * 'QA' or 'Quality Assurance' mode is for checking the model works as intended before export, or for modelling and animating all in one go. The model is loaded in the bind pose, with the base animation loaded on the model to put it into the rest pose. All animations are also loaded. The combined animations can be previewed in the NLA editor, by making sure the base animation and the selected overlay animation are both unmuted (ticked). By default, the NLA strips are set to the appropriate mode such that they combine in the way DSCS combines them.

Note: If you point the import function towards the unpacked game files, all the files will be already in a location understandable by the import script.

## Export Usage
1. To export, **select** any part of the model in **object mode** and navigate to `File > Export > Export DSCS`.
2. There are three import options:
    * "Modelling" will export the model and base animation only.
    * "Animation" will export animations only.
    * 'QA' will export the model and any animations.

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
   
## Some Known Bugs and Limitations
1. There are some issues with vertex normal import and export.
2. Some exported animations may crash the game.

## Future Plans
1. Finish the custom-channel animation feature.
2. Readers for remaining filetypes: DETR, NAVI, NOTE, PHYS, SPRK
3. [An external program that can assign shaders to models, currently WIP.](https://github.com/Pherakki/DSCSModelDataEditor)

## Contact
e-mail: pherakki@gmail.com

reddit: [u/Pherakki](https://www.reddit.com/user/Pherakki)

## Notes
1. Images are stored in a 'img' format, which is a DDS **with mipmaps** in disguise. 

## Acknowledgements
This project would not have even got off the ground without the [DSCSTools program](https://github.com/SydMontague/DSCSTools) by [SydMontague](https://github.com/SydMontague). Also, the [CSGeom program](https://github.com/xdanieldzd/CSGeom) by [xdanieldzd](https://github.com/xdanieldzd) was very useful to compare against for the geom files, even though the file format has changed somewhat for the PC release.
