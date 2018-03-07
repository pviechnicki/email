import pandas as pd 
import getopt
import sys

def usage():
	sys.stderr.write("usage: python comparelibs.py (-h|? show help) -1|--file1= <file1> -2|--file2= <file2> -v|--consider_versions")

def main():
	'''
	Compare two lists of libraries, note any differences, write out missing libs in needed_libraries.txt
	'''

	#Default values
	file1 = "requirements.txt"
	file2 = "dotce_libs.txt"
	versionsFlag = False

	try:
		opts, args = getopt.getopt(sys.argv[1:], "h?1:2:v", ["help", "file1=", "file2=", "consider_versions"])
	except getopt.GetoptError as err:
		print(err)
		sys.exit(2)
	for o, a in opts:
		if o in ("-h", "-?", "--help"):
			usage()
			sys.exit(0)
		elif o in ("-1", "--file1"):
			file1 = a
		elif o in ("-2", "--file2"):
			file2 = a
		elif o in ("-v", "--consider_versions"):
			versionsFlag = True
		else:
			assert False, "unhandled option"


	with open(file1, 'rt') as f1, open(file2, 'rt') as f2:
		requirements = f1.readlines()
		current = f2.readlines()
		requirements = set(requirements)
		current = set(current)

		requirements_no_version = list()
		current_no_version = list()

		for line in requirements:
			split = line.split("=")
			requirements_no_version.append(split[0])

		for line in current:
			split_current = line.split("=")
			current_no_version.append(split_current[0])

	if versionsFlag == False:
		packages_needed = set(requirements_no_version) - set(current_no_version)
	else:
		packages_needed = requirements - current

	packages_needed = str(packages_needed)

	sys.stdout.write(packages_needed)

	return True


if (__name__ == '__main__'):
	main()
