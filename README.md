# ImageSort

This script sorts images by their resolutions from the INITIAL folder to the TARGET folder.
In the target folder new directories named "Width x Height" (for example, "1920x1080") will be created.

* if target folder doesn't exist then it will be created;
* if folder already exists files will be added there;
* if the file with the same name already exists, then the new file will be renamed:
  "({number})" will be added to its name (for example, "wallpaper(3)").

All images from the nested directories in the initial folder will be sorted too.

* files for which resolution couldn't be determined will be copied or moved to the directory "Not images" in the target folder.
***


## Installation
`Python` 3.9+ (tested to work with == 3.12.3)  
The packages can be installed by running
```commandline
python3 -m pip install -r requirements.txt
```
***


## Run script
To sort files from initial dir and generate html report run
```commandline
imagesort.py dryrun "path/to/initial/dir" "path/to/report/dir"
```

To sort and copy files from initial dir into target dir run
```commandline
imagesort.py copy "path/to/initial/dir" "path/to/target/dir"
```

To sort and move files from initial dir into target dir run
```commandline
imagesort.py move "path/to/initial/dir" "path/to/target/dir"
```

To sort files into initial dir and delete the initial files run
```commandline
imagesort.py sort "path/to/initial/dir"
```
***


## To test script run
```commandline
pytest
```
***


### Files and directories:
* `./errors` package with exceptions for the main script  
* `./image_att` sorting files module
* `./templates` templates directory
- `./tests` tests module
* `imagesort.py` script for sorting images by resolutions
- `requirements.txt` required packages
