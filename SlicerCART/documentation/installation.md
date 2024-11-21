# SlicerCART Installation

## Requirements

* MacOS Sonoma or Sequoia (15.0.1) is recommended 
* [3D Slicer](https://download.slicer.org) version 5.6.2.
* Qt: might need to be installed.
  * The first five steps of the following procedure might be useful for this: [procedure](https://web.stanford.edu/dept/cs_edu/resources/qt/install-mac).
  * You can try importing Qt in the Slicer python console (e.g. `import slicer ` then `from slicer.util import Qt`)

*Although it may work on other versions and/or operating system, please note 
that it has not been tested.

If 3D Slicer has not been already installed, you can follow these steps: 
1. Install [3D Slicer](https://download.slicer.org):
2. Make sure that you are able to open and use the 3D Slicer software before 
   trying installing any extension/module. 
3. If you encounter some problems, you are encouraged to refer to:
   * [3D Slicer Documentation](https://slicer.readthedocs.io/en/latest/)
   * [3D Slicer forum](https://discourse.slicer.org/) (very active community)

## Installation Steps

1. Clone the [SlicerCART repository](https://github.com/neuropoly/slicer-manual-annotation) in the location of your choice.
2. Open 3D Slicer. 
3. Activate the checkbox `Enable developer mode` in `Edit 
   -> Application 
    Settings -> Developer -> Enable developer mode`. 
4. Open Finder (on macOS). Go to the location of the SlicerCART Repository. 
   Go to the location of the python file `SlicerCART.py` (_should only have one 
   FILE of that name. Note that if you add the path of the folder SlicerCART,
   it will not work: you MUST add the path of SlicerCART.py FILE_)  in `Edit -> Application Settings 
   -> Modules -> Additional module paths`. See image example below:
![](images/module_filepath.png)

Warning: be sure to drag and drop `SlicerCART.py` and not `SlicerCART` (the folder). 

5. The Application will ask to Restart: click Ok.
![](images/example_restart.png)

6. The module can be found under `Examples -> SlicerCART`: the module should 
   now be opened (N.B. If first use, you may have additional requirements 
   to install. A pop-up window from Slicer advertising you should pop-up if so: just click ok).
![](images/example_slicercart.png)


8. (Optional) Set the SlicerCART module to launch at 3DSlicer startup. To do so, go to `Edit -> Application Settings -> Modules -> Default startup module`
9. There might be errors. These would be seen in the Python Console: if any errors, we highly recommend you to fix them before any further use!

**In Summary:**

Install 3D Slicer --- Enable Developer Mode --- Add the PATH of SlicerCART.
py file in the modules list --- (Optional) Select to launch SlicerCART at 3D 
Slicer --- restart 3D Slicer --- READY FOR USE!

![](images/module_filepath.png)


### Troubleshooting 

* Qt might need to be installed. The first five steps of the following procedure might be useful for this: [procedure](https://web.stanford.edu/dept/cs_edu/resources/qt/install-mac).

### Other extensions that could be useful
* `SlicerJupyter` to be able to use Jupyter Notebooks connected to 3D Slicer.

[GO BACK on Documentation Welcome Page](welcome.md). 
[CONTINUE to QuickStart](quickstart.md).
