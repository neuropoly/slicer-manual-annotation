#!/bin/bash

echo "The sct_qc command from sct will be executed for manual segmentation"

echo ""
echo ""

echo "background image bg_image:" ${1}
echo "current_segment_path:" ${2}
echo "current_roi:" ${3}
echo "output_folder:" ${4}

# Note that this is a non-working example. Basic shell script can be run, but
# running other programs from the terminal still has to be completed (issues
# with 3D Slicer python interpreter)
#export PYTHONPATH=/Users/maximebouthillier/gitmax/code/neuropoly/sct/sct_v6.3/bin
#export PATH=/Users/maximebouthillier/gitmax/code/neuropoly/sct/sct_v6.3/bin;$PATH

export PYTHONPATH=/Users/maximebouthillier/gitmax/code/neuropoly/sct/sct_v6.3/bin
export PATH=/Users/maximebouthillier/Anaconda/anaconda3/bin/:$PATH
### a remplace le ; par : a re-essayer!

/Users/maximebouthillier/gitmax/code/neuropoly/sct/sct_v6.3/bin/sct_qc -i ${1} -s ${3} -d ${2} -p sct_deepseg_lesion -plane sagittal -qc ${4}


