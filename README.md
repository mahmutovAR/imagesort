# ImageSort

This script sorts images by their resolutions from the INITIAL folder to the TARGET folder.
In the target folder new directories named "Width x Height" (for example, "1920x1080") will be created.

* if target folder doesn't exist then it will be created;
* if folder already exists files will be added there;
* if the file with the same name already exists, then the new file will be renamed:
  "({number})" will be added to its name (for example, "wallpaper(3)").

All images from the nested directories in the initial folder will be sorted too.

* files for which resolution couldn't be determined will be copied or moved to the directory "Not images" in the target folder.


## To run script:
* `imagesort.py dryrun "initial_dir" "report_dir"` sorts files from "ini_dir" and generates html report in "report_dir"
* `imagesort.py copy "initial_dir" "target_dir"` sorts and copies files from "initial_dir" into "target_dir"
* `imagesort.py move "initial_dir" "target_dir"` sorts and moves files from "initial_dir" into "target_dir"
* `imagesort.py sort "initial_dir"` sorts files into "initial_dir" and deletes the initial files

### Files and directories:
* `imagesort.py` script for sorting images by resolutions
- `imagesort_tests.py` unittest script
* `./errors` package with exceptions for imagesort.py
- `./image_att/image_attributes.py` package with module for sorting files
* `./templates/report_temp.pt` template of html report
- `./tests` directory with tests of imagesort.py
* `./tests/errors` package with exceptions for imagesort_tests.py
- `./tests/reference report and structure`
- - `control report.html` reference html report for testing
- - `control structure.json` json file with reference directory structure for testing
* `./tests/unsorted` directory with files for testing

## Script runs on Python 3.9, with next modules:
* `hashlib`, `os`, `pathlib`, `shutil`, `stat`, `sys` (standard libraries)
* `argparse`, `Chameleon`, `Pillow`  (3rd party libraries)

### Test of ImageSort runs with next modules:
* `json`,`tempfile`, `unittest` (standard libraries)
* `bs4` (3rd party library)