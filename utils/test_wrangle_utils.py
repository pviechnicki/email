import unittest
import zipfile
import sys
import simplejson as json
import pandas as pd
import os
from wrangle_utils import initialize_wrangle_config
from io import BytesIO
from collections import defaultdict


'''
tests all functions in wrangle.utils
'''

class TestWrangleFuncs(unittest.TestCase):

	
	def setUp(self):
		sys.path.append("../utils")
		from load_directories import directory_loader
		input_directory, output_directory = directory_loader("..")
		self.input_directory = input_directory


	def tearDown(self):
		return

	def test_irm_decrypt(self):
		'''
		tests that if you feed the function an encrypted zip it returns a decrypted zip with 4 json files
		'''
		from wrangle_utils import irm_decrypt
		test_directory = self.input_directory
		test_zipfilename = '2018-01-23Z00.56.06.192.zip.aes'

		decrypted_zip = irm_decrypt(test_zipfilename, test_directory)
		fileLikeZip = BytesIO(decrypted_zip)
		with zipfile.ZipFile(fileLikeZip) as z:
			filenames =   [fn for fn in z.namelist()]
			for filename in filenames:
				self.assertEqual(filename[-5:],'.json', "Unrecognized file format {}: expecting .json".format(filename))
			self.assertEqual(len(filenames),4, "Expecting 4 files, found {}".format(len(filenames)))

	def test_parse_json_object(self):

		'''
		tests that if you pass a email in the form of a json string 
		it returns the correct parts for message id, subject, attachment count, sent dat, importance, body, sensitivity, and org_unit
		'''
		from wrangle_utils import parse_json_object
		test_json_filename = self.input_directory + '//' + 'Test'+'//' + 'TEST.json'
		with open(test_json_filename) as f:
			test_json_file = f.read()


		test_json_str = json.loads(test_json_file)

		correct_test_return = ({},'test@test.state.tld', 'of referring', 'hello', '2017-11-06T23:59:26', 'Normal', 'The Real American Love Story', 'Sensitivity Official', 'Enterprise Services,eRecords,eRecords Service Accounts', True, '', '', '', '', '', 'False')

		self.assertEqual(parse_json_object(test_json_str, 1, defaultdict(list), test=True), (correct_test_return))

	def test_remove_non_ascii_characters(self):
		'''
		tests that if you feed the function a non-ascii character it will return an empty string
		'''
		from wrangle_utils import remove_non_ascii_characters
		self.assertEqual(remove_non_ascii_characters('ð'),'')
		
	def test_dont_remove_ascii_characters(self):
		'''
		Converse: checks that you're not removing any ascii characters by accident
		Inspiration from https://stackoverflow.com/questions/5891453/is-there-a-python-library-that-contains-a-list-of-all-the-ascii-characters/5891509
		'''
		from wrangle_utils import remove_non_ascii_characters
		all_ascii_chars = ''.join([chr(i) for i in range(128)])
		self.assertEqual(remove_non_ascii_characters(all_ascii_chars), all_ascii_chars)
		

	def test_containsPII(self):
		'''
		tests that if text contains words 'birth date' then the function will return true and if the text is hello world that the function will return false
		'''
		from wrangle_utils import containsPII
		os.chdir("..\wrangle")
		wrangleConfig = initialize_wrangle_config()

		self.assertTrue(containsPII('birth date', wrangleConfig))
		self.assertFalse(containsPII('hello world', wrangleConfig))

	def test_create_df(self):
		'''
		tests that if you pass the function variables it assigns those variables to the correct column and writes to the dataframe
		'''
		from wrangle_utils import create_df

		test_email_df = pd.DataFrame(columns = ['messageId', 'subject', 'sent_date', 'importance', 'body','sensitivity', 'is_transitory','attachments','is_state','org_unit', 'user_type', 'country', 'department', 'office', 'division'])
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['messageId'].iloc[0],'1')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['subject'].iloc[0],'hello')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['sent_date'].iloc[0],'1/1/2018')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['importance'].iloc[0],'high')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['body'].iloc[0],'hello world')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['sensitivity'].iloc[0],'Sensitivity Personal')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['org_unit'].iloc[0],'IRM')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['is_state'].iloc[0],'Yes')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['user_type'].iloc[0],'contractor')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['country'].iloc[0],'USA')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['department'].iloc[0],'IRM/MSO')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['office'].iloc[0],'SA-28')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['division'].iloc[0],'MD')
		self.assertEqual(create_df('1','hello','0','1/1/2018','high','hello world','Sensitivity Personal','IRM','Yes','contractor','USA','IRM/MSO','SA-28','MD','False',test_email_df,False,0)['is_transitory'].iloc[0],'False')

if __name__ == "__main__":
	unittest.main()
	