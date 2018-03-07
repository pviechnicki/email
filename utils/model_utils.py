import pandas as pd
import os
import numpy as np
import sys
sys.path.append('C:\\Users\\ComputerA\\AppData\\Local\\Continuum\\Anaconda3\\envs\\dotce\\lib\\site-packages\\pyLDAvis')
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
from collections import defaultdict
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from sklearn.cross_validation import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn import metrics
import pickle
from nltk.probability import FreqDist, ConditionalFreqDist
#trying to re-add to git
def remove_empty_emails(email_df):
	#Add rowid
	email_df['rownum'] = range(0, len(email_df))
	email_df.groupby('sensitivity').count()
	# Filter out empty rows
	non_empty_df = email_df[email_df['body'].isnull() == False].sample(frac = 1)
	#sample method chooses a random sample of the origina frame
	#https://stackoverflow.com/questions/29576430/shuffle-dataframe-rows
	print("Original dataframe contains {} messages\nNon-empty datafram contains {} messages\n".format(
	len(email_df), len(non_empty_df)))

	non_empty_df['personal'] = (non_empty_df['sensitivity'] == 'Sensitivity Personal')

	#DELETE THIS FOR ACTUAL MODEL
	# for i, row in non_empty_df.iterrows():
	# 	if 'Russia' in row['body']:
	# 		non_empty_df = non_empty_df.set_value(i, 'personal', 'True')
	# print('SETTING ROWS TO PERSONAL THAT CONTAIN WORD RUSSIA - MAKE SURE TO REMOVE')
	#Create a vector of class labels
	class_labels = non_empty_df['personal']
	#use value_counts() method of series
	print(class_labels.value_counts())
	print(set(non_empty_df['personal']))

	return non_empty_df



def train_test_set(non_empty_df):
	#Create a training set and test set, 80% 20%
	train_df, test_df = train_test_split(non_empty_df, train_size = 0.8, random_state=44)
	class_labels_training = list(train_df['personal'])
	class_labels_test = list(test_df['personal'])
	value_counts = nltk.FreqDist(class_labels_training)

	return train_df, test_df, class_labels_test, class_labels_training, value_counts

def feature_selection(non_empty_df, n):

	for index, row in non_empty_df.iterrows():
		try:
			split_message = row['body'].split('From')
			message = split_message[0]
			# words = word_tokenize(message)
			# for word in words:
			# 	print(word)
			# 	allWords.append(word)

		except:
			message = row['body']
			# words = word_tokenize(message)
			# for word in words:
			# 	allWords.append(word)
	# print(allWords[0:10])
	allWords = myTokenize(message)
	fdist = FreqDist()
	cfdist = ConditionalFreqDist()

	pos_word_count = 0
	neg_word_count = 0



	condition = row['personal']

	all_unique_words = set(allWords)

	for word in all_unique_words:
		fdist[word] +=1
		cfdist[condition][word] += 1
		if (condition == True):
			pos_word_count +=1
		else:
			neg_word_count +=1

	word_chisq = {}
	fdistWords = FreqDist(allWords)
	for word, freq in fdist.items():
		pos_score = fdistWords.chi_sq(cfdist[True][word],(freq, pos_word_count),len(all_unique_words))
		neg_score = fdistWords.chi_sq(cfdist[False][word],(freq, neg_word_count), len(all_unique_words))
		word_chisq[word] = pos_score + neg_score
    
	best_words = sorted(word_chisq.items(), key=lambda x: x[1], reverse=True)[0:n]

	return best_words

def create_doc_matrices(train_df, test_df):
	##Instantiate a TFidf vectorizer
	vectorizer = TfidfVectorizer(sublinear_tf=True, encoding='utf-8', 
                             max_df=0.5, tokenizer=myTokenize)
	#This step can take a while
	train_X = vectorizer.fit_transform(train_df['body'])
	##Save feature names in a separate list
	feature_names = vectorizer.get_feature_names()
	#From http://fastml.com/classifying-text-with-bag-of-words-a-tutorial/
	#Create another matrix of tfidf scores for the documents in the test set
	test_X = vectorizer.transform(test_df['body'])

	return train_X, test_X, feature_names



def create_naive_bayes(train_X, class_labels_training):
	#The alpha value is the sensitivity parameter.
	# We train the classifier by feeding it with the labeled training data we created in step 3 above.
	model_nb = MultinomialNB(alpha=0.05)
	model_nb.fit(train_X, class_labels_training)

	return model_nb

def NB_results(model_nb, test_X, class_labels_test, test_df, output_directory):
	predictions = model_nb.predict( test_X )
	print("Accuracy score for your classifier: {:.3f}\n".format(model_nb.score( test_X, class_labels_test)))
	print("Error rate for your classifier: {:.3f}\n".format(1-model_nb.score( test_X, class_labels_test)))
	classifierStats = dict()
	classifierStats['accuracy'] = model_nb.score( test_X, class_labels_test)
	classifierStats['errorRate'] = (1 - model_nb.score( test_X, class_labels_test))

	results = [(class_labels_test[i], predictions[i]) for i in range(0,len(predictions))]
	#Add in the email id, subject, and body, then truePos, falsePos, trueNeg, falseNeg
	enrichedResults = pd.DataFrame.from_records(results, test_df['rownum'].tolist(), 
    columns = ['ground_truth', 'predicted_value'])
	enrichedResults['truthValue'] = enrichedResults.apply(lambda row: truth_value(row), axis=1)
	enrichedResults['subject'] = test_df['subject'].tolist()
	enrichedResults['body'] = test_df['body'].tolist()
	counts = enrichedResults['truthValue'].value_counts()
	for i in range(0,len(counts)):
		classifierStats[counts.index[i]] = counts[i]
	with open(output_directory + '//'+ 'classifierStats.pyc', 'wb') as f:
		pickle.dump(classifierStats, f)
	f.close()
	with open(output_directory + '//'+ 'classifierTestResults.pyc', 'wb') as f1:
		pickle.dump(enrichedResults, f1)

	f1.close()

	print(metrics.classification_report(class_labels_test, predictions))

	return predictions, results

def create_informative_terms(train_X, train_df, feature_names, test_df, output_directory):
	informativeTerms = top_feats_by_class(train_X, train_df, feature_names, top_n=100)
	#Should print out 10 most informative features for you
	informativeTerms.head(10)
	with open(output_directory + '//'+ 'informativeTerms.pyc', 'wb') as f:
		pickle.dump(informativeTerms, f)
	f.close()

	feature_counts_training = defaultdict(int)
	feature_counts_test = defaultdict(int)
	informativeTermsSet = set(informativeTerms['feature'])
	trainTokensTotal = 0
	testTokensTotal = 0

	for index, row in train_df.iterrows():
	    for token in myTokenize(row['body']):
	        trainTokensTotal += 1
	        if (token in informativeTermsSet):
	            feature_counts_training[token] += 1 

	for index, row in test_df.iterrows():
	    for token in myTokenize(row['body']):
	        testTokensTotal+= 1
	        if (token in informativeTermsSet):
	            feature_counts_test[token] += 1 

	#Write to disk
	with open(output_directory + '//'+ 'feature_counts_training.pyc', 'wb') as f:
	    pickle.dump(feature_counts_training, f)
	f.close()
	with open(output_directory + '//'+ 'feature_counts_test.pyc', 'wb') as f:
	    pickle.dump(feature_counts_test, f)
	f.close()

	print(informativeTermsSet)

	totalTermCounts = {'trainTokensTotal': trainTokensTotal, 'testTokensTotal': testTokensTotal}
	with open(output_directory + '//'+ 'totalTermCounts.pyc', 'wb') as f:
		pickle.dump(totalTermCounts, f)
	f.close()

	return informativeTerms, feature_counts_training, totalTermCounts



########################## HELPER FUNCTIONS ###############################################

def preprocess(text):
    no_punctuation_text = ''
    if (type(text)== str):
        lower_text = text.lower()
        no_punctuation_text = lower_text.translate({ord(c):'' for c in string.punctuation})
    return no_punctuation_text

def myTokenize(text):
	global snowballStemmer
	snowballStemmer = SnowballStemmer("english", ignore_stopwords=True)
	tokens = []
	cleaned = preprocess(text)
	tokens = nltk.word_tokenize(cleaned)
	filtered = [w for w in tokens if not w in stopwords.words('english')]
	stemmed = [w for w in map(snowballStemmer.stem, filtered)]
	return stemmed

def truth_value(myRow):
    if (myRow['ground_truth'] == True and myRow['predicted_value'] == True):
        return 'truePositive'
    elif (myRow['ground_truth'] == True and myRow['predicted_value'] == False):
        return 'falseNegative'
    elif (myRow['ground_truth'] == False and myRow['predicted_value'] == True):
        return 'falsePositive'
    elif (myRow['ground_truth'] == False and myRow['predicted_value'] == False):
        return 'trueNegative'
    else:
        return None
#Returns top n tfidf features as df, but takes dense format vector as input
def top_tfidf_feats(row, features, top_n=25):
    ''' Get top n tfidf values in row and return them with their corresponding feature names.'''
    topn_ids = np.argsort(row)[::-1][:top_n]
    top_feats = [(features[i], row[i]) for i in topn_ids]
    df = pd.DataFrame(top_feats)
    df.columns = ['feature', 'tfidf']
    return df

#convert single row into dense format
def top_feats_in_doc(Xtr, features, row_id, top_n=25):
    ''' Top tfidf features in specific document (matrix row) '''
    row = np.squeeze(Xtr[row_id].toarray())
    return top_tfidf_feats(row, features, top_n)

def top_mean_feats(Xtr, features, grp_ids=None, min_tfidf=0.1, top_n=25):
    ''' Return the top n features that on average are most important amongst documents in rows
        indentified by indices in grp_ids. '''
    if grp_ids:
        D = Xtr[grp_ids].toarray()
    else:
        D = Xtr.toarray()

    D[D < min_tfidf] = 0
    tfidf_means = np.mean(D, axis=0)

    return top_tfidf_feats(tfidf_means, features, top_n)


def top_feats_by_class(Xtr, y, features, min_tfidf=0.1, top_n=25):
    ''' Return a list of dfs, where each df holds top_n features and their mean tfidf value
        calculated across documents with the same class label. '''
    ids = np.where(y.personal==True)
    feats_df = top_mean_feats(Xtr, features, ids, min_tfidf=min_tfidf, top_n=top_n)
    feats_df.label = 'personal'

    return feats_df
