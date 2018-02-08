import os
import yaml
import sys
import pandas as pd
import zipfile
import simplejson as json
from wrangle_utils import irm_decrypt
from wrangle_utils import parse_json_object
from wrangle_utils import remove_non_ascii_characters
from wrangle_utils import containsPII
from wrangle_utils import create_df
from wrangle_utils import initialize_wrangle_config #Do all the initialization of lookup tables one time
import getopt
from io import BytesIO #needed to read in-memory version of zip file


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
	sys.stdout.write("Usage: python wrangle.py [-d|--directory= <directory name with zipped email files>] [-n|--number= <number of output emails requested>] [-h|?|--help]")	

def wrangle():

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
			dataDirectory = a
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

	for fn in os.listdir(dataDirectory):
		#Only open number of files neceesary for email requested
		if (emailCounter > numberRequested):
			break
		else:

			decrypted_zip = irm_decrypt(fn, dataDirectory)
			fileLikeZip = BytesIO(decrypted_zip)
		
			email_df = pd.DataFrame(columns = df_columns)
			try:
				assert email_df.empty == True
			except:
				sys.stderr.write('wrangle.py ERROR: email_df was not an empty DataFrame')
				return False

			with zipfile.ZipFile(fileLikeZip) as z:
				json_files = [fn for fn in z.namelist()]
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
						messageId, subject, attachment_count, sent_date, importance, body, sensitivity, org_unit = parse_json_object(json_text)
						body = remove_non_ascii_characters(body)
						Sensitive = containsPII(body, wrangleConfig)
						email_df = create_df(messageId, subject, attachment_count, sent_date, importance, body, sensitivity, org_unit, email_df, Sensitive, index)
				

			Master_df = Master_df.append(email_df)

	Master_df.to_csv('Master_df.csv')	

	return True

if __name__ == "__main__":
	wrangle()
