
Below are usage examples that guide the user through accomplishing different tasks.

#### At each start

(**Config the option to launch automatically the last folder used TODO)**

1. Select the volume folder you want to use for your segmentation task. Please note that this selection has been settled voluntarily to be done at each startup since the folder should be a site (e.g. site_003) in a BIDS formatted dataset, and that a site may change according to the evolution of a project.
2. Select the ouput folder you want to use for saving your segmentations.
   - If empty: this will automatically create two .yaml files 1) allCases.yaml containing all the cases matching criteria of interests (from the config.yaml file) from the selected volume folder directory 2) remainingCases.yaml containing all remaining cases to segment. Please not that this folder does not needs to be empty (see below).
   - If not empty: this will begin by looking for the 2 files allCases.yaml and remainingCases.yaml and update the GUI case list according to the list 'FILES_SEG' in allCases.yaml, and display in the slice viewer the first volume named in the list 'FILES_SEG' in remainingCases.yaml. In fact, if you want to focus your segmentation task on a specific contrast and/or view (e.g. T2w sagittal), this allows the GUI case list (from allCases.yaml) to represent your cases of interests (you just need to replace the elements of 'FILES_SEG' list in allCases.yaml by the elements of interests [at the first time the task is about to be performed, the 'FILES_SEG' list in remainingCases.yaml would ideally be the same as in allCases.yaml). Also, if you have already started your segmentation task (e.g. segmentation completion for 5 cases), this selection will enable to start from where you were at the end of your last segmentation (will load automatically the first element of remainingCases.yaml).

   
4. Select the ground-truth references folder you want to use when assessing your consistency and/or agreement with ground-truth images.

#### **Assess Segmentation and Get Results buttons**

To test if your segmentations that you want to perform would be consistents with some already considered successful manual segmentations and/or with segmentations that you have previously done, you may want / should try to perform manual segmentation on a case that has been already completed. This module allows you to do it in 3 steps:

1. *Click on Assess Segmentation button:* this will randomly select a volume in the ground-truth references folder ---> display it in the slice viewer with an anonymized name ---> create new test segments according to the label maks configured for this project ---> open the segment editor module and makes you ready to perform manual segmentation (same as if you would segment a new case)
2. *Perform manual segmentation:* complete a manual segmentation task as if you would proceed to the segmentation of a new case
3. *Click on Get Results button:* once you have completed the manual segmentation and clicked on this button, this will automatically compute the Dice Score (an agreement metrics) between your freshly done segmentation and the reference segmentation for each segmentation mask labels. If both segment are empty, this will show the value infinite, and label(s) will not be considered in the Dice Score mean.

#### **Start Segmentation**

Write the annotator's name in its specific text box. Select the annotator's degree and revision step (from 0 to 2) in the dropdown label menu. Altough this information can be modified at any time, it is mandatory for saving segmentations.**TODO: activate the function that mandate annotator's name requirements.**  **Please note that the revision step is different than the version since a single user may have multiple segmentation versions for the same revision step and both should not interfere.*

When you are ready to perform manual segmentation and/or correction on new data, you can click on Start Segmentation.

This will open the 3D Slicer segment editor modules and enables you to paint on the volume for the first segmentation label of the config.yaml file.

If you want to perform segmentation for another mask, you need to click on it in the segment editor module.

N.B. #1 You can adjust the painting sphere dimension by pressing "Shift" and scrolling the mouse wheel after having pressed in the slice viewer.

N.B. #2 From the moment you modify the first segmentation label in your segmentation label masks list, a timer is started in the background and will be resetted only when segmentation is saved.

#### **Save segmentation**

**Once a segmentation of a case is ready to be saved, you have to click on the Save segmentation button.**

**As mentioned earlier, this will:**

* Save segmentation masks in the selected output folder/versions (*if first version, creates automatically a versions folder)**
* Track the different versions (save the following version if previous version(s) already exist(s)) N.B. limitation to 99 versions for a single file*
* Save a .csv file with segmentation statistics (e.g. subject, annotator's name and degree, revision step, comments)
* Save a .json with segmentation statistics (e.g. subject, annotator's name and degree, revision step, comments) TODO
* Generate a QC report (using the QC report template from SCT) TODO
* Save the segmentation mask in the derivative folder of the subjet, and git version it! TODO (could be also from a QPushButton)
* Go to the next remaining case and make it ready to segment the first segmentation label mask without any further action

#### **Load masks**

This button allows to display/undisplay the latest version segmentation masks for a given volume (toggle).

For example, if the latest version for a given version is _v03 for label1 and label2, but _v02 for label3, _v03 for label1 and label2 and _v02 for label3 will be displayed.

Please note that if you want to see the segmentation mask for the currently displayed volume, you need to click again on the same case in the UI case list. TODO: make it update automatically ...

#### **Toggle Segmentation Versions**

This button allows to display specific versions in the slice viewer. A single or multiple versions can be displayed at the same time according to the user's needs. When a version is selected and displayed, the button becomes with a green background to indicate that the version is currently displayed. If the button is clicked again (toggled), then the corresponding version is undisplayed and the button becomes with normal background color (indicates that the version is not loaded).

N.B. If you open the segment editor and remove from the display some segment for a given version (even all), the toggle buttons will stay with green background. TODO: correct a bug when 2 labels selected (works ok with 3 labels) that makes loading 2 versions at the same time.

#### **Toggle Interpolation**

This button reverses the interpolation state of the volumes that are displayed. By default, the state of each volume (and segmentation mask) will be the one setted in the config.yaml file. If the toggle Interpolation is clicked, interpolation state of each volume that will be loaded after will be the same that has been determined by the last click on the Toggle Interpolation button. This can be reached also from a keyboard shortcut.
