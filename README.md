# Blender-Tools-for-DSCS
This repository provides an addon for Blender 2.8 that can (to some degree) import model files from the PC version of Digimon Story: Cyber Sleuth. It provides a new option in File > Import named "DSCS Model", which should be pointed towards 'name' files in the game data. 

## Preparation
1. Unpack the game files with [DSCSTools](https://github.com/SydMontague/DSCSTools), following the instructions in the readme.
2. Install Blender Tools for DSCS as a zip archive like any other Blender addon.

## Usage
1. The model files are split into name, skel, and geom files. Currently, these must all be in the same directory in order for the import to be successful.
2. Textures are expected to be located in a directory named 'images' in the same directory as the name, skel, and geom files.
3. Open Blender, navigate to File > Import > Import DSCS and open the appropriate name, skel, or geom file.
4. If you point the import function towards the unpacked game files, all the files will be already in a location understandable by the import script.

## Some Known Bugs and Limitations
1. Material names are not yet those found within the files.
2. Some vertices have no weights.

## Future Plans
1. Finish decoding the remaining unknown bytes
2. Add support for export from Blender
3. Add readers for anim files

## Acknowledgements
This project would not have even got off the ground without the [DSCSTools program](https://github.com/SydMontague/DSCSTools) by [https://github.com/SydMontague](SydMontague). Also, the [CSGeom program](https://github.com/xdanieldzd/CSGeom) by (xdanieldzd)[https://github.com/xdanieldzd] was very useful to compare against for the geom files, even though the file format has changed somewhat for the PC release.
