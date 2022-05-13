# ImageSort

This script sorts images by their resolutions into the directories named "Width x Height" (for example, "1920x1080").

* if folder already exists files will be added there,
* if the file with the same names already exists, then the new file will be renamed:
  "({num})" will be added to its name (for example, "wallpaper(3)").

All images from the nested directories in the initial folder will be sorted too.

* Files for which resolution couldn't be determined will be copied or moved to the directory "Not images" in the target folder.


## To run script:
`\..\imagesort.py mode "initial folder" "target folder"`

### mode = dryrun, copy, move, sort
* `dryrun "path"` generates html-report with sorted files structure from inputted folder
* `copy "path_1" "path_2"` sorts files from "directory_1" into "directory_2"
* `move "path_1" "path_2"` sorts and moves files from "directory_1" into "directory_2"
* `sort "path"` sorts files into the inputted folder and deletes the initial files


## Script runs on Python 3.8, with next modules:
* `copy`, `hashlib`, `os`, `pathlib`, `shutil`, `stat`, `sys` (standard library)
* `argparse`, `Chameleon`, `Pillow`  (3rd party library)