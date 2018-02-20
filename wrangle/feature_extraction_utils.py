import pandas as pd
import nltk
import re
from nltk import pos_tag
from nltk import word_tokenize

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
    return (config)

def printHeaders(fields):
    allFields = fields + ['subject', 'message']
    print("|".join(allFields))
          
def splitThread(text, myConfig):
    '''
    return list of messages
    '''
    myMatch = config['messageDelimitersRE'].search(text)
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

