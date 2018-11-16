import os
import numpy as np


# Set input and output paths
inPath = "GeerdesMIDI/"
outPath = "GeerdesMIDI2/"

# get all input 
filelist = np.array(os.listdir(inPath))

i = 1

# for each file in the inpath folder
for filename in filelist:

	if filename.split(".")[-1] == "MID":

		# cut off the .mid part of the name
		name_no_ext = filename.split(".")[0]
		
		# if name ends in _E, it's the composed ending version that we don't want
		if name_no_ext[-2:] != "_E":

			# get file destination
			os.rename(inPath + filename, outPath + filename)

			print i

			i += 1


