import os
import yaml
import sys
import pandas as pd
import zipfile
import math
sys.path.append('../utils')
import getopt
from feature_extraction_utils import MessageFeaturesCollection
from feature_extraction_utils import splitThread, splitMessage
from feature_extraction_utils import initializeFeatureExtractor
from feature_extraction_utils import generateBigramsList
from feature_extraction_utils import printHeaders

def usage():
        sys.stderr.write("usage: build_transitory_features.py -i|--infile=<input file> -o|--outfile=<output_data_filename")

def build_transitory_features(email_df, config, informativeBigrams):
    '''
	Open an email archive
	Split into messages
	Calculate linguistic features
	output as csv with transitory markings
	'''
    for index, row in email_df.iterrows():
        #Skip messages with no text
        if (len(row.body) > 0):
            #Read each thread
            thread = row.body

            #Split threads into messages, extract most recent,
            #build features collection
            message = splitThread(thread, config)
            #Build linguistic features which may correlate
            #with transitory marking
            featuresCollection = MessageFeaturesCollection(message, config, informativeBigrams)
            featuresCollection.print()
    return True

if (__name__ == '__main__'):
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

    config = initializeFeatureExtractor()
    #open csv storing emails archive
	#Extract metadata
    email_df = pd.read_csv(inputFile, sep='|')

    #Generate list of informative bigrams
    informativeBigrams = generateBigramsList(email_df, config, 'cat', 'fraud_waste_abuse', 20)

    with open('informativeBigrams.txt', 'w') as f:
        for b in informativeBigrams:
            print(b)
    f.close()

    printHeaders(config['fields'])

    build_transitory_features(email_df, config, informativeBigrams)
