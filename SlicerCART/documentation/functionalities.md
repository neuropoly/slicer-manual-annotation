# SlicerCART Functionalities

This section lists the functionalities of SlicerCART. If the function you 
are looking for is not found below, it is likely that SlicerCART does not have 
yet 
this feature: you are invited to open an issue on the [Github Repository](https://github.com/neuropoly/slicer-manual-annotation/issues) to 
request the functionality you are looking for.

**Specific functions (in details)**

This module has been adapted to perform several tasks. Among other things, it allows the user to:

* Customize configuration preferences for optimizing workflow for
  segmentation or classification tasks, including:
  * Task Selection (Segmentation and/or Classification)
  * Modality to be viewed/process/annotated (CT or MRI)
    * (Must one or the other for now. Does not currently take DICOM images)
  * Brain Imaging Data Structure (BIDS) format imposition (test quickly if a 
    dataset respects the BIDS convention through a BIDS-validator script: 
    makes unable to load a dataset if it does not respect BIDS format)
  * View to be displayed by default in the Slicer viewer (e.g. 
    axial, sagittal, etc.)
  * Interpolation of images (by default, Slicer images that are displayed 
    get "interpolated" (i.e. smoother): with SlicerCART, you can select this 
    option that can be relevant for segmentation tasks)
  * For CT-Scans:
    * Specify the range of Houndsfield units for which a segmentation mask 
      will be feasible (e.g. 45 to 90): otherwise, segmentation mask will 
      not be created.
  * Customize keyboard shortcuts
  * Customize mouse button functions
  * Configure from the GUI the segmentation labels, 
    including:
    * Label name
    * Label value
    * Color
    * Adding/Removal of labels
  * Select if timer should be displayed during segmentation task
  * Configure from the GUI the classification labels, 
    including adding/Removal of:
    * Labels 
    * Checkbox 
    * DropDown Menu with choice selection
    * Text field
  * (Specify to save all segments to one file or multiple files)TO DO
* Identify the name, degree and revision step related to the human annotator
* Select folder of interest where volumes are saved (and possibly impose BIDS)
  * Displays automatically the PATH of the loaded volume
* Select the output folder where processing and work is preferred to be saved
* (Select a ground-truth folder where references studies can be used for 
  iterative self-assessment)TO COME
* Display in the GUI a case list of all the studies of interests for the segmentation task (*from a site directory or a customized list)
* Select from the GUI case list any volume of interest to display
* Navigate through case list from next and previous buttons
* (Load automatically the first remaining case for segmentation in a 
  customized list)TO COME
* Create automatically all required segments that may be used according to the project configuration each time a volume is displayed
* From the Segmentation window:
  * Open quickly the Segment Editor
  * Start Painting for the first label
  * Erase any part of visible masks
  * Select Lasso Paint (fills the space of a contour-based geometrical 
    annotation)
  * (Place a measurement line) TO COMPLETE
* Toggle interpolation of the volume loaded
* Execute multiple automated functions when saving segmentation masks for a given volume. Indeed, the automated functions:
  * Save segmentation masks in the selected output folder with volume file hierarchy
  * Track the different versions (save the following version if previous version(s) already exist(s)) **N.B. limitation to 99 versions for a single volume*
  * Save a .csv file with segmentation statistics (e.g. subject, annotator's name and degree, revision step, date and time, total duration, duration of each label annotation)
  * Save a .csv file with classification statistics (e.g. subject, annotator's name and degree, revision step, date and time, checkboxes / dropdown / free text fields)
  * (Go to the next remaining case and make it ready to segment without any 
    further action)TO COME
* Load a pre-existing segmentation for further modification (will be saved as a new version of the segmentation)
* Compare different versions of segmentation TO COMPLETE
  * Specify versions to be loaded at the same time
  * Display multiple versions of segmentation masks at the same time
  * Modify specific segments of different versions
  * Save all segments displayed +- modified on the viewer as a version += 1 
    of segments in the output folder

[GO BACK on Documentation Welcome Page](welcome.md).
[Go BACK to User Guide](userguide.md).
[CONTINUE to Purpose](purpose.md). 