# AGS History Extractor

This tool unarchives multiple AGS release archives and pulls out demo and template data, in order to produce a rough
history in a git repository.

## Use

Note: If you're running under OSX, you may need to run under a case-sensitive file system to properly track filename
case changes between DOS and Windows.

 * Place zip files into data/
 * Edit order.txt to determine order to load zip files.
 * Run ./process.py

## Sourcing Releases

AGS releases have been archived all over the place. I sourced from:

 * http://www.adventurestockpile.com/AGS/
 * https://www.agsarchives.com/engine.html
 * http://www.adventuregamestudio.co.uk/finals/
 * http://www.agagames.com/ags/
