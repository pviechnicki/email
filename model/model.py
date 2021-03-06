import pandas as pd 
import sys
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

import getopt

#Add higher level directory to import path so it can find wrangle_utils
sys.path.append("..\wrangle")

#trying to re-add to git
def usage():
	sys.stdout.write("Usage: python model.py [-d|--directory= <top directory of the github repository where your directory yaml sits>] [-h|?|--help]")	

def run_model():
	use_feature_selection = False
	try:
		opts, args = getopt.getopt(sys.argv[1:], "d:n:h?", ["--directory=", "--number=", "--help"])
	except getopt.GetoptError as err:
		#Exit if can't parse args
		usage()	
		sys.exit(2)
	for o, a in opts:
		if (o == '-h' or o == '-?'):
			usage()
			exit(0)
		elif o in ('-d', '--directory'):
			parent_path = a
			sys.path.insert(0, parent_path + '//' + 'utils')
			from load_directories import directory_loader
			input_directory, output_directory = directory_loader(parent_path)
			from model_utils import remove_empty_emails
			from model_utils import train_test_set
			from model_utils import create_doc_matrix
			from model_utils import create_naive_bayes
			from model_utils import NB_results
			from model_utils import create_informative_terms
			from model_utils import feature_selection
		elif o in ('-n', '--number'):
			try:
				n = int(a)
				use_feature_selection = True
			except:
				
				sys.stder.write("Argument to -n|--number= option must be integer.")

	email_df = pd.read_csv(output_directory + '//' + 'Master_df.bsv', delimiter = '|')

	#creates sample df
	## removes empty emails
	## adds column to indicate a personal email
	non_empty_df = remove_empty_emails(email_df)

	#divides email df into a test and train set
	train_df, test_df, class_labels_test, class_labels_training, value_counts = train_test_set(non_empty_df)

	if use_feature_selection == True:
		best_words, top_word_list = feature_selection(train_df, n)
		train_X, test_X, feature_names = create_doc_matrix(train_df, test_df, top_word_list, feature_selection)

	else:
		train_X, test_X, feature_names = create_doc_matrix(train_df, test_df)


	model_nb = create_naive_bayes(train_X, class_labels_training)

	predictions, results = NB_results(model_nb, test_X, class_labels_test, test_df, output_directory)

	informativeTerms, feature_counts_training, totalTermCounts = create_informative_terms(train_X, train_df, feature_names, test_df, output_directory)

	return True

if __name__ == "__main__":
	run_model()

