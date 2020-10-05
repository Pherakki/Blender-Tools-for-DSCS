# Blender Tools for Digimon Story: Cyber Sleuth
This repository provides a work-in-progress addon for Blender 2.8 that can (to some degree) import model files from the PC version of Digimon Story: Cyber Sleuth. It provides a new option in File > Import named "DSCS Model", which should be pointed towards 'name' files in the game data. Experimental export functionality is in-progress.

## Preparation
1. Unpack the game files with [DSCSTools](https://github.com/SydMontague/DSCSTools), following the instructions in the readme.
2. Install Blender Tools for DSCS as a zip archive like any other Blender addon.

## Usage
1. The model files are split into name, skel, and geom files. Currently, these must all be in the same directory in order for the import to be successful.
2. Textures are expected to be located in a directory named 'images' in the same directory as the name, skel, and geom files.
3. Open Blender, navigate to File > Import > Import DSCS and open the appropriate name, skel, or geom file (all three will currently be simultaneously imported).
4. If you point the import function towards the unpacked game files, all the files will be already in a location understandable by the import script.

## Some Known Bugs and Limitations
1. Material names are not yet those found within the files.
2. There are five types of data attached to vertices not currently understood.
3. Materials are almost completely not understood.

## Future Plans
0. ~~Some time in October 2020 I may upload a cleaner version of my export script, so that others can experiment with tweaking the unknown byte data and report back with any in-game findings. Since limiting this experimentation to users who can use Python would likely reduce the number of people using it, this should be an executable GUI program...~~ Experimentation will be integrated with Blender export functionality
1. Finish decoding the remaining unknown bytes
2. Add support for export from Blender
3. Add readers for anim files

## Contact
e-mail: pherakki@gmail.com

## Notes
1. I have next to no experience with Blender or its API. The import script is a bit of a mess which will hopefully get cleaner over time.
2. Images are stored in a 'img' format, which is secretly a DDS (BC2; Linear DXT3 codec) **with mipmaps**. The game will not enjoy the experience of trying to load anything else and will present you with blank textures in retaliation. Save your editted (or new) textures as a BC2 DDS and rename the extension (I have not yet checked if renaming the extension is necessary).

## Acknowledgements
This project would not have even got off the ground without the [DSCSTools program](https://github.com/SydMontague/DSCSTools) by [SydMontague](https://github.com/SydMontague). Also, the [CSGeom program](https://github.com/xdanieldzd/CSGeom) by [xdanieldzd](https://github.com/xdanieldzd) was very useful to compare against for the geom files, even though the file format has changed somewhat for the PC release.
