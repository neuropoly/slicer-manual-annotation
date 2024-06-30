# SlicerCART
![slicerCART logo.png](SlicerCART/src/resources/Icons/SlicerCART.png)
SlicerCART : Configurable Annotation and Review Tool. 


## Description

* 3D Slicer extension
* Adapted from code of Dr. Laurent Létourneau-Guillon and his team in [ICH_SEGMENTER_V2](https://github.com/laurentletg/ICH_SEGMENTER_V2), [SlicerCART](https://github.com/laurentletg/SlicerCART), and [Brain_Extraction](https://github.com/MattFr56/CT_Brain_Extraction/blob/main/Brain_Extraction/Brain_Extraction/Brain_Extraction.py). This is an effort to create a unified code for a configurable 3D Slicer extension. 
* Inspired from [Neuropoly](https://neuro.polymtl.ca/)'s workflow. 
* This tool is made to improve manual segmentation workflows across different teams. 

**Keywords:** medical imaging, manual segmentation, manual correction, workflow, ground-truth segmentation, quality control

**Abbreviations:**

- MRI - Magnetic Resonance Imaging
- CT - Computed Tomography
- BIDS - Brain Imaging Data Structure
- GUI - Graphical User Interface
- QC - Quality Control

This module has been adapted to perform several tasks. Among other things, it allows the user to:

* Customize configuration preferences (see below for details)
* Customize keyboard shortcuts
* Identify the name, degree and revision step related to the human annotator
* Select folder of interest where volumes are saved (and possibly impose BIDS)
* Select the output folder where processing and work is preferred to be saved
* Select a ground-truth folder where references studies can be used for iterative self-assessment
* Display in the GUI a case list of all the studies of interests for the segmentation task (*from a site directory or a customized list)
* Select from the GUI case list any volume of interest to display
* Navigate through case list from next and previous buttons
* Load automatically the first remaining case for segmentation in a customized list
* Create automatically all required segments that may be used according to the project configuration each time a volume is displayed
* Toggle interpolation of the volume loaded
* Execute multiple automated functions when saving segmentation masks for a given volume. Indeed, the automated functions:
  * Save segmentation masks in the selected output folder with volume file hierarchy
  * Track the different versions (save the following version if previous version(s) already exist(s)) **N.B. limitation to 99 versions for a single volume*
  * Save a .csv file with segmentation statistics (e.g. subject, annotator's name and degree, revision step, date and time, total duration, duration of each label annotation)
  * Save a .csv file with classification statistics (e.g. subject, annotator's name and degree, revision step, date and time, checkboxes / dropdown / free text fields)
  * Go to the next remaining case and make it ready to segment without any further action
* Load a pre-existing segmentation for further modification (will be saved as a new version of the segmentation)

### Requirements

* MacOS Sonoma (recommended)
* A working version of [3D Slicer](https://download.slicer.org).
  * N.B. The version used to develop this module is the version 5.2.2 since more recent versions were not able to support some extensions that previously worked (e.g. JupySlicer)

This module has been developed on:

* MacOS Sonoma version 14.1.1
* 3D Slicer version 5.2.2

Although it may work on other versions and/or operating system, please note that it has not been tested.

## Installation steps
1. Install [3D Slicer](https://download.slicer.org).  
2. Clone this repository.
3. Modify `label_config.yml` to describe your annotations. There can be as many or as few as you would like. The colors are configurable using RGB integer values between 0 and 255. The default HU thresholds for each label are also configurable. These can also be modified directly in the extension. Note that additional tools will appear in the user interface if one of the labels is either intracerebral hemorrhage (ICH) or perihematomal edema (PHE). 
4. Open 3D Slicer. 
5. Activate the checkbox `Enable developer mode` in `Edit -> Application Settings -> Developer -> Enable developer mode`. 
6. Add the path of the folder containing the `SlicerCART.py` file in `Edit -> Application Settings -> Modules -> Additional module paths`. 
    * There might be errors. These would be seen in the Python Console. 
7. The module can be found under `Examples -> SlicerCART`. 
8. (Optional) Set the SlicerCART module to launch at 3DSlicer startup. To do so, go to `Edit -> Application Settings -> Modules -> Default startup module`

### Trouble shooting 
* Qt might need to be installed. The first five steps of the following procedure might be useful for this: [procedure](https://web.stanford.edu/dept/cs_edu/resources/qt/install-mac). 
* If some modules are missing (`ModuleNotFoundError`), they must be added to the 3D Slicer environment by using the following commands in the Python Console: 
        `from slicer.util import pip_install`
        `pip_install("XYZ")` where `XYZ` is replaced by the proper library

### Other extensions that could be useful
* `SlicerJupyter` to be able to use Jupyter Notebooks connected to 3D Slicer.

### Documentation
TODO (after sufficient development has been made)
* [SlicerCART Demo Video (June 24th 2024)](https://drive.google.com/drive/u/0/folders/1DClUQDOvTnbYoe68sdhgmVo_GL7vkBKA)
* Example of workflow that could be implemented (documentation [here](https://github.com/neuropoly/slicer-manual-annotation/blob/main/workflow_example.md)) with videos examples ([12min30:](https://www.dropbox.com/scl/fi/ddhj5f2rx2ydzy2k7s6b8/slicer-manual-annotation_overview.mov?rlkey=rhgs9usmhqfbfe9tylmk42tlo&st=c5zhnyjs&dl=0) summary; [40min](https://www.dropbox.com/scl/fi/j8e3xuhugjylg3hhxhzm7/20240619_slicer-manual-annotation-detailed_explanations.mov?rlkey=0otcuw4nwjuo8l72qxohir8ry&st=6vu8ob2n&dl=0): detailed).

### Video tutorials 
TODO (after sufficient development has been made)

### Other resources
* [3D Slicer Tutorials](https://www.youtube.com/watch?v=QTEti9aY0vs&)
* [3D Slicer Documentation](https://www.slicer.org/wiki/Documentation/Nightly/Training)

### Contributors

* Laurent Létourneau-Guillon
* Emmanuel Montagnon
* An Ni Wu
* Maxime Bouthillier
* Delphine Pilon
