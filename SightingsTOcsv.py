# Export the contents of AviSys files SIGHTING.DAT and FNotes.DAT to CSV format
# Author: Kent Fiala <Kent.Fiala@gmail.com>

Version = "2.0"

import sys
import csv
import ctypes
import os	# for getsize

# Input files
DATA_FILE = 'SIGHTING.DAT'
MASTER_FILE = 'MASTER.AVI'
PLACES_FILE = 'PLACES.AVI'
NOTE_INDEX = 'FNotes.IX'
NOTE_FILE = 'FNotes.DAT'
ASSOCIATE_FILE = 'ASSOCIAT.AVI'

# Output files
EXPORT_FILE = 'AviSys.sightings.'
NOTE_OUTPUT = 'FieldNotes.txt'

stateCode = {
'Alabama':'AL',
'Alaska':'AK',
'Arizona':'AZ',
'Arkansas':'AR',
'California':'CA',
'Colorado':'CO',
'Connecticut':'CT',
'Delaware':'DE',
'D.C.':'DC',
'Florida':'FL',
'Georgia':'GA',
'Hawaii':'HI',
'Idaho':'ID',
'Illinois':'IL',
'Indiana':'IN',
'Iowa':'IA',
'Kansas':'KS',
'Kentucky':'KY',
'Louisiana':'LA',
'Maine':'ME',
'Maryland':'MD',
'Massachusetts':'MA',
'Michigan':'MI',
'Minnesota':'MN',
'Mississippi':'MS',
'Missouri':'MO',
'Montana':'MT',
'Nebraska':'NE',
'Nevada':'NV',
'New Hampshire':'NH',
'New Jersey':'NJ',
'New Mexico':'NM',
'New York':'NY',
'North Carolina':'NC',
'North Dakota':'ND',
'Ohio':'OH',
'Oklahoma':'OK',
'Oregon':'OR',
'Pennsylvania':'PA',
'Rhode Island':'RI',
'South Carolina':'SC',
'South Dakota':'SD',
'Tennessee':'TN',
'Texas':'TX',
'Utah':'UT',
'Vermont':'VT',
'Virginia':'VA',
'Washington':'WA',
'West Virginia':'WV',
'Wisconsin':'WI',
'Wyoming':'WY'
}
provinceCode = {
'Alberta':'AB',
'British Columbia':'BC',
'Manitoba':'MB',
'New Brunswick':'NB',
'Newfoundland':'NL',	# AviSys uses 'NF'
'Northwest Terr.':'NT',
'Nova Scotia':'NS',
'Nunavut':'NU',
'Ontario':'ON',
'Prince Edward Is.':'PE',
'Quebec':'QC',			# AviSys uses 'PQ'
'Saskatchewan':'SK',
'Yukon Territory':'YT'
}

class NoteBlock:
# FNotes.DAT contains 512-byte blocks. The first block is a header. Subsequent blocks have this structure:

# If byte 0 is 00: (First block in a note)
# Offset
# 0:    Flag (00)
# 1-3:  000000
# 4-7:  Note number
# 8-505: Data
# 506-507: Number of valid bytes from offset 0 through 505
# 508-511: Index of next block


# If byte 0 is 01:  (Block that continues a note)
# 0:    Flag (01)
# 1-505: Data
# 506-507: Number of valid bytes from offset 1 through 505
# 508-511: Index of next block

# Data lines are contained in fixed-length records of 125 bytes, which span blocks
# E.g., first block contains 3 records of 125 bytes, plus the first 123 bytes of the 4th record.
# Each data line is prefixed with its length in the first byte

	def __init__(self,file,blockNumber):	# Read the specified block from FNotes.DAT
		self.file = file
		offset = blockNumber * 512
		file.seek(offset)
		block = file.read(512)
		validBytes = int.from_bytes(block[506:508],'little')
		self.next = int.from_bytes(block[508:512],'little')
		if block[0] == 0:
			self.data = block[8:validBytes]	# First block in chain
		else:
			self.data = block[1:validBytes+1]	# Any subsequent block

	def extract(self):	#	Extract the chain of blocks, and the individual records from the chain
		data = self.extractBlocks()
		output = ''
		ptr = 0
		while ptr < len(data):
			strlen = data[ptr]	# First byte has the length
			ptr += 1	# String starts in second byte
			output += data[ptr:ptr+strlen].decode('Windows-1252') + '\n'
			ptr += 124
		return output

	def extractBlocks(self):	# Extract data from this block and blocks chained to it
		data = self.data
		if self.next:
			block = NoteBlock(self.file,self.next)
			data += block.extractBlocks()
		return data

def readMaster():
#	Fill in the species name lookup table
#	MASTER.AVI contains the taxonomy in 110 byte records

#	Byte	Content
#   0		Life list mask: 20 All species have this bit; 2a species I have seen
#	1-2		Custom checklist mask (bits 0-14) (Custom checklists that include this species); bit 15: species in most recent report
#	3-4		Custom checklist seen mask
#	5-6		Species number
#	7		Common name length
#	8-43	Common name
#	44-51	State checklist mask (64 bits) (State checklists that include this species)
#	52		Genus name length
#	53-76	Genus name
#	77		Species name length
#	78-101	Species name
#	102-103	ABA bytes
#	104-109	Always 00

# ABA byte 0
# 01 ABA area species
# 00 not ABA area species

# ABA byte 1
# 01 Seen in ABA area
# 00 Not seen in ABA area


# Bytes 0-4 (Life list mask and checklist masks)
# Let 0200 be the mask for the NC checklist. Then bytes 0-4 work like this:
# 20 0000 0000  Non-NC species I have not seen anywhere; also family level entry
# 20 0200 0000  NC species that I have not seen anywhere
# 2a 0000 0000  Non-NC species I have seen somewhere but not in NC
# 2a 0000 0200  Non-NC species I have seen in NC
# 2a 0200 0000  NC species that I have seen but not in NC
# 2a 0200 0200  NC species seen in NC

	name = {}
	genusName = {}
	speciesName = {}
	try:
		master_input = open(MASTER_FILE, "rb")
	except FileNotFoundError:
		print('Error: File',MASTER_FILE,'not found.')
		raise SystemExit
	except:
		print("Error opening",MASTER_FILE,'--',sys.exc_info()[1])
		raise SystemExit

	while True:
		taxon = master_input.read(110)	# Read a record of 110 bytes
		if not taxon:
			break
		speciesNo = int.from_bytes(taxon[5:7],"little")
		name[speciesNo] = taxon[8:(8+taxon[7])].decode('Windows-1252')
		genusName[speciesNo] = taxon[53:(53+taxon[52])].decode('Windows-1252')
		speciesName[speciesNo] = taxon[78:(78+taxon[77])].decode('Windows-1252')

	master_input.close()
	return (name,genusName,speciesName)

class FileSpecs:
	def __init__(self):
		
		try:
			sighting_file = open(DATA_FILE,"rb")
		except FileNotFoundError:
			print('Error: File',DATA_FILE,'not found.')
			raise SystemExit
		except:
			print("Error opening",DATA_FILE,'--',sys.exc_info()[1])
			raise SystemExit

		header = sighting_file.read(14)
		reclen = header[12]
		if reclen == 111:
			AviSysVersion = 6
		elif reclen == 76:
			# Version 4 and 5 have same structure for SIGHTING.DAT but different sizes for PLACES.AVI		
			placesSize = os.path.getsize(PLACES_FILE)
			if placesSize == 11340:
				AviSysVersion = 4
			elif placesSize == 63450:
				AviSysVersion = 5
			else:
				print(PLACES_FILE, 'contains', placesSize, 'bytes, which is not expected for any supported AviSys version')
				raise SystemExit
		else:
			print(DATA_FILE, 'record length is', reclen, '; not a supported AviSys version')
			raise SystemExit

		sighting_file.close()

		self.version = AviSysVersion
		if AviSysVersion == 6:
			# PLACES.AVI
			self.placeLink = 37
			self.placesRecl = 39
			self.placeDivisor = 450
			# SIGHTING.DAT
			self.commentLenIndex = 28
			self.commentOffset = 29
			self.tallyIndex = 109
			self.dataLrecl = 111

		else:
			self.placeLink = 25
			self.placesRecl = 27
			if AviSysVersion == 4:
				self.placeDivisor = 80
			else:
				self.placeDivisor = 450
			
			self.commentLenIndex = 27
			self.commentOffset = 28
			self.tallyIndex = -1		# quantity field not supported before Version 6
			self.dataLrecl = 76


class Place:
	def __init__(self,placeNumber,name,link,filespecs):
		self.placeNumber = placeNumber
		self.name = name
		self.link = link
		self.table = (placeNumber-1)//(filespecs.placeDivisor)
	def __str__(self):
		return str(self.placeNumber) + ': ' + self.name + ' ' + str(self.link) + ' (table ' + str(self.table) + ')'

def readPlaces():
#	The places file (PLACES.AVI) contains fixed length records of 39 bytes
#	Bytes
#	0-1		Place number
#	6		Length of place name
#	7-36	Place name
#	37-38	Place number of linked location

	global filespecs

	output = {}

	try:
		places_input = open(PLACES_FILE,"rb")
	except FileNotFoundError:
		print('Error: File',PLACES_FILE,'not found.')
		raise SystemExit
	except:
		print("Error opening",PLACES_FILE,'--',sys.exc_info()[1])
		raise SystemExit

	while True:	#	Read all the places in the file
		place = places_input.read(filespecs.placesRecl)	# Read a record of 39 bytes
		if not place:
			break
		placeNumber = int.from_bytes(place[0:2],"little")
		if placeNumber == 0:
			continue;

		name = place[7:(7+place[6])].decode('Windows-1252')
		link = int.from_bytes(place[filespecs.placeLink:filespecs.placeLink+2],"little")
		placeInfo = Place(placeNumber,name,link,filespecs)
		output[placeNumber] = placeInfo

	places_input.close()
	# Now make the 6-level list of links for each place
	for placeNumber in output:
		place = output[placeNumber]
		links = []
		for i in range(6):
			if i == place.table:	# i is the entry for this place
				links.append(place.name)
				next = place.link	# now list the higher-level places this one is linked to
				if next == 0:
					while table < 5:
						table += 1
						links.append('')
					break
				place = output[next]
				table = place.table
			else:
				links.append('')	#	Links are null until we get to the first one
		output[placeNumber].linklist = links
	return output


class Association:
	def __init__(self,placeName,locationName,lat,lng,state,nation):
		self.placeName = placeName
		self.locationName = locationName
		self.lat = lat
		self.lng = lng
		self.state = state
		self.nation = nation


def readAssociate():
#	The hotspot association file (ASSOCIAT.AVI) contains fixed length records of 152 bytes
#	Bytes
# 0			Place len
# 1-30		AviSys place (30 chars)
# 31-33		?
# 34		locid len
# 35-41		locid
# 42		hotspot len
# 43-102 	eBird hotspot (60 chars)
# 103		lat len
# 104-115	lat
# 116-123	binary (float) lat
# 124		lng len
# 125-136	lng
# 137-144	binary (float) lng
# 145		state len
# 146-148	state
# 149		nation len
# 150-151	nation


	output = {}

	try:
		associate_input = open(ASSOCIATE_FILE,"rb")
	except FileNotFoundError:
#		print('Note: File',ASSOCIATE_FILE,'not found.')
		return output
	except:
		print("Error opening",ASSOCIATE_FILE,'--',sys.exc_info()[1])
		raise SystemExit


	while True:	#	Read all the places in the file
		association = associate_input.read(152)	# Read a record of 152 bytes
		if not association:
			break
		if len(association) != 152:
			print("Odd, length is",len(association))
		else:
			place =	association[1:1+association[0]].decode('Windows-1252')
			location = association[43:43+association[42]].decode('Windows-1252')
			lat = association[104:104+association[103]].decode('Windows-1252')
			lng = association[125:125+association[124]].decode('Windows-1252')
			state = association[146:146+association[145]].decode('Windows-1252')
			nation = association[150:150+association[149]].decode('Windows-1252')

			Info = Association(place,location,lat,lng,state,nation)
			output[place] = Info

	associate_input.close()
	return output


def readNoteIndex():
#	FNotes.IX contains fixed-length blocks.
#	The first block begins with a 32 byte descriptive header:
#	Bytes 0-3 contain 0xffffffff
#	Bytes 4-7 contain ??
#	Bytes 8-11 Number of blocks in the file
#	Bytes 12-15 Size of each block (874 bytes)
#	Bytes 16-21 ??
#	Bytes 22-25 Number of field notes in the file
#	Bytes 26-29 Number of notes per block (62)
#	The rest of the first block is empty.

#	In subsequent blocks:
#	Byte 0:	Number of valid index entries in this block
#	Index entries begin at Byte 6 and are an array of 14-byte entries

#	Index entry has block number in binary in bytes 0-3,
#	length of note number (always 5) in byte 8,
#	and note number in ascii in bytes 9-13

#	Valid index entries are grouped at the beginning of a block,
#	and the block may be padded out with non-valid, i.e., unused, entries.

	try:
		note_index = open(NOTE_INDEX,"rb")
	except FileNotFoundError:
		print('Error: File',NOTE_INDEX,'not found.')
	except:
		print("Error opening",NOTE_INDEX,'--',sys.exc_info()[1])
		raise SystemExit

	header = note_index.read(32)
	marker = int.from_bytes(header[0:4],'little')
	if marker != 4294967295:
		print('Unexpected value',marker,'at beginning of',NOTE_INDEX)
#		raise SystemExit
	numBlocks		= int.from_bytes(header[8:12],'little')		# number of 874 byte blocks (e.g., 11)
	blockSize		= int.from_bytes(header[12:16],'little')	# blocksize (874, 0x036a)
	numNotes		= int.from_bytes(header[22:26],'little')	# Number of notes (e.g., 600)
	blockFactor		= int.from_bytes(header[26:30],'little')	# Number of notes per block (62, 0x3E)

	reclen = int((blockSize-6) / blockFactor)	# 14
	if reclen != 14:
		print('Reclen was expected to be 14 but is', reclen)
		raise SystemExit
	note_index.read(blockSize - 32)	# Have already read 32 bytes of first block. Now read the rest (and discard).

	index = {}
	while True:
		block = note_index.read(blockSize)
		if not block:
			break
		numValid = block[0]
		if not numValid:
			break
#		Loop through each index entry in this block
		for ptr in range(6,blockSize,reclen):
			ix = block[ptr:ptr+reclen]
			if not ix:
				break
			blockNumber = int.from_bytes(ix[0:4],'little')
			nchar = ix[8]
			ascii = ix[9:9+nchar].decode('Windows-1252')
			index[int(ascii)] = blockNumber

			numValid -= 1
			if not numValid:
				break	# Finished with all valid entries this block
	note_index.close()
	return index

def integrateNote(comment,fieldnoteText):
#	Integrate the comment and field note.
#	If the observation was imported from eBird via http://avisys.info/ebirdtoavisys/
#	the AviSys comment may duplicate the beginning of the eBird comment.
#	Here we remove duplication.
	if fieldnoteText != '':	# If there is a field note
		work = comment	# Working copy of the comment
		keepLen = 0	# Length of the beginning of the comment to keep, if any duplication
		ptr = 0	# Where we are in the comment
		hasAttributes = True if ptr < len(work) and work[ptr] == '/' else False
		while hasAttributes:	# There are AviSys attributes at the beginning of comment
			attributeLen = 3 if ptr+2 < len(work) and comment[ptr+2] == '/' else 2	# Attributes are either 2 or 3 bytes
			ptr += attributeLen	# Bump ptr past this attribute
			while ptr < len(work) and work[ptr] == ' ':	# and past any trailing blanks
				ptr += 1
			hasAttributes = True if ptr < len(work) and work[ptr] == '/' else False	# Check if there is another attribute
		if ptr < len(work) and work[ptr] == '(':	# If the first part of comment is parenthesized, skip over it
			ptr += 1
			while ptr < len(work) and work[ptr] != ')':
				ptr += 1
			if work[ptr] == ')':
				ptr += 1
				while ptr < len(work) and work[ptr] == ' ':
					ptr += 1
		keepLen = ptr	# Keep at least this much of the comment
		work = work[ptr:]	# Check if this part of the comment is duplicated in the field note

		text = fieldnoteText
		linend = fieldnoteText.find('\n')	# end of first line
		# If the first line contains ' :: ' it is probably a heading so skip that line
		if fieldnoteText[0:linend].find(' :: ') > 0:
			text = fieldnoteText[linend+1:]
		linend = text.find('\n')	# end of second line
		text = text[0:linend] + ' ' + text[linend+1:]	# Examine the first two lines as one line

		ptr = 0
		while ptr < len(text) and text[ptr] == ' ':	# Skip over any leading blanks
			ptr += 1
		if len(work):	# If we have a comment
			if text[ptr:ptr+len(work)] == work:	# If the comment is identical to the beginning of the field note
				if keepLen:	# Discard the comment text. Keep only the comment prefix (attributes and/or parenthesized content)
					comment = comment[0:keepLen]
				else:
					comment = ''	# Discard the entire comment.
		comment = comment.strip() + ' ' + fieldnoteText	# Concatenate comment prefix and field note.
		comment = comment.strip(' \n')
	return comment


#########################################################################################################
######################################## The program starts here ########################################
#########################################################################################################
print('SightingsTOcsv version ' + Version)
outArray = []
noteDict = {}
# ref https://stackoverflow.com/questions/55172090/detect-if-python-program-is-executed-via-windows-gui-double-click-vs-command-p
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
process_array = (ctypes.c_uint * 1)()
num_processes = kernel32.GetConsoleProcessList(process_array, 1)

if len(sys.argv) < 2:	# If no command-line argument
	if num_processes <= 2:	# Run from double-click
		outputType = 'eBird'
	else:					# Run from command line
		outputType = 'AviSys'
else:
	outputType = sys.argv[1]

if outputType.lower() == 'avisys':
	outputType = 'AviSys'
elif outputType.lower() == 'ebird':
	outputType = 'eBird'
elif outputType.lower() == 'myebird':
	outputType = 'MyEBirdData'
else:
	print("Please specify either AviSys, eBird, or MyEBird")
	raise SystemExit

filespecs = FileSpecs()

try:
	FNotes = open(NOTE_FILE,"rb")
except FileNotFoundError:
	print('Error: File',NOTE_FILE,'not found.')
	raise SystemExit
except:
	print("Error opening",NOTE_FILE,'--',sys.exc_info()[1])
	raise SystemExit

noteIndex = readNoteIndex()
(name,genusName,speciesName) = readMaster()
places = readPlaces()

association = readAssociate()

try:
	sighting_file = open(DATA_FILE,"rb")
except FileNotFoundError:
	print('Error: File',DATA_FILE,'not found.')
	raise SystemExit
except:
	print("Error opening",DATA_FILE,'--',sys.exc_info()[1])
	raise SystemExit

# Format of SIGHTING.DAT
# Header record
# 0-3 ffffffff
# 8-11 Number of records
# 12   Reclen   (6F, 111)
# padded to 111 bytes
#
# Sighting record
# 0-3 always 00000000
# 4-5 Species number
# 6-9 Fieldnote number
# 10-13 Date
# 14-15 Place number
# 16 Country len
# 17-19 Country
# 20-23 nation bits  e.g. 0d200800 for lower 48
# 24-27 always 00000000
# 28 Comment len
# 29-108 Comment
# 109-110 Count
#
# Update 2021 08 14: 
# I figured out how bytes 0-3 are used. 
# For valid sighting records, the first 4 bytes are zeroes.
# Corrupted records can be kept in the file but ignored;
# they are stored in a linked list where bytes 0-3 are the link pointer.
# The last record in the linked list has ffffffff in bytes 0-3.
# The first four bytes of the header (first four bytes of the file) point to the beginning of the linked list of corrupt records.
# If there are no corrupt records, the file begins with ffffffff.
# The value of the link pointer is the record number; thus multiply by 111 to get the byte offset in the file.
# To ignore invalid records, skip any record that does not begin with 00000000.
#
# Nation bits:
# 00000100  Australasia
# 00000200  Eurasia
# 00000400  South Polar
# 00000800  [AOU]
#
# 00010000  [Asia]
# 00020000  Atlantic Ocean
# 00040000  Pacific Ocean
# 00080000  Indian Ocean
#
# 00100000  [Oceanic]
# 00200000  North America
# 00400000  South America
# 00800000  Africa
#
# 01000000  [ABA Area]
# 02000000  [Canada]
# 04000000  [US]
# 08000000  [Lower 48]
#
# 10000000  [West Indies]
# 20000000  [Mexico]
# 40000000  [Central America]
# 80000000  [Western Palearctic]

header = sighting_file.read(filespecs.dataLrecl)	# Read header record
marker = int.from_bytes(header[0:4],'little')
corruptRecords = 0

EXPORT_FILE += outputType+'.csv'
try:
	CSV = open(EXPORT_FILE,'w', newline='')
except PermissionError:
	print('Denied permission to open',EXPORT_FILE,'-- Maybe it is open in another program? If so, close it and try again.')
	raise SystemExit
except:
	print('Error opening',EXPORT_FILE,'--',sys.exc_info()[1])
	raise SystemExit

try:
	noteOut = open(NOTE_OUTPUT,'w', newline='')
except PermissionError:
	print('Denied permission to open',NOTE_OUTPUT,'-- Maybe it is open in another program? If so, close it and try again,')
	raise SystemExit
except:
	print('Error opening',NOTE_OUTPUT,'--',sys.exc_info()[1])

nrecs = int.from_bytes(header[8:12],"little")

recordCount = 0
while True:
	sighting = sighting_file.read(filespecs.dataLrecl)
	if not sighting:
		break
	recordCount+=1
	corruptPointer = int.from_bytes(sighting[0:4],'little')
	corruptedRecord = corruptPointer != 0
	speciesNo = int.from_bytes(sighting[4:6],'little')
	fieldnote = int.from_bytes(sighting[6:10],'little')
	if fieldnote:
		block = NoteBlock(FNotes,noteIndex[fieldnote])
		fieldnoteText = block.extract()
		noteDict[recordCount] = fieldnoteText
	else:
		fieldnoteText = ''
	fieldnoteText = fieldnoteText.rstrip(' \n')
	date = int.from_bytes(sighting[10:14],'little')
	day = date % 100
	month = (date // 100) % 100
	year = (date // 10000) + 1930
	date = str(month) + '/' + str(day) + '/' + str(year)
	sortdate = str(year) + '-' + str(month).rjust(2,'0') + '-' + str(day).rjust(2,'0')
	place = int.from_bytes(sighting[14:16],'little')
	countryLen = sighting[16]
	country = sighting[17:19].decode('Windows-1252')
	
	commentLen = sighting[filespecs.commentLenIndex]
	shortComment = sighting[filespecs.commentOffset:filespecs.commentOffset+commentLen].decode('Windows-1252').strip()

	comment = integrateNote(shortComment,fieldnoteText)

	if outputType in ['eBird','MyEBirdData']:
		comment = comment.replace("\n"," ")

	if filespecs.tallyIndex > 0:
		tally = int.from_bytes(sighting[filespecs.tallyIndex:filespecs.tallyIndex+2],'little')
	else:
		tally = 1

	if speciesNo in name:
		commonName = name[speciesNo]
	else:
		commonName = '?'
		if not corruptedRecord:
			print("No name found for species number", speciesNo)
			raise SystemExit

	if place not in places:
		if not corruptedRecord:
			print("Place", place, "is not set")
			raise SystemExit
		else:
			location = 'Unknown location'
	else:
		linkList = places[place].linklist
		location = linkList[0] if linkList[0] != '' else \
			linkList[1] if linkList[1] != '' else \
			linkList[2] if linkList[2] != '' else \
			linkList[3] if linkList[3] != '' else \
			linkList[4] if linkList[4] != '' else \
			linkList[5] if linkList[5] != '' else \
			linkList[6]

		if outputType == 'eBird' and location in association:
			location = association[location].locationName	# Use associated eBird location name instead of AviSys place name

	if len(linkList) > 3:	# linkList will be short for an unlinked location
		if country == 'US':
			state = stateCode[linkList[3]]
		elif country == 'CA':
			state = provinceCode[linkList[3]]
		else:
			state = linkList[3]
	else:
		state = ''

	if len(linkList) > 2:
		county = linkList[2]
	else:
		county = ''

	if corruptedRecord:
		corruptRecords += 1
		print('Corrupt record found:',commonName,location,date,state,country,comment)
	else:
		outArray.append([commonName,genusName[speciesNo],speciesName[speciesNo],tally,comment,location,sortdate,date,state,country,speciesNo,recordCount,shortComment,county,speciesNo])

def sortkey(array):
	return array[6]+array[5]	# date+location

outArray.sort(key=sortkey)

if outputType == 'eBird':
	csvFields = ['Common name','Genus','Species','Species Count','Species Comment','Location','Lat','Lng','Date','Start time','State','Country','Protocol','N. Observers','Duration','Complete','Distance','Area','Checklist comment','Important: Delete this header row before importing to eBird']
elif outputType == 'MyEBirdData':
	csvFields = ['Submission ID','Common Name','Scientific Name','Taxonomic Order','Count','State/Province','County','Location ID','Location','Latitude','Longitude','Date','Time','Protocol','Duration (Min)','All Obs Reported','Distance Traveled (km)','Area Covered (ha)','Number of Observers','Breeding Code','Observation Details','Checklist Comments','ML Catalog Numbers']
else:
	csvFields = ['Common name','Genus','Species','Place','Date','Count','Comment','State','Nation','Blank','SpeciesNo']

CSVwriter = csv.DictWriter(CSV,fieldnames=csvFields)
CSVwriter.writeheader()

# Assign a "subid", i.e., a checklist number, to each unique date-location combination.
# If all counts for a subid are "1", replace them with "X".
subid = 0
currentKey = " "
rowcounter = 0
startRow = 0
eX = True if outputType != 'AviSys' else False
for row in outArray:
	key = row[6]+row[5]
	if key != currentKey:	# New date-location combination
		if eX and subid:	# If all counts in previous subid were "1", set them to "X"
			for i in range(startRow,rowcounter):
				outArray[i][3] = 'X'
		subid += 1	# unique subid for each date-location combination

		startRow = rowcounter
		currentKey = key
		eX = True if outputType != 'AviSys' else False
	if row[3] > 1:	# Count
		eX = False	# Make note that there was a count > 1s
	outArray[rowcounter].append(subid)	# should be index 15
	rowcounter += 1					

if outputType == 'eBird':
	for row in outArray:
		CSVwriter.writerow({'Common name':row[0],'Genus':row[1],'Species':row[2],'Species Count':row[3],'Species Comment':row[4],
			'Location':row[5],'Lat':'','Lng':'','Date':row[7],'Start time':'','State':row[8],'Country':row[9],
			'Protocol':'historical','N. Observers':1,'Duration':'','Complete':'N','Distance':'','Area':'','Checklist comment':'Imported from AviSys'})

elif outputType == 'MyEBirdData':
	for row in outArray:
		CSVwriter.writerow({'Submission ID':row[15],'Common Name':row[0],'Scientific Name':row[1]+' '+row[2],
			'Taxonomic Order':row[14],'Count':row[3],'State/Province':row[9]+'-'+row[8],'County':row[13],'Location ID':'',
			'Location':row[5],'Latitude':'','Longitude':'','Date':row[6],'Time':'','Protocol':'historical',
			'Duration (Min)':'','All Obs Reported':0,'Distance Traveled (km)':'','Area Covered (ha)':'',
			'Number of Observers':'1',
			'Breeding Code':'',
			'Observation Details':row[4],
			'Checklist Comments':'Imported from AviSys',
			'ML Catalog Numbers':''})
		
else:
	for row in outArray:
		dateVal = row[6].split('-')
		date = str(int(dateVal[1]))+'/'+str(int(dateVal[2]))+'/'+dateVal[0]

		CSVwriter.writerow({'Common name':row[0],'Genus':row[1],'Species':row[2],'Place':row[5],'Date':date,'Count':row[3],'Comment':row[4],
			'State':row[8],'Nation':row[9],'Blank':'','SpeciesNo':row[9]})

# Write all field notes to a file
# The entry for each note begins with species name -- date -- place on the first line, followed by a blank line.
# The text of the field note follows
# The note is terminated by a line of 80 equal signs (which is something that could not be part of the actual note).
# Note: If AviSys type output, the place is the AviSys place. If eBird type output, the associated eBird location, if any, is used as the place.
for row in outArray:
	recordNo = row[11]
	if recordNo in noteDict:
		shortComment = row[12]
		noteOut.write(row[0] +' -- '+ row[6] +' -- '+  row[5] + '\n\n')
		if len(shortComment):
			noteOut.write( 'Short comment: ' + shortComment + '\n\n')
		noteOut.write(noteDict[recordNo] + '\n' + '==========================================================================================\n')

sighting_file.close()
noteOut.close()
CSV.close()

if recordCount != nrecs:
	print('Should be', nrecs, 'records, but counted', recordCount)
else:
	print(nrecs,"records processed","from AviSys version", filespecs.version,"data.")
if corruptRecords:
	if corruptRecords == 1:
		print('File', DATA_FILE, 'contains one corrupt record, which has been ignored. ')
		print('To remove it from AviSys, run Utilities->Restructure sighting file.')
	else:
		print('File', DATA_FILE, 'contains', corruptRecords, 'corrupt records, which have been ignored. ')
		print('To remove them from AviSys, run Utilities->Restructure sighting file.')
	print(nrecs-corruptRecords, 'records are valid.')
