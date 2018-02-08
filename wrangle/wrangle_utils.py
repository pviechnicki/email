import base64
import sys
import string
import re
import yaml
import simplejson as json
from io import StringIO
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2

class AESCipher:
	'''AES Cipher Class'''
	def __init__( self, key ):
		self.key = key.encode('utf-8')
		#hashlib.sha256(key.encode('utf-8')).digest()

	def decrypt( self, enc ):
	   	# enc = enc.decode('utf8')  
		# first 32 bytes are salt
		salt = enc[:32]
	   	# generate password using key and salt, 32 block size, 1000 iters   
		password = PBKDF2(self.key, salt, 32, 1000)
		# take first 32 bytes as the key
		keyBytes = password[:32]
		# use key and first 16 of password for the IV
		cipher = AES.new(keyBytes, AES.MODE_CBC, password[:16] )
		#return unpad(cipher.decrypt( enc[32:] ))
		# return unpad(cipher.decrypt(enc[32:]))
		return cipher.decrypt(enc[32:])

def irm_decrypt(file_name, directory):
	''' 
	decrypts file from file path name and returns decrypted json file
	'''

	#Make sure the input is a zip file aes encryption
	if (file_name[-8:] == '.zip.aes'):

		unpad = lambda s : s[0:-s[-1]]


		cipher = AESCipher('Password1')
		sys.path.insert(0, directory)
		# with zipfile.ZipFile(directory + '//' + file_name) as z:
		with open(directory + '//' + file_name, 'rb') as f:
			txt = f.read()

		decrypted_zip = cipher.decrypt(txt)

		with open('outfile.zip', 'wb') as outfile:
			outfile.write(decrypted_zip)

		return decrypted_zip
	else: 
		sys.stderr.write("Warning: Unrecognized file type {} passed to irm_decrypt. Skipping.".format(fn))
		return None




def parse_json_object(json_text):
	'''
	extracts relevant information from the json object and returns variables that contain information
	'''
	exclude = set(string.punctuation)
	properties_list = json_text['metadata']['properties']
	messageId = json_text['metadata']['message']['messageId']
	subject = json_text['metadata']['message']['subject']
	attachment_count = json_text['metadata']['attachments']
	sent_date = json_text['metadata']['message']['sentDate']
	importance = json_text['metadata']['message']['importance']
	org_unit = json_text['metadata']['users'][1]['orgUnit']
	body = json_text['metadata']['message']['plainTextBody']
	body = body.replace('\r\n','')
	sensitivity = str(next((p.values() for p in properties_list if p.get('key')== 'Sensitivity')))
	sensitivity = sensitivity.replace('dict_values','')
	sensitivity = ''.join(ch for ch in sensitivity if ch not in exclude)
	sensitivity.strip()

	return messageId, subject, attachment_count, sent_date, importance, body, sensitivity, org_unit

def initialize_wrangle_config():
	'''
	Initialize lookup tables and other config stuff one time, not for each file
	'''
	configContainer = {} #Empty dict to hold configuration info
	with open('PII_words.yaml', 'r') as P:
		PII_words_file = yaml.load(P)

		configContainer['PII_words'] = PII_words_file['PII']

	with open('column_titles_json.yaml', 'r') as f:
		configContainer['column_titles'] = yaml.load(f)

	return configContainer

def remove_non_ascii_characters(body):
	'''
	takes body of email and removes non-ascii characters
	'''

	assert type(body) is str 

	return ''.join([i if ord(i)<128 else '' for i in body])

def containsPII(emailText, configContainer):
	'''
	tests for PII and returns either a variable called Sensitive to indicate whether the email contains sensitive information
	'''
	result = False

	SSN = re.search(r'\d\d\d-\d\d-\d\d\d\d', emailText)

	if SSN:
		result = True
	else:
		for item in configContainer['PII_words']:
			PII = re.search(item, emailText)
			if PII:
				result = True
				break
	
	return result

def create_df(messageId, subject, attachment_count, sent_date, importance, body, sensitivity, org_unit, email_df, Sensitive, index):
	'''
	Turns variables parsed from json object into dataframe if emails do not contain sensitive PII
	'''
	if Sensitive == False:
		email_df.loc[index] = [messageId, subject, sent_date, importance, body, sensitivity, attachment_count, org_unit]
	else: 
		print('email removed due to sensitive information in the body')

	return email_df

