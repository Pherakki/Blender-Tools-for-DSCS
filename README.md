# Blender Tools for Digimon Story: Cyber Sleuth
This repository provides a work-in-progress addon for Blender 2.8 that can (to some degree) import model files from the PC version of Digimon Story: Cyber Sleuth. It provides new options in File > Import and File > Export named "DSCS Model", which should be pointed towards 'name' files in the game data. The file format is not yet fully decoded, bugs remain, and there are some Blender issues yet to be understood. There is also experimental support for the PS4 version.

Progress reports are hosted in the [discussions](https://github.com/Pherakki/Blender-Tools-for-DSCS/discussions/1) and documentation is in-progress in the [wiki](https://github.com/Pherakki/Blender-Tools-for-DSCS/wiki).

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
3. Shaders are expected to be located in a directory named 'shaders' in the same directory as the name, skel, and geom files.
4. Open Blender, navigate to File > Import > Import DSCS and open the appropriate name, skel, or geom file (all three will currently be simultaneously imported).
5. If you point the import function towards the unpacked game files, all the files will be already in a location understandable by the import script.

## Export Usage
1. To export, select any part of the model in **object mode** and navigate to File > Export > Export DSCS.

Note: The required shaders will be copied into the output folder along with your saved data and any required textures.

## Saving for later editting, or extracting textures
If you want to save an imported model as a .blend file, or if you want to extract the textures for external programs to use:
1. Pack files into the blend by ensuring File > External Data > Automatically pack into .blend is checked before saving the file. **The textures are saved as temporary files so they will be deleted when you exit Blender unless you do this!**
2. If you have saved the file as a .blend, click File > External Data > Unpack all into files to extract any textures you may want to edit outside Blender.

## Installing your editted models
1. Currently, only model replacement is available. Give your files the same name as those they are intended to replace (e.g. to replace the male main character in Cyber Sleuth, name your files pc001.name, pc001.skel, pc001.geom).
2. Put the files into the DSDBP archive, which you need to extract with [DSCSTools](https://github.com/SydMontague/DSCSTools).
3. Put any replaced textures in DSDBP/images
4. Put any exported shaders in DSDBP/shaders
5. Re-pack the DSDBP archive with [DSCSTools](https://github.com/SydMontague/DSCSTools).
6. Overwrite your game's DSDBP archive you your edited one (as always, make a backup!).
7. **You *might* also have some success using [SimpleDSCSModManager](https://github.com/Pherakki/SimpleDSCSModManager) to do this automatically.**

## Potential fixes for common "bugs"
1. If your mesh has some highly distorted polygons that converge at the centre of the room (or obscure the screen), this is likely an issue with vertex weights. Should be resolved in the future once investigated.
2. If the import/export options do not appear, navigate to your Blender addons folder. On Windows, this folder is located in: drive\Users\User\AppData\Roaming\Blender Foundation\Blender\version\scripts\addons, and you can navigate to "User\AppData\Roaming\" by typing "%appdata%" into the file address bar in File Explorer. Ensure that the addon code is in a folder, perhaps named something like "Blender-Tools-For-DSCS_master", and not in a bunch of folders like "FileReaders", "CollatedData" etc. If the code is not contained in a single folder in this manner, create a new folder and drag + drop all the code from this addon into the folder. The contents of this folder should now contain files and folders in the GitHub repository. Restart Blender, and re-load the addon.
   
## Some Known Bugs and Limitations
1. There are some issues with vertex normal import and export.
2. Material names are not yet those found within the files.

## Future Plans
1. Finish decoding the remaining unknown bytes
2. Export Animations
3. Readers for remaining filetypes: DETR, NAVI, NOTE, PHYS, SPRK
4. An external program that can assign shaders to models

## Contact
e-mail: pherakki@gmail.com

reddit: [u/Pherakki](https://www.reddit.com/user/Pherakki)

## Notes
1. I have next to no experience with Blender or its API. The import script is a bit of a mess which will hopefully get cleaner over time.
2. Images are stored in a 'img' format, which is secretly a DDS (BC2; Linear DXT3 codec) **with mipmaps**. The game will not enjoy the experience of trying to load anything else and will present you with blank textures in retaliation. Save your editted (or new) textures as a BC2 DDS and rename the extension (I have not yet checked if renaming the extension is necessary).

## Acknowledgements
This project would not have even got off the ground without the [DSCSTools program](https://github.com/SydMontague/DSCSTools) by [SydMontague](https://github.com/SydMontague). Also, the [CSGeom program](https://github.com/xdanieldzd/CSGeom) by [xdanieldzd](https://github.com/xdanieldzd) was very useful to compare against for the geom files, even though the file format has changed somewhat for the PC release.
