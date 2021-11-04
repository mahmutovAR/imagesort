"imagesort.py" sorts images by their resolutions.

Application creats directories named "Width x Height" (for example, "1920x1080"),
if folder already exists files will be added there,
if there are files with the same names, but they are different,
then the new file will be renamed "!{num}-" will be added to its name.

The directories in the initial folder won't be modified.

Files with "not image" format in the initial folder will be copied or moved to
the directory "Other files" in the target folder.
Files for which resolution couldn't be determined will be copied or moved to
the directory "Error files" in the target folder.


To run application:
\..\imagesort.py "initial folder" "target folder" "mode"

"mode" = default, dryrun, copy
default - sorts images and moves them from the initial folder to the target folder
dryrun – creates the html repor in the target folder
copy - sorts images and copies them to the target folder


Application works on Python 3.8.0 and up, with next modules:
PIL (installation required for Python 3.7)
Chameleon
