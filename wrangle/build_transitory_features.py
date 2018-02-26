import os
import yaml
import sys
import pandas as pd
import zipfile
import simplejson as json
import math
from wrangle_utils import remove_non_ascii_characters
from wrangle_utils import containsPII
from wrangle_utils import create_df
from wrangle_utils import initialize_wrangle_config #Do all the initialization of lookup tables one time
import getopt
from feature_extraction_utils import MessageFeaturesCollection
from feature_extraction_utils import splitThread, splitMessage
from feature_extraction_utils import initializeFeatureExtractor


def usage():
	sys.stderr.write("usage: build_transitory_features.py -i|--infile=<input file> -o|--outfile=<output_data_filename")

def build_transitory_features(config):
	'''
	Open an email archive
	Split into messages
	Calculate linguistic features
	output as csv with transitory markings
	'''

	#Get and parse command line args
	inputFile = 'Master_df.bsv' #Defaults for input and output file
	outputFile = 'output.bsv'

	try:
		opts, args = getopt.getopt(sys.argv[1:], "i:o:h?", ["--infile=", "--outfile=", "--help"])
	except getopt.GetoptError as err:
		#Exit if can't parse args
		usage()	
		sys.exit(2)
	for o, a in opts:
		if (o == '-h' or o == '-?'):
			usage()
			exit(0)
		elif o in ('-i', '--infile'):
			inputFile = a
		elif o in ('-o', '--outfile'):
			outputFile = a
		else:
			sys.stderr.write("Unrecognized option: {}\n".format(o))
			usage()
			exit(2)


	#open csv storing emails archive
	#Extract metadata

	email_df = pd.read_csv(inputFile, sep='|')

	#Generate list of informative bigrams
	#informativeBigrams = generateBigramsList(email_df)

	for index, row in email_df.iterrows():
		#Skip messages with no text
		if (len(row.body) > 0):

			#Read each thread
			thread = row.body

			#Split threads into messages, extract most recent, build features collection
			message = splitThread(thread, config)
			#Build linguistic features which may correlate with transitory marking
			featuresCollection = MessageFeaturesCollection(message, config)
			print(featuresCollection._taggedSentences)
		break

				
	#Output as csv

	return True

if (__name__ == '__main__'):
	config = initializeFeatureExtractor()
	build_transitory_features(config)
