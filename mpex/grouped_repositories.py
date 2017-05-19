#!/usr/bin/env python3

import collections
import json
import os
import subprocess

def check_output_no_ret(*popenargs, **kwargs):
	""" see subprocess.check_output """
	if 'stdout' in kwargs:
		raise ValueError('stdout argument not allowed, it will be overridden.')
	process = subprocess.Popen(stdout=subprocess.PIPE, stderr=subprocess.PIPE, *popenargs, **kwargs)
	output, unused_error = process.communicate()
	unused_retcode = process.poll()
	return output

def annex_whereis(path):
	"""
	capture the output of 'git annex whereis'
	"""
	os.chdir(path)
	cmd = ["git-annex","whereis","--json"]
	return check_output_no_ret(cmd)


def parse_annex_whereis(raw, omit_untrusted=False):
	"""
	parse 'git annex whereis --json' output,
	returns a dictionary with the filename -> uuid association
	and a dictionary with the uuids > description association
	"""
	# remember the uuids which hold the file
	files = collections.defaultdict(list)
	# remember the uuid to description association
	repositories = {}
	for line in raw.decode("utf-8").split('\n'):
		# skip empty lines
		if not line:
			continue
		# load json
		j = json.loads(line)
		# get file path
		filepath = j["file"]
		# we trust whereis, but we do not trust untrusted
		whereis = []
		for d in j["whereis"]:   whereis.append( (d,True) )
		if not omit_untrusted:
			for d in j["untrusted"]: whereis.append( (d,False) )
		
		for whereis_dictionary,trusted in whereis:
			# create decent short cuts
			description, uuid = whereis_dictionary["description"], whereis_dictionary["uuid"]
			# mark untrusthworthy repositories
			if not trusted:
				description += " [untrusted]"
			# this uuid has the file
			files[filepath].append(uuid)
			# remember uuid -> description
			if not uuid in repositories:
				repositories[uuid] = description
		
	# return parsed data
	return files, repositories


def group_files(files):
	"""
		group the file -> uuid association,
		returns a dictionary with the the association set of uuids -> files
	"""
	grouped = collections.defaultdict(list)
	
	for filepath, uuids in files.items():
		grouped[frozenset(uuids)].append(filepath)
		
	return grouped


class Directory:
	def __init__(self, name, parent=None):
		self.name = name
		self.parent = parent
		self.dirs = []
		self.grouped = collections.defaultdict(list)

	def get_name(self):
		if not self.parent:
			return self.name
		parent = self.parent.get_name()
		# special case root: has an empty name
		if not parent:
			return self.name
		# standard case
		return os.path.join(parent,self.name)

	def get_directory(self, directory_name):
		for sub_directory in self.dirs:
			if sub_directory.name == directory_name:
				return sub_directory
		else:
			sub_directory = Directory(directory_name,self)
			self.dirs.append(sub_directory)
			return sub_directory

	def get_subfolder(self,subfolder):
		# subfolder is a list
		if not subfolder:
			return self

		sub_directory = self.get_directory(subfolder[0])
		return sub_directory.get_subfolder(subfolder[1:])
	
	def get_description(self):
		if not self.grouped and not self.dirs:
			return None # can be anything
		
		description = collections.defaultdict(list)
		
		# gather information
		for uuids,filepaths in self.grouped.items():
			description[uuids].extend(filepaths)
		for sub_directory in self.dirs:
			sub_description = sub_directory.get_description()
			# could be None
			if sub_description:
				for uuids, sub_list in sub_description.items():
					description[uuids].extend(sub_list)
		
		# judge: if only one uuid occurs, replace all the individual files with self
		if len(description) == 1:
			uuid = description.popitem()[0]
			description[uuid].append(self)
		
		return description
	
	def get_file_count(self):
		return sum(len(filepaths) for filepaths in self.grouped.values()) + sum(sub_dir.get_file_count() for sub_dir in self.dirs)

def full_split(filepath):
	""" returns the sub folder list and the file name """
	# get file name
	path, filename = os.path.split(filepath)
	# special case empty path 
	if not path:
		return [], filename
	# prepare split_path
	split_path = [path]
	
	# we call split until there is nothing to split anymore
	while True:
		split = os.path.split(split_path[0])
		if not split[0]:
			break
		# if the split was succesful, replace the first item in split_filepath
		split_path[0:1] = split
		
	return split_path, filename


def group_files_hierarchical(files):
	"""
		group the file -> uuid association and preserve folder structure
	"""
			
	root = Directory("")
	
	for filepath, uuids in files.items():
		split_path, filename = full_split(filepath)
		# get containing sub folder
		subfolder = root.get_subfolder(split_path)
		# add file
		subfolder.grouped[frozenset(uuids)].append(filepath)
	
	return root 


def get_file_count_from_mixed_list(mixed_directory_file_list):
	# split it up
	directories = [element for element in mixed_directory_file_list if isinstance(element,Directory)]
	files = [element for element in mixed_directory_file_list if not isinstance(element,Directory)]
	return sum(d.get_file_count() for d in directories) + len(files)


ModeMap = {
		'reset':		0,
		'bright':		1,
		'underscore':	4,
		'blink':		5,
		'reverse':		7,
		'hidden':		8
}
TerminalColorMap = {
		'black': 	30,
		'red':		31,
		'green':	32,
		'yellow':	33,
		'blue':		34,
		'magenta':	35,
		'cyan':		36,
		'white':	37,
}
def colored_format(text, index):
	available_colors = ['red','green','yellow','blue','magenta','cyan']
	
	code_to_str = lambda x: ("\033[%sm" % x)
	
	codepoint = TerminalColorMap[available_colors[ index % len(available_colors) ]]
	
	return "{color}{text}{reset}".format(
				color = code_to_str( codepoint ),
				text = text,
				reset = code_to_str( 0 )
			)


# noinspection PyArgumentList
def print_report(root, repositories, number_of_content_lines = 5):
	# sort uuids by size
	description = sorted(root.get_description().items(),
						 key=lambda kv:get_file_count_from_mixed_list(kv[1]),
						 reverse=True)
	
	# sort by occurences
	flattened_list = sum((list(uuids) for uuids,_ in description), [])
	counter_dict = collections.Counter(flattened_list)
	sorted_repos = sorted(repositories.items(),
						key=lambda kv: (-counter_dict[kv[0]],kv[1]))
	
	for uuids, mixed_directory_file_list in description:
		# print header
		repo_names = [colored_format(name,i)
							for i,(uuid,name) in enumerate(sorted_repos)
							if uuid in uuids]
		repo_names = ", ".join(repo_names)
		file_count = get_file_count_from_mixed_list(mixed_directory_file_list)
		print("repositories {repos} ({count} files)".format(repos=repo_names,count=file_count))	   

		# split it up
		directories = [element for element in mixed_directory_file_list if isinstance(element,Directory)]
		files = [element for element in mixed_directory_file_list if not isinstance(element,Directory)]

		# sort it (show big folders first)

		# lexigraphic sort order
		directories.sort(key=lambda e: e.get_name())
		# then sort by folder size (big ones are first)
		directories.sort(key=lambda e: e.get_file_count(), reverse=True)
		files.sort()

		# reverse so we can use pop
		directories.reverse()
		files.reverse()

		# create a counter so we don't overshoot our target
		elements_printed = 0

		while directories and elements_printed < number_of_content_lines:
			directory = directories.pop()
			folder_name = directory.get_name() + os.path.sep # trailing sep
			folder_count = directory.get_file_count()
			file_count += folder_count
			print("\t",folder_name,"(%d files)" % folder_count)
			elements_printed += 1

		while files and elements_printed < number_of_content_lines:
			filepath = files.pop()
			print("\t",filepath)
			elements_printed += 1

		# report omitted data
		omitted_comment = []

		# care about directories
		if directories:
			directory_count = len(directories)
			file_count = sum(d.get_file_count() for d in directories)
			comment = "{d_count} directories with {f_count} files".format(d_count=directory_count,f_count=file_count)
			omitted_comment.append(comment)

		if files:
			file_count = len(files)
			comment = "{f_count} ungrouped files".format(f_count=file_count)
			omitted_comment.append(comment)

		if omitted_comment:
			print("\t<omitted {comment}>".format(comment=" and ".join(omitted_comment)))
		
		print()

def do_report(path, number_of_content_lines=5, omit_untrusted=False):
	raw = annex_whereis(path)
	files, repositories = parse_annex_whereis(raw,omit_untrusted=omit_untrusted)
	#grouped = group_files(files)
	root = group_files_hierarchical(files)
	print_report(root, repositories, number_of_content_lines)

if __name__ == "__main__":
	import sys
	if len(sys.argv) < 2:
		print("first argument has to be a git annex path")
		sys.exit(2)
	# save first argument
	path = sys.argv[1]
	
	# second argument is the number of content lines, default is 5
	try:
		number_of_content_lines = int(sys.argv[2])
	except:
		number_of_content_lines = 5
	
	omit_untrusted = False
	
	# create and print the report
	do_report(path,number_of_content_lines,omit_untrusted=omit_untrusted)

