# Blender Tools for Digimon Story: Cyber Sleuth
This repository provides a work-in-progress addon for Blender 2.8 that can (to some degree) import model files from the PC version of Digimon Story: Cyber Sleuth. It provides new options in File > Import and File > Export named "DSCS Model", which should be pointed towards 'name' files in the game data. The file format is not yet fully decoded, bugs remain, and there are some Blender issues yet to be understood.

## Preparation
1. Get some files to work with by unpacking the game files with [DSCSTools](https://github.com/SydMontague/DSCSTools), following the instructions in the readme. Alternatively, install [SimpleDSCSModManager](https://github.com/Pherakki/SimpleDSCSModManager) and click 'Extract DSDB'.
2. Install `Blender Tools for DSCS` as a zip archive like any other Blender addon:
    * In Blender, open Edit > Preferences
    * Click 'Add-ons' on the left-hand pane of the pop-up
    * Click 'Install' at the top of the right-hand pane
    * Navigate to the location of the `Blender Tools for DSCS` zip archive, select it, and click 'Install Add-on' in the file browser pop-up.

## Import Usage
1. The model files are split into name, skel, and geom files. Currently, these must all be in the same directory in order for the import to be successful.
2. Textures are expected to be located in a directory named 'images' in the same directory as the name, skel, and geom files.
3. Open Blender, navigate to File > Import > Import DSCS and open the appropriate name, skel, or geom file (all three will currently be simultaneously imported).
4. If you point the import function towards the unpacked game files, all the files will be already in a location understandable by the import script.

## Export Usage
1. Once you are done editing, pack files into the blend by ensuring File > External Data > Automatically pack into .blend is checked before saving the file. **The textures are saved as temporary files so they will be deleted when you exit Blender unless you do this!**
2. If you have saved the file as a .blend, click File > External Data > Unpack all into files to extract any textures you may want to edit outside Blender.
3. To export, select any part of the model in object mode and navigate to File > Export > Export DSCS.

## Installing your edited models
1. Currently, only model replacement is available. Give your files the same name as those they are intended to replace (e.g. to replace the male main character in Cyber Sleuth, name your files pc001.name, pc001.skel, pc001.geom).
2. Put the files into the DSDBA archive, which you need to extract with [DSCSTools](https://github.com/SydMontague/DSCSTools).
3. Put any replaced textures in DSDBA/images
4. Re-pack the DSDBA archive with [DSCSTools](https://github.com/SydMontague/DSCSTools).
5. Overwrite you game's DSDBA archive you your edited one (as always, make a backup!).
4. **You *might* also have some success using [SimpleDSCSModManager](https://github.com/Pherakki/SimpleDSCSModManager) to do this automatically.**

## Potential fixes for common "bugs"
1. Some materials fail to show up in-game. **This is not a `Blender Tools for DSCS` Bug. You can demonstrate this by moving the vanilla files for pc002 into the DSDBA archive.** You may be able to fix this by locating the offending material in a Blender 'Properties' window, scrolling down to the material's 'Custom Properties', and changing 'unknown_0x11' to 0. If it is already 0, this method will not work.
2. If your mesh has a few highly distorted polygons that converge at the centre of your current room, ensure that none of your meshes have empty or unnecessary vertex groups. Delete any the are not needed.

## Some Known Bugs and Limitations
1. **Currently you can only use, mix, and edit models that are ripped from the game using `Blender Tools for DSCS`.** Adding custom meshes and materials will not work, because the ones loaded from the game files contain unknown and undecoded data that will not be present in any new meshes or materials initialised in Blender. Editing meshes and transferring meshes between models *should* be fine, but there will certainly be some issues somewhere at this early stage..!
2. **Blender appears to re-calculate vertex normals incorrectly for these models.** If you edit meshes, you may find that they appear blocky. I'm looking into a writing a custom calculator to alleviate this issue.
3. There are some (minor?) lighting issues with models put into the DSDBA archive (this may be another "vanilla bug").
4. Material names are not yet those found within the files.
5. There are five types of data attached to vertices not currently understood.
6. Materials need a lot of work.
7. Please use the skeleton of the model you are replacing if you want animations to work correctly..!

## Future Plans
1. Finish decoding the remaining unknown bytes
3. Add readers for anim files

## How can I help?
Most of the remaining unknown data either breaks the files or appears to have no effect if it is changed. There are a lot of files that can be checked for visual changes if these data are tweaked; but I am only a single person and it will take time to figure out what the rest of the data does. However, a lot of this data is loaded into Blender by `Blender Tools for DSCS` and is editable. These data are stored under the 'Custom Properties' of a a parent object, armature, mesh, or material. At the moment I don't have a clear experimentation plan set out. However, in the near future, I will provide guidance on how you can tweak the data present in the models to see what effect it has in-game. If you discover anything, it will help speed up development significantly!

## Contact
e-mail: pherakki@gmail.com

## Notes
1. I have next to no experience with Blender or its API. The import script is a bit of a mess which will hopefully get cleaner over time.
2. Images are stored in a 'img' format, which is secretly a DDS (BC2; Linear DXT3 codec) **with mipmaps**. The game will not enjoy the experience of trying to load anything else and will present you with blank textures in retaliation. Save your edited (or new) textures as a BC2 DDS and rename the extension (I have not yet checked if renaming the extension is necessary).

## Acknowledgements
This project would not have even got off the ground without the [DSCSTools program](https://github.com/SydMontague/DSCSTools) by [SydMontague](https://github.com/SydMontague). Also, the [CSGeom program](https://github.com/xdanieldzd/CSGeom) by [xdanieldzd](https://github.com/xdanieldzd) was very useful to compare against for the geom files, even though the file format has changed somewhat for the PC release.
