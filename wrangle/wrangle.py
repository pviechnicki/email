import os
import yaml
import sys
import pandas as pd
import zipfile
import simplejson as json
import math
from wrangle_utils import irm_decrypt
from wrangle_utils import parse_json_object
from wrangle_utils import remove_non_ascii_characters
from wrangle_utils import containsPII
from wrangle_utils import create_df
from wrangle_utils import initialize_wrangle_config #Do all the initialization of lookup tables one time
import getopt
from io import BytesIO #needed to read in-memory version of zip file
from wrangle_utils import directory_loader
from collections import defaultdict



'''
Iterates through directory of encrypted zip files.

For each zip file:
	Step 1: Create empty dataframe (Master_df)
	Step 2: Decrypt zip file
	Step 3: Create empty dataframe to contain contents of zip file (email_df)
	Step 3: Unzip file
	Step 4: Iterate through each file in zip file. For each file in zip...
		1) load as json string
		2) parse out relevant fiels (message id, subject, attachment count, sent date, importance, body sensitivity, org unit)
		3) remove non ascii characters from the body of the email
		4) discard any emails with birth dates or SSNs
		5) append to email_df
	Step 5: Append email_df to Master_df

Write Master_df to a csv in output data folder

'''

def usage():
	sys.stdout.write("Usage: python wrangle.py [-d|--directory= <top directory of the github repository where your directory yaml sits>] [-n|--number= <number of output emails requested>] [-h|?|--help]")	

def wrangle():
	#set default for numberRequested
	numberRequested = math.inf

	#Get and parse command line args
	try:
		opts, args = getopt.getopt(sys.argv[1:], "d:n:h?", ["--directory=", "--number=", "--help"])
	except getopt.GetoptError as err:
		#Exit if can't parse args
		usage()	
		sys.exit(2)
	for o, a in opts:
		if (o == '-h' or o == '-?'):
			usage()
			exit(0)
		elif o in ('-d', '--directory'):
			yaml_directory = a
			input_directory, output_directory = directory_loader(yaml_directory)

		elif o in ('-n', '--number'):
			try:
				numberRequested = int(a)
			except:
				sys.stder.write("Argument to -n|--number= option must be integer.")
				sys.exit(2)
		else:
			assert False, "wrangle.py unhandled option: {}".format(o)

	#Initialize wrangle config
	wrangleConfig = initialize_wrangle_config()

	#Make copy of column names in local list
	df_columns = wrangleConfig['column_titles']['df_columns']

	Master_df = pd.DataFrame(columns=df_columns)

	#Set email counter to 0
	emailCounter = 0
	missing_fields_dict = defaultdict(list)
	weird_directories = dict()

	for zfn in os.listdir(input_directory):
		#Only open number of files neceesary for email requested
		if (emailCounter > numberRequested):
			break
		else:

			decrypted_zip = irm_decrypt(zfn, input_directory)
			fileLikeZip = BytesIO(decrypted_zip)
		
			email_df = pd.DataFrame(columns = df_columns)
			try:
				assert email_df.empty == True
			except:
				sys.stderr.write('wrangle.py ERROR: email_df was not an empty DataFrame')
				return False

			with zipfile.ZipFile(fileLikeZip) as z:
				json_files = [fn for fn in z.namelist()]
				try:
					assert len(json_files) == 30
				except:
					weird_directories[zfn] = len(json_files)
					# sys.stderr.write('wrangle.py ERROR: THERE WERE {} FILES IN THE DIRECTORY'.format(len(json_files)))

				for index, fn in enumerate(json_files):
					try:
						assert fn[-5:] == '.json'
					except:
						sys.stderr.write('wrangle.py ERROR: FILE {} INSIDE ZIP WAS NOT A JSON'.format(fn))
						return False
					

					emailCounter += 1
					
					#Only write output if we're below the number of emails requested
					if (emailCounter <= numberRequested):
						json_str = z.read(fn)
						json_text = json.loads(json_str)
						missing_fields_dict, messageId, subject, attachments, sent_date, importance, body, sensitivity, org_unit, is_state, user_type, country, department, office, division, is_transitory = parse_json_object(json_text, fn, missing_fields_dict)
						body = remove_non_ascii_characters(body)
						Sensitive = containsPII(body, wrangleConfig)
						email_df = create_df(messageId, subject, attachments, sent_date, importance, body, sensitivity, org_unit, is_state, user_type, country, department, office, division, is_transitory, email_df, Sensitive, index)
				

			Master_df = Master_df.append(email_df)
			
			
	print('ERROR: THESE FILES ARE MISSING FIELDS:')
	print(missing_fields_dict)
	print('------------------------------------------------------------------------------------------------------')
	print('ERROR: THESE ZIP FILES HAVE A WEIRD NUMBER OF FILES:')
	print(weird_directories)	
	Master_df.to_csv(path_or_buf=(output_directory + '//' + 'Master_df.bsv'), sep='|')	

	return True

if __name__ == "__main__":
	wrangle()
