By Dr Laurent Létourneau-Guillon (May 2024)

# DEVELOPMENT GUIDELINES

## Objective: Generalize the ICH_Segmenter_V2 tool

A configurable annotation and review tool for medical imaging. 
A module that can be easily configured to annotate and perform iterative review of medical images. 
Capability for image/volume level annotation (checkbox, combo box, freetext) and segmentation (loading volume and mask, relying mainly on the segment editor to perform annotation).
Since each segmentation project is unique, I would not attempt to integrate all possible features of the segment editor tool in this module. Although adding the Hounsfield unit for CT annotation is a good idea it will not be useable for MRI tasks (perhaps this could be encapsulated in another module in the future). 


The ICH_Segmenter_V2 tool, available at [ICH_SEGMENTER_V2](https://github.com/laurentletg/ICH_SEGMENTER_V2), can be adapted for similar projects involving other pathologies.

### Features:
1. Compatible with the Slicer module format. For example, it adheres to the singleton parameter mode pattern as seen in the [Slicer tutorial on YouTube by ETS](https://youtu.be/tOldfUkSecI?si=JfNKnhsXuLk9okhD). Note: the new version of Slicer uses a `@decorator` for this, see [documentation](https://slicer.readthedocs.io/en/latest/developer_guide/parameter_nodes/overview.html#parameter-node-wrapper). The goal is to have it approved and [accessible via the extension manager](https://slicer.readthedocs.io/en/latest/developer_guide/extensions.html) for increased visibility.

### Requirements:

- Configurable (at a minimum, pair of label ID/name: value)
- Configuration file vs. another Slicer module to generate config (yaml vs json vs toml) - could potentially be another module within the same extension that write a config file (easier for beginners)
- Ability to add checkboxes, combo boxes, and freetext via configuration, with their names. See the beginning of the 'gui/DynamicGUI' code here: [Slicer_module_case_review](Other modules to be integrated for reference DO NOT DEVELOP HERE/Slicer_module_case_review/RSNA_Reviewing_normal_cases/gui)
- Add keyboard shortcuts (ideally configurable) - see ICH Segmenter_V2 for an example (and below in the ICH_SEGMENTER_V2 config file. 
```yaml
- KEYBOARD_SHORTCUTS:
  - method: "keyboard_toggle_fill"
    shortcut: "d"
```
- Support for multi-series (e.g., MRI with T1, T2, etc.) - see BraTS GUI
![](SlicerCART/res/img/example_multi_series_brats.png)
- Note that the BraTS GUI expect the following folder structure:
```
- BraTS2021
      - BraTS2021_001
        - BraTS2021_001_flair.nii.gz
        - BraTS2021_001_t1.nii.gz
        - BraTS2021_001_t1ce.nii.gz
        - BraTS2021_001_t2.nii.gz
        - BraTS2021_001_seg.nii.gz
      - BraTS2021_002
        - BraTS2021_002_flair.nii.gz
        - BraTS2021_002_t1.nii.gz
        - BraTS2021_002_t1ce.nii.gz
        - BraTS2021_002_t2.nii.gz
        - BraTS2021_002_seg.nii.gz

```
![](SlicerCART/res/img/folder_structure_brats.png)
- See code for loaded patient – study – series in ICH Segmenter_V2 and BraTS GUI: [2023_ASNR_AI_workshop_curation](https://github.com/laurentletg/2023_ASNR_AI_workshop_curation)
- Annotation version saving including annotator name, level and review step, as currently done in ICH_Segmenter_V2.
- Support for multi-study comparison (different time points)- not yet implemented.
- ?Implement BIDS format ? (of the option to use BIDS format ?). 

### Development Notes:

- Start from ICH Segmenter and refactor to remove superfluous elements
- Implement the parameter node thing (described above)
- Move all logic to the logic class
- Add minimal tests in the test class
- Fragment code into sub-modules (too many lines of code) – I have tried but failed because it requires going through the Slicer interpreter. I haven't yet figured out how to do this.
- Possible inspiration: [Case Iterator module](https://github.com/JoostJM/SlicerCaseIterator), MONAILabelReviewer (part of the MONAI label extension).
- Potentially, implement the option to load more than one series per study. 
- Possibility to add a list widget for patient and studies separetely with the possibility to navigate at the patient and study level separately. If there are multiples series per patients load all series nested under the patient - studies (see Brats example). 
- Consider the best way to serialize results (csv vs json vs sql). Currently in csv, as my logic is that it is easier for anyone to make manual corrections in csv than in json (less readable) or sql (requires software to access the database – heavier code).

### Meeting notes
- [2024-06-07](https://docs.google.com/document/d/16Dwak4ILy49S0yHlvBe5NdN4Gaa9qxwiJnC8ZRQ1jMM/edit)
