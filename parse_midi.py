#######################
# Andy Wiggins
# MIDI 2 unitized CSV
#######################

from mido import MidiFile
import os
import numpy as np
import csv
import music21
import shutil

class Score:

	def __init__(self, name, notes, length, key):
		self.name = name
		self.notes = notes
		self.length = length
		self.key = key

	def __str__(self):
		s = "----score----"
		s += "\nname: " + str(self.name)
		s += "\nnotes: "
		for n in self.notes:
			s += str(n)
			s += "\n"
		s = s[:-1]
		s += "\nlength: " + str(self.length) + " measures"
		s += "\nlength: " + str(self.key)
		return s

class Note:

	def __init__(self, pitch, start, duration, channel):
		self.pitch = pitch
		self.start = start
		self.duration = duration
		self.channel = channel

	def __str__(self):
		s="\t--note--"
		s += "\n\tpitch: " + str(self.pitch)
		s += "\n\tstart: " + str(self.start)
		s += "\n\tduration: " + str(self.duration)
		s += "\n\tchannel: " + str(self.channel)
		return s

class HarmUnit:

	def __init__(self, chordNotes, chordName):
		self.chordNotes = chordNotes
		self.chordName = chordName
		
def pitchStr(note):
	'''returns the string of the note name given a midi note val'''
	alpha = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
	octave = str((note // 12) - 1)
	noteIndex = note % 12
	return alpha[noteIndex] + octave

def noteinKey(note,key):
	'''returns an int in [1,11] for a note given a key'''

def getKeyFromName(filename):
	'''retrieves the song key and mode from the title of the midi file'''

	# split name by T- to get the key separated out, split at . remove file ext
	# split at _ to seperate key letter and mode

	# take off ".mid"
	noex = filename[:-4]

	# major or minor
	mode = noex[-5:]

	letters = ["A","B","C","D","E","F","G"]

	# no sharp or flat
	if noex[-7] in letters:
		keyLet = noex[-7]

	else:
		keyLet = noex[-8:-6]

	key = [keyLet,mode]

	# key = filename.split("T-")[1].split(".")[0].split("_")
	return key

def parseMidi(filename):
	'''creates a score object for a midi file'''

	# load the midi file
	mid = MidiFile(filename)

	# list of started notes
	startedNotes = {}

	# list of completed notes
	notes = []

	# set bool for song started
	songStarted = False

	# current measure number
	currentMeasureNumber = 0

	# get the ticks per unit
	# unit is the denominator of note value
	# ex: 8 for eigth note, 16 for sixteenth note
	ticksPerMeasure = mid.ticks_per_beat * 4.0

	# set a default tempo
	tempo = 500000

	# start with blank name
	name = ""
	nameSet = False

	# iterate through all messages in the midi file
	for message in mid:

		mess = message.dict()

		###################
		# print mess
		###################

		dtime = mess['time']
		mtype = mess['type']

		# only after the song has started do we count ticks and units
		if songStarted:

			# convert dtime (seconds) to ticks via tempo (microseconds/beat) and ticks per beat
			dticks = int(round(dtime * 1000000 * (1.0 / tempo) * mid.ticks_per_beat))	

			# update current measure number based on the number of ticks that passed
			currentMeasureNumber += (dticks / ticksPerMeasure)

		# check if the tempo changed and update
		if mtype == 'set_tempo':
			tempo = mess['tempo']

		# store the track name, if in midi file
		elif mtype == 'lyrics' and nameSet == False:
			name = mess['text']
			nameSet = True

		# if the message is a non zero velocity note on, store it in started notes
		elif mtype == 'note_on' and mess['velocity'] != 0:

			# start the song ticker
			if not songStarted:
				songStarted = True

			# get the parameters of the note
			# duration is zero till we have a note off
			pitch = mess['note']
			# round it 8 decimal places
			start = round(currentMeasureNumber,8)
			duration = 0
			channel = mess['channel']

			# get the dict key
			key = (channel,pitch)

			# if the key is not in the dictionary
			if key not in startedNotes.keys():

				# create an empty list in the dict for this key
				startedNotes[key] = []

			# append the new note 
			startedNotes[key].append(Note(pitch,start,duration,channel))

		# if the message is a note off, find and remove the started note,
		# compute duration, and store the output note 
		elif mtype == 'note_off' or (mtype == 'note_on' and mess['velocity'] == 0):

			# get the parameters of the note
			pitch = mess['note']
			end = currentMeasureNumber
			channel = mess['channel']

			# get the dict key
			key = (channel,pitch)

			# if the key is not in the dict, skip this message
			# theres no note to turn off
			if key not in startedNotes.keys():
				continue

			# get the list of started notes with the key
			noteList = startedNotes[key]

			# get the first note from the list 
			n = noteList.pop(0)

			# if the note list is empty, remove the key from the dict
			if noteList == []:

				# delete the key
				del startedNotes[key]

			# compute and store its duration
			# round 8 decimal places
			n.duration = round(end - n.start,8)

			# add the completed note to completed notes
			notes.append(n)

	# at the end, current measure number is the length of the score in whole notes
	length = currentMeasureNumber

	# get key from file name
	songKey = getKeyFromName(filename)

	# create string of letter name + mode
	# songKey = songKey[0] + " " + songKey[1]

	# return a new score object
	return Score(name,notes,length,songKey)

def getChord(notes,key):

	# if the note set is empty
	if len(notes) == 0 or len(notes) == 1:

		# assign NC (no chord) as the chord name
		chordName = "NC"

	else:

		# create the music21 chord from the note name list
		chord = music21.chord.Chord(notes)

		# get the quality of the chord (major, minor, diminished, augmented)
		# as well as the root and the bass
		quality = chord.quality
		root = chord.root()
		bass = chord.bass()

		# if the quality is missing, we don't have a third, basically
		if quality == "other":

			# case to see if there's a fifth
			if chord.semitonesFromChordStep(5) == 7:
				# is there a 4th also?
				if chord.semitonesFromChordStep(4) == 5:				
					# with a 1 4 5 we have a sus4 chord
					q = "sus4"
				# if not, is there a 2nd?
				elif chord.semitonesFromChordStep(2) == 2:
					# with a 1 2 5 we have a sus2 chord
					q = "sus2"
				# if neither of these sus chords, call it a 5 chord
				else:
					# set the quality tag to "5"
					q = "5"

			else:
				# quality = other but no 5? it's some weird chord we can't name...
				q = "none"

		# if it's built on a major triad
		elif quality == "major":

			# if theres a major 7th
			if chord.semitonesFromChordStep(7) == 11:
				q = "maj7"
			# if theres a minor 7th
			elif chord.semitonesFromChordStep(7) == 10:
				q = "7"
			# if theres no seven, or some weird 7
			else:
				# set quality tag to maj
				q = "maj"

		# minor
		elif quality == "minor":

			# if theres a major 7th
			if chord.semitonesFromChordStep(7) == 11:
				q = "minmaj7"
			# if theres a minor 7th
			elif chord.semitonesFromChordStep(7) == 10:
				q = "min7"
			# if theres no seven, or some weird 7
			else:
				# set quality tag to min
				q = "min"

		# diminished
		elif quality == "diminished":

			# if theres a minor 7th
			if chord.semitonesFromChordStep(7) == 10:
				# half diminished 7th chord
				q = "hdim7"
			# if theres a dim 7th
			elif chord.semitonesFromChordStep(7) == 9:
				q = "dim7"
			# if theres no seven, or some weird 7
			else:
				# set quality tag to dim
				q = "dim"

		# augmented
		elif quality == "augmented":
			# we dont really care about 7s in augmented chords
			q = "aug"

		else:
			# what kind of chord is this?!?
			q = "none"

		# if we couldnt get a good quality tag return no chord
		if q == "none":
			chordName = "NC"

		# else put together chord name with root and bass
		else:
			#######
			root_num = music21.interval.notesToChromatic(music21.note.Note(key[0]), root).mod12
			bass_num = music21.interval.notesToChromatic(root, bass).mod12
			########

			# get root as number in terms of song key
			# chordName = root.name + q + "/" + bass.name
			chordName = str(root_num) + ":" + q + "/" + str(bass_num)

	# return the chord name string
	return chordName

def getHarmony(score,unitSize):
	'''gets unitized harmony for a score, given a unit size'''

	# get the notes of the score
	notes = score.notes

	songKey = score.key

	# create a list of notes still on
	stillOn = []

	# round length up to nearest whole note
	length = int(np.ceil(score.length))

	# the unitized score to be output
	unitized = []

	# iterate through units
	for unitIndex in np.arange(0,length,unitSize):

		# find all notes with start in this unit
		currUnit = filter(lambda n: n.start >= unitIndex and n.start < unitIndex + unitSize, notes)

		# add any notes still on to current unit
		currUnit += stillOn

		# clear the still on list
		stillOn = []

		# create a empty chord notes dictionary
		unitNotes = {}

		# for each note on in the current unit
		for note in currUnit:	

			# if the note did not end in this unit
			if note.duration > unitSize:

				# subtract unitSize from its duration
				newDuration = note.duration - unitSize

				# create a new note with the updated duration and add it to still on
				stillOn.append(Note(note.pitch,note.start,newDuration,note.channel))

				# set the note's duration in the current unit to the unit size
				currDuration = unitSize

			# if the newDuration is negative, the note doesn't occupy the whole unit
			# the note doesn't get added to still on
			# and the notes current duration is its full duration
			else:

				# the note's duration ends in the unit
				currDuration = note.duration

			# create dictionary key for note with channel,pitch
			dictKey = (note.channel,note.pitch)

			# if we've seen a note with this key
			if dictKey in unitNotes.keys():

				# increase its duration accordingly
				unitNotes[dictKey] += currDuration

			else:
				# otherwise, add the note to the chordNotes dict
				unitNotes[dictKey] = currDuration

		#create an empty list of chord notes
		chordNotes = []

		# for each key in the unit notes dictionary
		for k in unitNotes.keys():

			# get the channel and pitch from the key
			# get duration from dict entry
			# use start of unit as start of note
			channel = k[0]
			pitch = k[1]
			duration = unitNotes[k]
			start = unitIndex

			# if the duration is greater than or equal to half the unit size
			if duration >= (unitSize / 2.0):

				# add a new note with its cumulative duration in the current unit to the chord note list
				chordNotes.append(Note(pitch,start,duration,channel))	

		# change chordNotes to be just the pitches
		chordNotes = map(lambda n: n.pitch, chordNotes)

		# remove duplicates by casting to a set and back to a list
		chordNotes = list(set(chordNotes))

		# sort notes low to high
		chordNotes.sort()

		# find the chord for the list of chord note pitches
		# chord name works better when pitches are sorted low -> high
		chordName = getChord(chordNotes,songKey)

		# change chordNotes to be just the pitch names
		chordNotes = map(lambda p: music21.pitch.Pitch(p).nameWithOctave, chordNotes)

		chordNotes = " ".join(chordNotes)

		# create a new harmony unit with the notes and the chord name
		newHarmUnit = HarmUnit(chordNotes,chordName)

		# append the chord to the unitzed list
		unitized.append(newHarmUnit)

	# return the unitized list
	return unitized

def getMelody(score,unitSize):

	# unit size of 1/16 note to match sibelius settings
	# treat melody like monosynth, new note will overwrite previous note
	# choose the longest new note first
	# if none, choose the one note still one
	# decrement the chosen note's duration by the unit size and store in still on if duration > 0.
	# if none, write unit as rest and clear note still on

	# get the notes of the score
	notes = score.notes

	# extract just the melody notes of the score
	# ASSUME the melody is on channel 3 (this is tue for three provided examples)
	melNotes = filter(lambda n: n.channel == 3, notes)

	# round length up to nearest whole note
	length = int(np.ceil(score.length))

	# create a place to store a note that's still on
	stillOn = 0

	# the unitized melody to be output
	# (a list of strings)
	unitized = []

	# iterate through units
	for unitIndex in np.arange(0,length,unitSize):

		# find all notes with start in this unit
		newNotes = filter(lambda n: n.start >= unitIndex and n.start < unitIndex + unitSize, melNotes)

		# if newnotes contains at least 2 notes
		if len(newNotes) > 1:

			# sort new notes by duration (large to small) first then by start (small to large)
			newNotes = sorted(newNotes, key=lambda n: (-n.duration, n.start))

			# chosen note is the first note in the newNotes list
			chosenNote = newNotes[0]

			# if the chosen note is longer than the unit
			if chosenNote.duration > unitSize:

				# subtract unit size to get the new duration
				newDuration = chosenNote.duration - unitSize

				# set still on to be a new note with updated duration
				stillOn = Note(chosenNote.pitch, chosenNote.start, newDuration, 3)

			# if the note ends this unit 
			else:

				# reset still on to 0
				stillOn = 0

			# append the chosen note to the unitzed melody
			unitized.append(pitchStr(chosenNote.pitch) + ":+")

		# otherwise, if the new notes list is 1 note long, choose it as the new note
		elif len(newNotes) == 1:

			# chosen note is the only note in the newNotes list
			chosenNote = newNotes[0]

			# if the chosen note is longer than the unit
			if chosenNote.duration > unitSize:

				# subtract unit size to get the new duration
				newDuration = chosenNote.duration - unitSize

				# set still on to be a new note with updated duration
				stillOn = Note(chosenNote.pitch, chosenNote.start, newDuration, 3)

			# if the note ends this unit 
			else:

				# reset still on to 0
				stillOn = 0

			# append the chosen note to the unitzed melody
			unitized.append(pitchStr(chosenNote.pitch) + ":+")

		# otherwise, the newNotes list is empty, so check if there's a note still on to add
		elif stillOn != 0:

			# chosen note is the still on note
			chosenNote = stillOn

			# if the chosen note is longer than the unit
			if chosenNote.duration > unitSize:

				# subtract unit size to get the new duration
				newDuration = chosenNote.duration - unitSize

				# set still on to be a new note with updated duration
				stillOn = Note(chosenNote.pitch, chosenNote.start, newDuration, 3)

			# if the note ends this unit 
			else:

				# reset still on to 0
				stillOn = 0

			# append the chosen note to the unitzed melody
			unitized.append(pitchStr(chosenNote.pitch) + ":-")

		# there were no new notes and no notes still on, so we rest
		else:
			
			# append a 0 for the unit to represent a rest
			unitized.append("0")

	return unitized

def createHarmonyCSV(filename,units,unitSize,songName,songKey):

	# create an empty array
	arr = []

	# append the score info and unit size
	arr.append([songName,songKey,"unit size: "+str(unitSize),""])

	# add an empty row
	arr.append(["","","",""])

	# add row labels
	arr.append(["unit number","global index","chord name","notes in unit"])

	# for each index in unit
	for i in range(len(units)):

		# get the harmony unit at that index
		hUnit = units[i]

		# get the notes in the chord
		notes = hUnit.chordNotes

		# get the chord name
		chord = hUnit.chordName

		# create a row with index, chord, notes
		row = [str(i),str(i*unitSize + 1),chord,notes]

		# add the row to array
		arr.append(row)

	# transpose the array
	arr = np.transpose(arr)

	# open a file with the filename
	with open(filename, "wb") as f:

		# create a csv writer object
		writer = csv.writer(f)

		# write the array as row
		writer.writerows(arr)

def createMelodyCSV(filename,units,unitSize,songName,songKey):

	# create an empty array
	arr = []

	# append the score info and unit size
	arr.append([songName,songKey])
	arr.append(["unit size: ",str(unitSize)])
	arr.append(["+ for note onset","- for note continuation"])
	arr.append(["0 for rest",""])

	# add an empty row
	arr.append(["",""])

	# add row labels
	arr.append(["unit number","melody note"])

	# for each index in unit
	for i in range(len(units)):

		# get the meldoy unit at that index
		mUnit = units[i]

		# create a row with index, chord, notes
		row = [str(i),mUnit]

		# add the row to array
		arr.append(row)

	# transpose the array
	arr = np.transpose(arr)

	# open a file with the filename
	with open(filename, "wb") as f:

		# create a csv writer object
		writer = csv.writer(f)

		# write the array as row
		writer.writerows(arr)

def main():

	HARMONY = True
	MELODY = False

	# # delete the out directory
	# shutil.rmtree('../out', ignore_errors=True)

	# Set path to input midi files
	inPath = 'GeerdesMIDI_keys/'

	# get all input 
	filelist = np.array(os.listdir(inPath))

	# counter
	i = 0

	# for each file in the filelist
	for f in filelist:

		print f
		print

		# get the file extension
		fileExt = f.split(".")[-1]

		# if it's midi file
		if fileExt.lower() == "mid":

			#get the filename:
			filename = inPath + f

			# parse the file to create a score
			print "Parsing MIDI file..."
			score = parseMidi(filename)

			# get the song name and key from score object
			songName = score.name
			songKey = score.key
			songKey = songKey[0] + " " + songKey[1]

			# unitsizes array
			# 1/16, 1/8, 1/4, 1/2, 1, 2, 4
			################# PUT THIS BACK ###################
			unitSizes = [0.25,0.5,0.75,1,1.5,2]
			###################################################


			# for each unit size
			for unitSize in unitSizes:

				print unitSize

				# MELODY

				if MELODY:
				
					# get the melody units
					melodyUnits = getMelody(score,unitSize)

					# create the output path if it doesn't exist
					mOutPath = "out/melody/" + str(unitSize) + "/"
					if not os.path.exists(mOutPath):
						os.makedirs(mOutPath)

					# set the full filename to save the melody data to
					mFullFilename = mOutPath + "".join(f.split(".")) + ".csv"

					# write the melody csv
					createMelodyCSV(mFullFilename,melodyUnits,unitSize,songName,songKey)

				# HARMONY

				if HARMONY:

					# get the harmony units, given the score and unit size
					harmonyUnits = getHarmony(score,unitSize)

					# create the output path if it doesn't exist
					hOutPath = "out/harmony/" + str(unitSize) + "/"
					if not os.path.exists(hOutPath):
						os.makedirs(hOutPath)

					# set the full filename to save the harmony data to
					hFullFilename = hOutPath + "".join(f.split(".")) + ".csv"

					# write the harmony csv
					createHarmonyCSV(hFullFilename,harmonyUnits,unitSize,songName,songKey)

				
			# move the file
			dst = "done/"
			if not os.path.exists(dst):
				os.makedirs(dst)
			os.rename(filename, dst + f)

			i += 1
			print i


if __name__ == "__main__": main()
