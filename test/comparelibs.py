import pandas as pd 

with open('requirements.txt', 'r') as r, open('dotce_libs.txt', 'r') as c:
	requirements = r.readlines()
	current = c.readlines()
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


packages_needed = set(requirements_no_version) - set(current_no_version)

packages_needed = str(packages_needed)

with open('packages_needed.txt', 'w') as pn:
	pn.write(packages_needed)



