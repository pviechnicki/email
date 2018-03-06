import pandas as pd
import nltk
import re
import sys
from nltk import pos_tag
import math
from decimal import Decimal
DEBUGFLAG = True
pmiCutoff = 4
from nltk import TreebankWordTokenizer
from nltk.probability import FreqDist, ConditionalFreqDist
from nltk.corpus import stopwords
from urlextract import URLExtract #Tests whether a string is a valid url
from email.utils import parseaddr #Test for valid email address
from nltk.collocations import BigramAssocMeasures

def isProperty(token):
    '''
    Return true if the token is a property like uid=40911
    '''
    if re.match('\w+=\w+', token):
        return True
    else:
        return False

def isPunctuation(token):
    if (token in [',', '.', ':', '...', ';', '(', ')','--']):
        return True
    else:
        return False

def nonAlphaMatch(token, config):
    if config['nonAlphaRegex'].match(token):
        return True
    else:
        return False

def isEmailAddress(token):
    '''
    Return true if the token is a valid email address
    '''
    result = parseaddr(token)
    if result[0] == '':
        return False
    else:
        return True

def isURL(token, config):
    '''
    Test if token is formated as URL
    '''
    if config['URLExtractor'].has_urls(token):
        return True
    else:
        return False



def isValidToken(word, config):
    if word in config['stopWords']:
        #Filter stop words
        return False
    elif (len(word) < 3):
        #Make sure the token is 3 chars or longer
        return False
    elif (isPunctuation(word)):
        #Make sure the token is not punctuation
        return False
    elif nonAlphaMatch(word, config):
        #Make sure the token contains at least some letters
        return False
    elif isEmailAddress(word):
        return False
    elif isURL(word, config):
        return False
    elif isProperty(word):
        return False
    else:
        return True

def stripHighBitChars(text):
    '''
    The name says it all
    '''
    return("".join([char for char in text if ord(char) < 128]))

def bigramsFromSentences(sentences, config):
    '''
    pass in a list of sentences,
    get back a list of bigrams from same
    '''
    bigrams = [bigram for sentence in sentences for bigram in zip(
        [word for word in config['wordTokenizer'].tokenize(stripHighBitChars(sentence).lower()) if isValidToken(word, config)][:-1],
        [word for word in config['wordTokenizer'].tokenize(stripHighBitChars(sentence).lower()) if isValidToken(word, config)][1:]
        )]
    return(bigrams)

def pmi(n_ii, n_ix, n_xi, n_xx):
    '''
    Pointwise mutual information for bigrams
    '''
    total_bigrams = n_ii + n_ix + n_xi + n_xx
    total_bigrams_containing_w1 = n_ii + n_ix
    total_bigrams_containing_w2 = n_ii + n_xi
    d = Decimal((n_ii/(total_bigrams))/((total_bigrams_containing_w1/total_bigrams)*(total_bigrams_containing_w2/total_bigrams)))
    return d.ln()

def generateBigramsList(myEmailDf, config, catColname, catValue, n=20):
    '''
    extract the top n bigrams from the specified data frame
    using chisq information gain score according to category
    specified in df.catColname with value=catValue
    '''
        # Filter out empty rows
    non_empty_df = myEmailDf[myEmailDf['body'].isnull() == False].sample(frac=.1)
    #Make binary variable for in_category/not_in_category
    non_empty_df['in_category'] = (non_empty_df[catColname] == catValue)

    print("Original dataframe contains {} messages\nNon-empty datafram contains {} messages\n".format(
        len(myEmailDf), len(non_empty_df)))

    #myStemmer = SnowballStemmer('english')
#    myTokenizer = TreebankWordTokenizer()

    allWords = []
    allBigrams = []
    fdist = FreqDist()
    cfdist = ConditionalFreqDist()

    #Make sure we're assigning the right conditions
    print(non_empty_df.groupby('in_category').count())
    pos_bigram_count = 0
    neg_bigram_count = 0


    for (index, row) in non_empty_df.iterrows():
        message = splitThread(row['body'], config)

        #Calculate simple frequnecy distribution of terms in the vocabulary
        allWords += [word for word in config['wordTokenizer'].tokenize(
            stripHighBitChars(message).lower()
            ) if isValidToken(word, config)
                     ]

        condition = row['in_category']
        sentences = []
        sentences = splitMessage(message, config)


        bigrams = bigramsFromSentences(sentences, config)

        #Tally up bigram occurrences and conditional occurrences
        for bigram in bigrams:
            fdist[bigram] += 1
            cfdist[condition][bigram] += 1
            if (condition == True):
                pos_bigram_count += 1
            else:
                neg_bigram_count += 1
            allBigrams.append(bigram)

    total_bigram_count = pos_bigram_count + neg_bigram_count

    bigram_chisq = {}
    bigram_pmi = {}

    fdistWords = FreqDist(allWords)

    #Compute chisquared values for each bigram for each category
    for bigram, freq in fdist.items():
        pos_score = BigramAssocMeasures.chi_sq(cfdist[True][bigram],
                                               (freq, pos_bigram_count),
                                               total_bigram_count)
        neg_score = BigramAssocMeasures.chi_sq(cfdist[False][bigram],
                                               (freq, neg_bigram_count),
                                               total_bigram_count)
        bigram_chisq[bigram] = pos_score + neg_score
        w1, w2 = bigram
        bigram_pmi[bigram] = pmi(fdist[bigram], fdistWords[w1],
                                 fdistWords[w2], total_bigram_count)

    filtered = {k:v for k,v in bigram_chisq.items() if bigram_pmi[k] > pmiCutoff}
    best = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[0:n]
    best_bigrams = [b for b,s in best]

    if (DEBUGFLAG):
        print("Min: {}".format(min(bigram_pmi.items(), key=lambda x: x[1])))
        print("Max: {}".format(max(bigram_pmi.items(), key=lambda x: x[1])))

        for b in best_bigrams:
            print("{}|{}".format(b, bigram_pmi[b]))

    return best_bigrams

class MessageFeaturesCollection:

    '''
    Just a conventient collection of properties of each email message...
    '''
    def __init__(self, messageText, config, informativeBigrams):
        self._sentences = splitMessage(messageText, config)
        self._taggedSentences = [pos_tag(config['wordTokenizer'].tokenize(sentence)) for sentence in self._sentences]
        self._bigrams = bigramsFromSentences(self._sentences, config)

        self.wordCount = len(config['wordTokenizer'].tokenize(messageText))
        self.sentenceCount = len(self._sentences)
        self.questionCount = self.countQuestions(self._taggedSentences, config)
        self.verbCount = self.countVerbs(self._taggedSentences)
        self.modalVerbCount = self.countModalVerbs(self._taggedSentences)
        self.presentTenseVerbCount = self.countPresentTenseVerbs(self._taggedSentences)
        self.punctuationCount = self.countPunctuation(self._taggedSentences)
        self.punctuationPerSentence = ((self.punctuationCount / self.sentenceCount) if self.sentenceCount > 0 else 0)
        self.hasGreeting = self.includesGreeting(self._sentences, config)
        self.hasSignoff = self.includesSignoff(self._sentences, config)
        self.b0 = self.containsBigram(informativeBigrams[0])
        self.b1 = self.containsBigram(informativeBigrams[1])
        self.b2 = self.containsBigram(informativeBigrams[2])
        self.b3 = self.containsBigram(informativeBigrams[3])
        self.b4 = self.containsBigram(informativeBigrams[4])
        self.b5 = self.containsBigram(informativeBigrams[5])
        self.b6 = self.containsBigram(informativeBigrams[6])
        self.b7 = self.containsBigram(informativeBigrams[7])
        self.b8 = self.containsBigram(informativeBigrams[8])
        self.b9 = self.containsBigram(informativeBigrams[9])
        self.b10 = self.containsBigram(informativeBigrams[10])
        self.b11 = self.containsBigram(informativeBigrams[11])
        self.b12 = self.containsBigram(informativeBigrams[12])
        self.b13 = self.containsBigram(informativeBigrams[13])
        self.b14 = self.containsBigram(informativeBigrams[14])
        self.b15 = self.containsBigram(informativeBigrams[15])
        self.b16 = self.containsBigram(informativeBigrams[16])
        self.b17 = self.containsBigram(informativeBigrams[17])
        self.b18 = self.containsBigram(informativeBigrams[18])
        self.b19 = self.containsBigram(informativeBigrams[19])


    def print(self):
        properties = [
            self.wordCount,
            self.sentenceCount,
            self.questionCount,
            self.verbCount,
            self.modalVerbCount,
            self.presentTenseVerbCount,
            self.punctuationCount,
            self.punctuationPerSentence,
            self.hasGreeting,
            self.hasSignoff,
            self.b0,
            self.b1,
            self.b2,
            self.b3,
            self.b4,
            self.b5,
            self.b6,
            self.b7,
            self.b8,
            self.b9,
            self.b10,
            self.b11,
            self.b12,
            self.b13,
            self.b14,
            self.b15,
            self.b16,
            self.b17,
            self.b18,
            self.b19
            ]
        print("|".join([str(property) for property in properties]))


    def containsBigram(self, bigram):
        '''
        Is this bigram contained in this message?
        '''
        if (bigram in self._bigrams):
            return True
        else:
            return False


    def countVerbs(self, taggedSentences):
        result = 0
        for sentence in taggedSentences:
            for (word, tag) in sentence:
                if (isVerb(tag)):
                    result += 1
        return result
    def countModalVerbs(self, taggedSentences):
        result = 0
        for sentence in taggedSentences:
            for (word, tag) in sentence:
                if (isModalVerb(tag)):
                    result += 1
        return result
    def countPresentTenseVerbs(self, taggedSentences):
        result = 0
        for sentence in taggedSentences:
            for (word, tag) in sentence:
                if (isPresentTenseVerb(tag)):
                    result += 1
        return result
    def countQuestions(self, taggedSentences, config):
        result = 0
        for sentence in taggedSentences:
            #check if first word is wh-word, or last token is question mark
            if sentence[0][0].lower() in config['whWords']:
                result += 1
            elif (sentence[-1][1] == '.' and sentence[-1][0] == '?'):
                result += 1
        return result
    def countPunctuation(self, taggedSentences):
        result = 0
        for sentence in taggedSentences:
            for (word, tag) in sentence:
                if isPunctuation(tag):
                    result += 1
        return result
    def countWordsPerSentence(self, sentences):
        lengths = [len(sentence) for sentence in sentences]
        if len(sentences) > 0:
            return sum(lengths) / len(lengths)
        else:
            sys.stderr.write("Warning, message with 0 sentences found by countWordsPerSentence")
            return 0
    def includesGreeting(self, sentences, config):
        '''
        Does this email message start with an explicit greeting like dear, etc
        #Only consider first two sentences
        '''
        if len(sentences) >= 2:
            loopNum = 1
        else:
            loopNum = 0
        for sentence in sentences[0:loopNum]:
            if (config['greetingWordsRE'].match(sentence)):
                return True
        return False

    def includesSignoff(self, sentences, config):
        '''
        Does this email end with an explicit signoff like 'Sincerely, yours, regards...
        Only consider last two sentences
        '''
        if len(sentences) >= 2:
            loopNum = -2
        else:
            loopNum = -1
        for sentence in sentences[loopNum:-1]:
            if (config['signoffWordsRE'].match(sentence)):
                return True
        return False

def initializeFeatureExtractor(DEGUGFLAG=False):
    config = dict()
    config['messageDelimiter'] = 'From: ' #Marks start of replied to message in email body

    if DEBUGFLAG:
        sys.stderr.write("initializing sentence and word tokenizers...\n")
    config['sentenceSplitter'] = nltk.data.load('tokenizers/punkt/english.pickle')

    config['wordTokenizer'] = TreebankWordTokenizer()

    config['fields'] = [
        'wordCount',
        'sentenceCount',
        'questionCount',
        'verbCount',
        'presentTenseVerbCount',
        'modalVerbCount',
        'punctuationCount',
        'punctuationPerSentence',
        'hasGreeting',
        'hasSignoff',
        'b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8', 'b9', 'b10',
        'b11', 'b12', 'b13', 'b14', 'b15', 'b16', 'b17', 'b18', 'b19'
    ]

    config['whWords'] = ['who', 'what', 'where', 'why', 'how', 'which']

    #Make sure to add .* before first and after last word in list
    config['greetingWords'] = ['.*dear sir', 'dear sir/madam', 'dear madam', 'dear', 'hello', 'hi.*']
    greetingString = ".*|.*".join(config['greetingWords'])
    config['greetingWordsRE'] = re.compile(greetingString, re.IGNORECASE)

    config['signoffWords'] = ['.*sincerely', 'thanks', 'best wishes', 'v/r', 'cheers',
    'regards', 'faithfully', 'yours truly', 'yours sincerely', 'best regards', 'sincerely yours.*']
    signoffString  = ".*|.*".join(config['signoffWords'])
    config['signoffWordsRE'] = re.compile(signoffString, re.IGNORECASE)

    config['stopWords'] = set(stopwords.words('english'))

    config['nonAlphaRegex'] = re.compile('^[^a-z]+$', re.IGNORECASE)

    config['URLExtractor'] = URLExtract()

    return (config)

def printHeaders(fields):
    allFields = fields + ['subject', 'message']
    print("|".join(allFields))

def splitThread(text, myConfig):
    '''
    return first in list of messages, splitting on delimiter from config
    '''
    return text.split(myConfig['messageDelimiter'])[0]

def splitMessage(text, myConfig):
    '''
    return list of sentences
    '''
    return(myConfig['sentenceSplitter'].tokenize(text))

def isVerb(tag):
    if (tag[0] == 'V' or tag == 'MD'):
        return True
    else:
        return False

def isModalVerb(tag):
    if (tag == 'MD'):
        return True
    else:
        return False
def isPresentTenseVerb(tag):
    if (tag in ['VBP', 'VBZ', 'VBG']):
        return True
    else:
        return False

def isPunctuation(tag):
    if (tag in ['.', ',', ':', '--']):
        return True
    else:
        return False

def extractFeatures(myConfig):

    #Read in csv of emails
    email_df = pd.read_csv('../data/pv_email/combined_emails.csv', sep='|')

    #Extract bigrams
    if (DEBUGFLAG):
        sys.stderr.write("Selecting informative bigrams...\n")
    informativeBigrams = extractBigrams(email_df, myConfig, 'cat',
                                        'fraud_waste_abuse', 50)

    #Split into threads
    for index, row in email_df.iterrows():
        #Split into messages
        outputBuffer = []
        thread = row['body']
        if (len(thread) > 1):
            #(actually only do this for final message in thread)
            subject = row['subject']
            message = splitThread(thread, myConfig)
            messageMetadata = dict() #Container to hold metadata

            #Parse into sentences
            sentences = splitMessage(message, myConfig)

            messageMetadata['sentenceCount'] = len(sentences)
            messageMetadata['wordCount'] = 0
            messageMetadata['verbCount'] = 0
            messageMetadata['presentTenseVerbCount'] = 0
            messageMetadata['modalVerbCount'] = 0
            messageMetadata['punctuationCount'] = 0

            for sentence in sentences:
                words = config['wordTokenizer'].tokenize(sentence)
                messageMetadata['wordCount'] += len(words)
                taggedWords = pos_tag(words)

                for word in words:
                    if isPunctuation(word):
                        messageMetadata['punctuationCount'] += 1
                for (word, tag) in taggedWords:
                    if (isVerb(tag)):
                        messageMetadata['verbCount'] += 1
                    if (isPresentTenseVerb(tag)):
                        messageMetadata['presentTenseVerbCount'] += 1
                    if (isModalVerb(tag)):
                        messageMetadata['modalVerbCount'] += 1
            temp = [str(messageMetadata[field]) for field in myConfig['fields']]
            outputBuffer = temp + [subject, message]
            print("|".join(outputBuffer))
            break

        #Capitalization

'''
def extractBigrams(myDf, config, catColname, catValue, n=20):

    email_df = myDf
    #Add rowid
    email_df['rownum'] = range(0, len(email_df))

    # Filter out empty rows
    non_empty_df = email_df[email_df['body'].isnull() == False].sample(frac=.1)
    #Make binary variable for in_category/not_in_category
    non_empty_df['in_category'] = (non_empty_df[catColname] == catValue)

    print("Original dataframe contains {} messages\nNon-empty datafram contains {} messages\n".format(
        len(email_df), len(non_empty_df)))

    #myStemmer = SnowballStemmer('english')
    myTokenizer = TreebankWordTokenizer()

    allWords = []
    allBigrams = []
    fdist = FreqDist()
    cfdist = ConditionalFreqDist()

    #Make sure we're assigning the right conditions
    print(non_empty_df.groupby('in_category').count())
    pos_bigram_count = 0
    neg_bigram_count = 0

    for (index, row) in non_empty_df.iterrows():
        message = splitThread(row['body'], config)

        #Calculate simple frequnecy distribution of terms in the vocabulary
        allWords += [word for word in myTokenizer.tokenize(
            stripHighBitChars(message).lower()
        ) if isValidToken(word)
        ]

        condition = row['in_category']
        sentences = []
        sentences = splitMessage(message, config)

        bigrams = [bigram for sentence in sentences for bigram in zip(
            [word for word in myTokenizer.tokenize(stripHighBitChars(sentence).lower()) if isValidToken(word)][:-1],
            [word for word in myTokenizer.tokenize(stripHighBitChars(sentence).lower()) if isValidToken(word)][1:]
        )]

        #Tally up bigram occurrences and conditional occurrences
        for bigram in bigrams:
            fdist[bigram] += 1
            cfdist[condition][bigram] += 1
            if (condition == True):
                pos_bigram_count += 1
            else:
                neg_bigram_count += 1
            allBigrams.append(bigram)

    total_bigram_count = pos_bigram_count + neg_bigram_count

    bigram_chisq = {}
    bigram_pmi = {}

    #Compute chisquared values for each bigram for each category
    for bigram, freq in fdist.items():
        pos_score = BigramAssocMeasures.chi_sq(cfdist[True][bigram],
                                               (freq, pos_bigram_count),
                                               total_bigram_count)
        neg_score = BigramAssocMeasures.chi_sq(cfdist[False][bigram],
                                               (freq, neg_bigram_count),
                                               total_bigram_count)

        bigram_chisq[bigram] = pos_score + neg_score
        w1, w2 = bigram
        bigram_pmi = pmi(fdist[bigram], fdistWords[w1],
                         fdistWords[w2], total_bigram_count)

    filtered = {k:v for k,v in bigram_chisq.items() if bigram_pmi[k] > pmiCutoff}
    best = sorted(bigram_scores.items(), key=lambda x: x[1], reverse=True)[0:n]
    best_bigrams = [b for b,s in best]

    return best_bigrams
'''
