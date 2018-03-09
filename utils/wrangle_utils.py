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
import yaml
import os


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
		sys.stderr.write("Warning: Unrecognized file type {} passed to irm_decrypt. Skipping.".format(file_name))
		return None




def parse_json_object(json_text, fn, missing_fields_dict, test=False):
	'''
	extracts relevant information from the json object and returns variables that contain information
	'''
	exclude = set(string.punctuation)
	properties_list = json_text['metadata']['properties']
	messageId = json_text['metadata']['message']['messageId']
	subject = json_text['metadata']['message']['subject']
	try:
		attachments = json_text['metadata']['attachments'][0]['text']
	except:
		attachments = json_text['metadata']['attachments']
	sent_date = json_text['metadata']['message']['sentDate']
	importance = json_text['metadata']['message']['importance']
	user_role_list = json_text['metadata']['users']
	try:
		from_dict = next(item for item in user_role_list if item["userRoles"] == ['From'])
	except StopIteration:
		try:
			from_dict = next(item for item in user_role_list if item["userRoles"] == ['From', 'Cc'])
		except:
			from_dict = next(item for item in user_role_list if item["userRoles"] == ['From', 'To'])
	org_unit = from_dict['orgUnit']
	is_state = from_dict['isState']
	try:
		user_type = from_dict['userType']
	except KeyError:
		user_type = ''
		missing_fields_dict[fn].append('user_type')
		
	try:
		country = from_dict['country']
	except KeyError:
		country = ''
		missing_fields_dict[fn].append('country')
	try:
		department = from_dict['department']
	except KeyError:
		department = ''
		missing_fields_dict[fn].append('department')
	try:
		office = from_dict['office']
	except KeyError:
		office = ''
		missing_fields_dict[fn].append('office')
	try:	
		division = from_dict['division']
	except KeyError:
		division = ''
		missing_fields_dict[fn].append('division')
	

	body = json_text['metadata']['message']['plainTextBody']
	body = body.replace('\r\n','')
	sensitivity = str(next((p.values() for p in properties_list if p.get('key')== 'Sensitivity')))
	sensitivity = sensitivity.replace('dict_values','')
	sensitivity = ''.join(ch for ch in sensitivity if ch not in exclude)
	sensitivity.strip()
	is_transitory = str(next((p.values() for p in properties_list if p.get('key')== 'IsTransitory')))
	is_transitory = is_transitory.split(",")
	is_transitory = is_transitory[1]
	is_transitory = ''.join(ch for ch in is_transitory if ch not in exclude)
	is_transitory = is_transitory.strip()

	if test == True:
		missing_fields_dict = {}

	else:
		missing_fields_dict = missing_fields_dict
	return missing_fields_dict, messageId, subject, attachments, sent_date, importance, body, sensitivity, org_unit, is_state, user_type, country, department, office, division, is_transitory

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

def create_df(messageId, subject, attachments, sent_date, importance, body, sensitivity, org_unit, is_state, user_type, country, department, office, division, is_transitory, email_df, Sensitive, index):
	'''
	Turns variables parsed from json object into dataframe if emails do not contain sensitive PII
	'''
	if Sensitive == False:
		email_df.loc[index] = [messageId, subject, sent_date, importance, body, sensitivity, is_transitory, attachments, is_state, org_unit, user_type, country, department, office, division]
	else: 
		print('email removed due to sensitive information in the body')

	return email_df
