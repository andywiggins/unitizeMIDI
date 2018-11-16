####################################################
# Renames all files to include their detected key
#
# Andy Wiggins
####################################################

import music21
import numpy as np
import os

# Set input and output paths
inPath = "GeerdesMIDI/"
outPath = "GeerdesMIDI_keys/"

# get all input 
filelist = np.array(os.listdir(inPath))

i = 1

# for each file in the inpath folder
for filename in filelist[2:]:
	
	# print filename
	print filename	

	# get the file extension
	fileExt = filename.split(".")[-1]

	# if it's midi file
	if fileExt.lower() == "mid":

		# import the score as a music21 file
		score21 = music21.converter.parse(inPath + filename)

		# Krumhasl key analysis to predict song key
		key21 = score21.analyze('Krumhansl')

		# create string of letter name + mode
		songKey = str(key21.tonic.name) + "_" + str(key21.mode)

		# cut off the .mid part of the name
		name_no_ext = filename.split(".")[0]

		new_name = name_no_ext + "-" + songKey

		# get file destination
		dst = outPath + new_name + ".MID"

		# rename the file accordingly
		os.rename(inPath + filename, dst)

		print i

		i += 1

print "done."

	

	
