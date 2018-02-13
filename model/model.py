#---------------------------------------------------------------------------------#
# Read a pandas dataframe of emails, and train a text categorizer on them         #
# Write out results in pickle files to feed visualizations.                       #
#---------------------------------------------------------------------------------#
import pandas as pd 
import sys
import getopt
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from model_utils import remove_empty_emails
from model_utils import train_test_set
from model_utils import create_doc_matrices
from model_utils import create_naive_bayes
from model_utils import NB_results
from model_utils import create_informative_terms

def usage():
	sys.stderr.write("usage: python model.py [-d|--datafile= <datafile>] [-h|-?]")

def model():
	'''
		model(): reads in csv file specified on command line with -d option,
		filters emails with no body,
		adds personal categorical variable
		divides into train, dev-test, and test
		converts to term X doc matrix
		trains naive bayes classifier on matrix
		runs classifier against dev-test data
		reports output.
	'''
	#Get and parse command line args
	try:
		opts, args = getopt.getopt(sys.argv[1:], "d:h?", ["--datafile=", "--help"])
	except getopt.GetoptError as err:
		#Exit if can't parse args
		usage()	
		sys.exit(2)
	for o, a in opts:
		if (o == '-h' or o == '-?'):
			usage()
			exit(0)
		elif o in ('-d', '--datafile'):
			dfPath = a
		else:
			assert False, "model.py unhandled option: {}".format(o)

	email_df = pd.read_csv(dfPath)

	#creates sample df
	## removes empty emails
	## adds column to indicate a personal email
	non_empty_df = remove_empty_emails(email_df)

	#divides email df into a test and train set
	train_df, test_df, class_labels_test, class_labels_training, value_counts = train_test_set(non_empty_df)

	train_X, test_X, feature_names = create_doc_matrices(train_df, test_df)

	model_nb = create_naive_bayes(train_X, class_labels_training)

	predictions, results = NB_results(model_nb, test_X, class_labels_test, test_df)

	informativeTerms, feature_counts_training, totalTermCounts = create_informative_terms(train_X, train_df, feature_names, test_df)

	return True

if (__name__ == '__main__'):
	model()