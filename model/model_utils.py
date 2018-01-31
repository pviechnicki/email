import pandas as pd 
import os
import numpy as np
import sys
sys.path.append('C:\\Users\\ComputerA\\AppData\\Local\\Continuum\\Anaconda3\\envs\\dotce\\lib\\site-packages\\pyLDAvis')
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from sklearn import metrics
from sklearn.cross_validation import train_test_split
from sklearn.linear_model import LogisticRegression as LR
from sklearn.naive_bayes import MultinomialNB

def remove_empty_emails(email_df):
	'''
	creates sample df with 80% of non empty emails and creates personal column to indicate whether the email was originally tagged as personal
	'''
	email_df.groupby('sensitivity').count()
	# Filter out empty rows
	non_empty_df = email_df[email_df['body'].isnull() == False].sample(frac=.8)
	#sample method chooses a random sample of the origina frame
	#https://stackoverflow.com/questions/29576430/shuffle-dataframe-rows
	print("Original dataframe contains {} messages\nNon-empty datafram contains {} messages\n".format(
	len(email_df), len(non_empty_df)))
	non_empty_df['personal'] = (non_empty_df['sensitivity'] == 'Sensitivity Personal')
	#Create a vector of class labels
	class_labels = non_empty_df['personal']
	#use value_counts() method of series
	class_labels.value_counts()

	return non_empty_df

def create_train_test(non_empty_df):
	'''
	defines train and test set, gets list of all values in personal column for both training and test set to be used in models
	'''

	train_df, test_df = train_test_split(non_empty_df, train_size = 0.8, random_state=44)
	class_labels_training = list(train_df['personal'])
	class_labels_test = list(test_df['personal'])
	value_counts = nltk.FreqDist(class_labels_training)

	return train_df, test_df, class_labels_training, class_labels_test


def myTokenize(text):
	'''
	creates a list of tokens using a SnowballStemmer
	'''
	global snowballStemmer
	snowballStemmer = SnowballStemmer("english", ignore_stopwords=True)
	tokens = []
	cleaned = preprocess(text)
	tokens = nltk.word_tokenize(cleaned)
	filtered = [w for w in tokens if not w in stopwords.words('english')]
	stemmed = [w for w in map(snowballStemmer.stem, filtered)]

	return stemmed

def preprocess(text):
	'''
	turns all text into lowercase and removes punctuation to create tokens
	'''
	no_punctuation_text = ''
	if (type(text)== str):
		lower_text = text.lower()
		no_punctuation_text = lower_text.translate({ord(c):'' for c in string.punctuation})

	return no_punctuation_text

def Instantiate_TFIDF_Vectorizer():
	'''
	creates matrices of TFidf scores for both the training set and the testing set, also returns list of feature names
	'''
	##Instantiate a TFidf vectorizer
	vectorizer = TfidfVectorizer(sublinear_tf=True, encoding='utf-8', 
                             max_df=0.5, tokenizer=myTokenize)

	return vectorizer

def Train_Vectorizer(train_df, vectorizer):

	#may have to do feature selection rather than pass entire body
	train_X = vectorizer.fit_transform(train_df['body'])

	##Save feature names in a separate list
	feature_names = vectorizer.get_feature_names()

	return train_X, feature_names

def  Test_Vectorizer(test_df, vectorizer):
	
	#From http://fastml.com/classifying-text-with-bag-of-words-a-tutorial/
	#Create another matrix of tfidf scores for the documents in the test set
	test_X = vectorizer.transform(test_df['body'])

	return test_X

def Logistic_Regression(train_X, test_X, class_labels_training, class_labels_test):
	'''
	runs logistic regression

	calculates p value for logistric regression

	prints model output and p value
	'''
	model_lr = LR()
	model_lr.fit(train_X, class_labels_training)
	print(model_lr)

	p = model_lr.predict_proba( test_X )[:,1]
	print(model_lr.score( test_X, class_labels_test))

	return p

def Naive_Bayes(train_X, test_X, class_labels_training, class_labels_test):
	'''
	runs Naive Bayes model

	calculates p value for Naive Bayes 'p2'

	prints model output and p value
	'''

	model_nb = MultinomialNB(alpha=0.05)
	print(model_nb.fit(train_X, class_labels_training))

	p2 = model_nb.predict( test_X )
	print(model_nb.score( test_X, class_labels_test))

	results = [(class_labels_test[i], p2[i]) for i in range(0,len(p2))]
	len(results)
	print(results[0:20])


	return results, p2, model_nb

def analyze_results(test_df, p, p2, class_labels_test):
	'''
	counts number of true negatives, true positives, false negatives and false positives for logistic

	calculates classifier accuracy and error rates for logistic (calls on functions accuracy and error rate defined below)

	calculates precision and recall for naive bayes

	'''
	output_df = pd.DataFrame( data = {'messageId': test_df['messageId'], 
                                  'personal': test_df['personal'], 
                                  'logistic': p })
	print("Output dataframe length: {}\n".format(len(output_df)))
	THRESHOLD = .23
	output_df['prediction'] = (output_df['logistic'] >= THRESHOLD)
	print("DF columns:{}\n".format(", ".join(output_df.columns)))
	print(output_df.head(30))

	true_positives = len(output_df.loc[(output_df['personal'] == True) & (output_df['prediction'] == True)])
	false_positives = len(output_df.loc[(output_df['personal'] == False) & (output_df['prediction'] == True)])
	true_negatives = len(output_df.loc[(output_df['personal'] == False) & (output_df['prediction'] == False)])
	false_negatives = len(output_df.loc[(output_df['personal'] == True) & (output_df['prediction'] == False)])
	print("Results\nTrue Positives\tTrue_Negatives\tFalse_Positives\False_Negatives\n")
	print("\t".join(map(str, [true_positives, true_negatives, false_positives, false_negatives])))

	print("Classifier Accuracy: {}\n".format(accuracy(true_positives, true_negatives, 
                                                  false_positives, false_negatives)))
	print("Classifier Error Rate: {}\n".format(error_rate(true_positives, true_negatives,
                                                      false_positives, false_negatives)))

	print(metrics.classification_report(class_labels_test, p2))

	return true_positives, true_negatives, false_negatives, false_positives


def accuracy(tp, tn, fp, fn):
	accuracy_metric = ((tp + tn)/(tp + tn + fp + fn))
	return accuracy_metric

def error_rate(tp, tn, fp, fn):
	error_metric = ((fp + fn)/ (tp + tn + fp + fn))
	return error_metric

def show_most_informative_features(vectorizer, clf, n=20):
	'''
	prints list of most informative features
	'''
	feature_names = vectorizer.get_feature_names()
	coefs_with_fns = sorted(zip(clf.coef_[0], feature_names))
	top = zip(coefs_with_fns[:n], coefs_with_fns[:-(n + 1):-1])
	for (coef_1, fn_1), (coef_2, fn_2) in top:
	    print ("\t%.4f\t%-15s\t\t%.4f\t%-15s" % (coef_1, fn_1, coef_2, fn_2))

	return None 




