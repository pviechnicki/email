import unittest
import zipfile
import sys
import simplejson as json
import pandas as pd
import os
# sys.path.append('../wrangle')
# from wrangle_utils import irm_decrypt
# from wrangle_utils import parse_json_object
# from wrangle_utils import remove_non_ascii_characters
# from wrangle_utils import containsPII
# from wrangle_utils import create_df
# from wrangle_utils import initialize_wrangle_config
from io import BytesIO
import getopt


'''
tests all functions in wrangle.utils
'''
def usage():
	sys.stdout.write("Usage: python test_wrangle.py [-d|--directory= <top directory of the github repository where your directory yaml sits>] [-h|?|--help]")	

def test():


	#Get and parse command line args
	try:
		opts, args = getopt.getopt(sys.argv[1:], "d:h?", ["--directory=",  "--help"])
	except getopt.GetoptError as err:
		#Exit if can't parse args
		usage()	
		sys.exit(2)
	for o, a in opts:
		if (o == '-h' or o == '-?'):
			usage()
			exit(0)
		elif o in ('-d', '--directory'):
			parent_path = a
			sys.path.insert(0, parent_path + '//' + 'utils')
			from load_directories import directory_loader
			from test_wrangle_utils import TestWrangleFuncs
			test_wrangle_funcs = TestWrangleFuncs()
			runner = unittest.TextTestRunner()
			results = runner.run(unittest.makeSuite(TestWrangleFuncs))


		else:
			assert False, "test_wrangle.py unhandled option: {}".format(o)

	
if __name__ == "__main__":
	test()