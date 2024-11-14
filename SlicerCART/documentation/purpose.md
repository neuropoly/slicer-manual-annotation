# SlicerCART Purpose

This section explains the rationale behind SlicerCART and its purpose.


**Rationale:**

* Manual segmentation and classification tasks are required in the research setting related to medical imaging artificial intelligence tool development
* An open-source solution for such tasks would better benefit the research setting
* Actual open-source solutions that enable imaging viewing and annotation are not optimal from an end-user standpoint (especially from various background), increasing the already high burden of manual segmentation and classification tasks
* A workflow aimed to efficiently navigate through a dataset while performing manual segmentation / correction, including revision steps and robust annotation consistency assessment is crucial for handling large amount of data and provide the best ground-truth references segmentation as possible. 

**Module specific functions (in details)**

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