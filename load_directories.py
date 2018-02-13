import yaml

def directory_loader(yaml_directory):
	with open(yaml_directory + '//' + 'directories.yaml', 'r') as D:
		directories_file = yaml.load(D)

		input_directory = directories_file['Input']
		output_directory = directories_file['Output']

		input_directory = input_directory[0]
		output_directory = output_directory[0]

	return input_directory, output_directory

