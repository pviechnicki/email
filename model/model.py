import pandas as pd 
import sys
sys.path.insert(0,'C:/Users/ComputerA/email_marker/REPO/data/Output')
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from model_utils import remove_empty_emails
from model_utils import train_test_set
from model_utils import create_doc_matrices
from model_utils import create_naive_bayes
from model_utils import NB_results
from model_utils import create_informative_terms
import getopt

#trying to re-add to git
def usage():
	sys.stdout.write("Usage: python model.py [-d|--directory= <top directory of the github repository where your directory yaml sits>] [-h|?|--help]")	

def run_model():
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
			yaml_directory = a
			sys.path.insert(0, yaml_directory)
			from load_directories import directory_loader
			input_directory, output_directory = directory_loader(yaml_directory)

	email_df = pd.read_csv(output_directory + '//' + 'Master_df.csv')

	#creates sample df
	## removes empty emails
	## adds column to indicate a personal email
	non_empty_df = remove_empty_emails(email_df)

	#divides email df into a test and train set
	train_df, test_df, class_labels_test, class_labels_training, value_counts = train_test_set(non_empty_df)


	train_X, test_X, feature_names = create_doc_matrices(train_df, test_df)

	model_nb = create_naive_bayes(train_X, class_labels_training)

	predictions, results = NB_results(model_nb, test_X, class_labels_test, test_df, output_directory)

	informativeTerms, feature_counts_training, totalTermCounts = create_informative_terms(train_X, train_df, feature_names, test_df, output_directory)

	return True

if __name__ == "__main__":
	run_model()

