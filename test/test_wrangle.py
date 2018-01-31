import unittest
import sys
import pandas as pd
sys.path.insert(0, 'C:/Users/ComputerA/email_marker/src/wrangle')
from wrangle_utils import irm_decrypt
from wrangle_utils import load_json_file
from wrangle_utils import parse_json_object
from wrangle_utils import remove_non_ascii_characters
from wrangle_utils import filter_sensitive_emails
from wrangle_utils import create_df

'''
tests all functions in wrangle.utils
'''

class TestWrangleFuncs(unittest.TestCase):

	# def test_irm_decrypt(self):
	# 	'''
	# 	tests that the first two characters in the decrypted object (result_text) are {"
	# 	'''
	# 	self.assertEqual(irm_decrypt('DeloitteEncrypyted','C:/Users/ComputerA/email_marker/data/Encrypted_Test')[:10],'{"birthId"')

	# def test_load_json_file(self):
	# 	'''
	# 	tests that the object returned from the json loader is a json object
	# 	'''
	# 	self.

	# def test_parse_json_object(self):
	# 	'''
	# 	tests that the word sensitivity is contained in the value for sensitivity. Sensitivity should be either 'Sensitivity Personal' or 'Sensitivity Official'
	# 	'''
	# 	_, _, _, _, _, _, sensitivity = parse_json_object()
	# 	self.assertIn('Sensitivity', sensitivity)

	def test_remove_non_ascii_characters(self):
		'''
		tests that if you feed the function a non-ascii character it will return an empty string
		'''
		self.assertEqual(remove_non_ascii_characters('ð'),'')
		self.assertEqual(remove_non_ascii_characters('hello world'), 'hello world')
		

	def test_filter_sensitive_emails(self):
		'''
		tests that if text contains words 'birth date' then the function will return true and if the text is hello world that the function will return false
		'''
		self.assertTrue(filter_sensitive_emails('birth date'))
		self.assertFalse(filter_sensitive_emails('hello world'))

	def test_create_df(self):
		'''
		tests that if you pass the function variables it assigns those variables to the correct column and writes to the dataframe
		'''
		test_email_df = pd.DataFrame(columns = ['messageId', 'subject', 'sent_date', 'importance', 'body', 'sensitivity', 'attachment_count'])
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal',test_email_df,False,0)['messageId'].iloc[0],'1')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal',test_email_df,False,0)['subject'].iloc[0],'hello')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal',test_email_df,False,0)['sent_date'].iloc[0],'1/1/2018')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal',test_email_df,False,0)['importance'].iloc[0],'high')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal',test_email_df,False,0)['body'].iloc[0],'hello world')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal',test_email_df,False,0)['sensitivity'].iloc[0],'Sensitivity Personal')



if __name__ == '__main__':
	unittest.main()
