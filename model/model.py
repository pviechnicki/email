import pandas as pd 
import sys
sys.path.insert(0,'C:/Users/ComputerA/email_marker/REPO/data/Output')
from model_utils import remove_empty_emails
from model_utils import create_train_test
from model_utils import preprocess
from model_utils import myTokenize
from model_utils import Instantiate_TFIDF_Vectorizer
from model_utils import Train_Vectorizer
from model_utils import Test_Vectorizer
from model_utils import Logistic_Regression
from model_utils import Naive_Bayes
from model_utils import accuracy
from model_utils import error_rate
from model_utils import analyze_results
from model_utils import show_most_informative_features



email_df = pd.read_excel('C:/Users/ComputerA/email_marker/REPO/data/Output/email_df.xlsx', sheetname = 'Sheet1')

#creates sample df
## removes empty emails
## adds column to indicate a personal email
non_empty_df = remove_empty_emails(email_df)

#divides email df into a test and train set
train_df, test_df, class_labels_training, class_labels_test = create_train_test(non_empty_df)


#creates a Tfidf vectorizer using the stemmed words
vectorizer= Instantiate_TFIDF_Vectorizer()

#
train_X, feature_names = Train_Vectorizer(train_df, vectorizer)

test_X = Test_Vectorizer(test_df, vectorizer)

p = Logistic_Regression(train_X, test_X, class_labels_training, class_labels_test)

results, p2, model_nb = Naive_Bayes(train_X, test_X, class_labels_training, class_labels_test)

true_positives, true_negatives, false_negatives, false_positives = analyze_results(test_df, p, p2, class_labels_test)

_ = show_most_informative_features(vectorizer, model_nb, n=20)




