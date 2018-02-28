import pandas as pd
import nltk
import re
from nltk import pos_tag
from nltk import word_tokenize


def generateBigramsList(myEmailDf):
    '''
    bigramsList = []
    for index, row in myEmailDf.iterrows():

        subject = row['subject']
        body = row['body']

        if (len(body) > 0):
    '''        
    return None

class MessageFeaturesCollection:

    '''
    Just a conventient collection of properties of each email message...
    '''
    def __init__(self, messageText, config):
        self._sentences = splitMessage(messageText, config)
        self._taggedSentences = [pos_tag(word_tokenize(sentence)) for sentence in self._sentences]
        self.wordCount = len(word_tokenize(messageText))
        self.sentenceCount = len(self._sentences)
        self.questionCount = self.countQuestions(self._taggedSentences, config)
        self.verbCount = self.countVerbs(self._taggedSentences)
        self.modalVerbCount = self.countModalVerbs(self._taggedSentences)
        self.presentTenseVerbCount = self.countPresentTenseVerbs(self._taggedSentences)
        self.punctuationCount = self.countPunctuation(self._taggedSentences)
        self.punctuationPerSentence = ((self.punctuationCount / self.sentenceCount) if self.sentenceCount > 0 else 0)
        self.hasGreeting = self.includesGreeting(self._sentences, config)
        self.hasSignoff = self.includesSignoff(self._sentences, config)

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

def initializeFeatureExtractor():
    config = dict()
    messageDelimiters = ['(.*)From: '] #Marks start of replied to message in email body
    config['messageDelimitersRE'] = re.compile('|'.join(messageDelimiters))

    config['sentenceSplitter'] = nltk.data.load('tokenizers/punkt/english.pickle')

    config['fields'] = [
        'sentenceCount',
        'wordCount',
        'presentTenseVerbCount',
        'modalVerbCount',
        'punctuationCount'
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

    return (config)

def printHeaders(fields):
    allFields = fields + ['subject', 'message']
    print("|".join(allFields))
          
def splitThread(text, myConfig):
    '''
    return list of messages
    '''
    myMatch = myConfig['messageDelimitersRE'].search(text)
    if myMatch == None:
        return(text)
    else:
        return (myMatch.group(0))

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
                words = word_tokenize(sentence)
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

    #C. Meaningful bigrams

    #Write out results
    
if (__name__ == '__main__'):
    config = initializeFeatureExtractor()
    printHeaders(config['fields'])
    extractFeatures(config)


