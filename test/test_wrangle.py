import unittest
import zipfile
import sys
import simplejson as json
import pandas as pd
sys.path.insert(0, 'C:/Users/ComputerA/email_marker/REPO/wrangle')
from wrangle_utils import irm_decrypt
from wrangle_utils import parse_json_object
from wrangle_utils import remove_non_ascii_characters
from wrangle_utils import filter_sensitive_emails
from wrangle_utils import create_df

'''
tests all functions in wrangle.utils
'''

class TestWrangleFuncs(unittest.TestCase):

	def test_irm_decrypt(self):
		'''
		tests that if you feed the function an encrypted zip it returns a decrypted zip with 4 json files
		'''

		sys.path.insert(0,'C:/Users/ComputerA/email_marker/REPO/data/Input/EncrypyedZip_Test')

		test_directory = 'C:/Users/ComputerA/email_marker/REPO/data/Input/EncrypyedZip_Test'
		test_zipfilename = '2018-01-23Z00.56.06.192.zip.aes'

		decrypted_zip = irm_decrypt(test_zipfilename, test_directory)
		with zipfile.ZipFile('outfile.zip') as z:
				json_files = [fn for fn in z.namelist()]
		self.assertEqual(json_files[0][-5:],'.json')
		self.assertEqual(len(json_files),4)

	def test_parse_json_object(self):

		'''
		tests that if you pass a json string it returns the correct parts for message id, subject, attachment count, sent dat, importance, body, sensitivity, and org_unit
		'''

		sys.path.insert(0,'C:/Users/ComputerA/email_marker/REPO/data/Input/JSON_Test')
		test_json_filename = 'C:/Users/ComputerA/email_marker/REPO/data/Input/JSON_Test/TEST.json'
		with open(test_json_filename) as f:
			test_json_file = f.read()

		test_json_str = json.loads(test_json_file)

		correct_test_return = ('1AJPU7S4T2U4.9RRJTZ4W0TT41@mimefactory.state.tld', 'of referring to white political dominance. The', [], '2017-11-06T23:59:26', 'Normal', 'The Real American Love Story', 'Sensitivity Official', 'Enterprise Services,eRecords,eRecords Service Accounts')

		self.assertEqual(parse_json_object(test_json_str), correct_test_return)

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
		test_email_df = pd.DataFrame(columns = ['messageId', 'subject', 'sent_date', 'importance', 'body', 'sensitivity', 'attachment_count', 'org_unit'])
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM',test_email_df,False,0)['messageId'].iloc[0],'1')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM',test_email_df,False,0)['subject'].iloc[0],'hello')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM',test_email_df,False,0)['sent_date'].iloc[0],'1/1/2018')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM',test_email_df,False,0)['importance'].iloc[0],'high')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM',test_email_df,False,0)['body'].iloc[0],'hello world')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM',test_email_df,False,0)['sensitivity'].iloc[0],'Sensitivity Personal')



if __name__ == '__main__':
	unittest.main()
