import os
import yaml
import sys
sys.path.insert(0, 'C:/Users/ComputerA/email_marker/REPO/data/Input/DevEncrypted_Test')
sys.path.insert(0, 'C:/Users/ComputerA/email_marker/REPO/data/Output')
import pandas as pd
import zipfile
import simplejson as json
from wrangle_utils import irm_decrypt
from wrangle_utils import parse_json_object
from wrangle_utils import remove_non_ascii_characters
from wrangle_utils import filter_sensitive_emails
from wrangle_utils import create_df

'''
Iterates through directory of encrypted zip files.

For each zip file:
	Step 1: Create empty dataframe (Master_df)
	Step 2: Decrypt zip file
	Step 3: Unzip file
	Step 4: Iterate through each file in zip file. For each file in zip...
		1) 

'''

directory = 'C:/Users/ComputerA/email_marker/REPO/data/Input/DevEncrypted_Test'

with open('column_titles_json.yaml', 'r') as f:
	column_titles = yaml.load(f)

df_columns = column_titles['df_columns']

Master_df = pd.DataFrame(columns= df_columns)

for fn in os.listdir(directory):
	try:
		assert fn[-8:] == '.zip.aes'
	
		decrypyed_zip = irm_decrypt(fn, directory)
		email_df = pd.DataFrame(columns = df_columns)
		try:
			assert email_df.empty == True

			with zipfile.ZipFile('outfile.zip') as z:
				json_files = [fn for fn in z.namelist()]
				for index, fn in enumerate(json_files):
					try:
						assert fn[-5:] == '.json'
						with z.open(fn) as f:
							json_str = f.read()
							json_text = json.loads(json_str)
							messageId, subject, attachment_count, sent_date, importance, body, sensitivity, org_unit = parse_json_object(json_text)
							body = remove_non_ascii_characters(body)
							Sensitive = filter_sensitive_emails(body)
							email_df = create_df(messageId, subject, attachment_count, sent_date, importance, body, sensitivity, org_unit, email_df, Sensitive, index)

					except:
						print('ERROR: FILE INSIDE ZIP WAS NOT A JSON')
	
		except:
			print('ERROR: email_df was not an empty DataFrame')
		

		Master_df = Master_df.append(email_df)

	except:
		print('ERROR: FILE IN DATA DIRECTORY WAS NOT AN ENCRYPTED ZIP')

Master_df.to_csv('C:/Users/ComputerA/email_marker/data/output/Master_df.csv')	
