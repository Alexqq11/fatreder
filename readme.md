util for reading, writing and parsing fat32 dumps
requires python >=3.5
for your attention tests folder contains 256 mb of test images

python fatreader.py
usage: fatreader [-h] [-n] [-k] [-l LOAD]
                 {load,ls,cp,cd,md,pwd,exit,move,cat,rm,rmdir,rename,size} ...

watch an extract file and directories in fat32 images

positional arguments:
  {load,ls,cp,cd,md,pwd,exit,move,cat,rm,rmdir,rename,size}
                        sub-command help
    load                load -h , --help
    ls                  ls -h, --help
    cp                  cp -h, --help
    cd                  cd -h, --help
    md                  md -h, --help
    pwd                 pwd -h, --help
    exit                exit -h, --help
    move                move -h, --help
    cat                 cat -h, --help
    rm                  rm -h, --help
    rmdir               rmdir -h, --help
    rename              rename -h, --help
    size                size -h, --help

optional arguments:
  -h, --help            show this help message and exit
  -n, --no-scan         do not check the image for errors
  -k, --keep-alive      do not exit from util after get sys.args
  -l LOAD, --load LOAD  load working image from path
  About:

  Yoy can cat content of files, look at file tree.
  Export files from image, or import it
  And explore fat dumps.
  You use it "as is" at your own risk.
  may be it last commit for this project, because it was created in for training purposes.
  this project distributed under "MIT" license
  Test Coverage more than 81%

  About files in project:

  for run CLI or CUI use fatreader.py
  Core.py Core class links utils and file structure parsers
  If you want use it like a library look at FileSystemUtils.py.
    Here you can find realization of commands for working with image
  For working with fat allocation table you can use classes from FatTableReader.py
  In Structures.py and ReservedRegionReader.py you can find how organized and how work with service fields of fat image.
