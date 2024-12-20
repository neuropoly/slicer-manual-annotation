import qt
import slicer
# TODO: There is probably a more elegant way to install pacakages through the
#  extension manager when the user installs the extension.
# TODO: check if the package installed with error

# Dictionary of required python packages and their import names
REQUIRED_PYTHON_PACKAGES = {
    "nibabel": "nibabel",
    "pandas": "pandas",
    "PyYAML": "yaml",
    "pynrrd": "nrrd",
    "slicerio": "slicerio",
    "bids_validator": "bids_validator"
}


def check_and_install_python_packages():
    missing_packages = []

    for pip_name, import_name in REQUIRED_PYTHON_PACKAGES.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(pip_name)

    if missing_packages:
        msg = ("SlicerCART module: The following required python packages are "
               "missing:")
        msg += "\n" + "\n".join(missing_packages)
        msg += "\nWould you like to install them now?"
        response = qt.QMessageBox.question(slicer.util.mainWindow(),
                                           'Install Extensions', msg,
                                           qt.QMessageBox.Yes |
                                           qt.QMessageBox.No)
        if response == qt.QMessageBox.Yes:
            for pip_name in missing_packages:
                slicer.util.pip_install(pip_name)
                # Wait for the installation to complete
                slicer.app.processEvents()
            qt.QMessageBox.information(slicer.util.mainWindow(),
                                       'Restart Slicer',
                                       'Slicer will now restart to complete '
                                       'the installation.')
            slicer.app.restart()
        else:
            qt.QMessageBox.warning(slicer.util.mainWindow(),
                                   'Missing Extensions',
                                   'The SlicerCART module cannot be loaded '
                                   'without the required extensions.')
