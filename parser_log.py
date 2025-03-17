import os
import csv
import util
import argparse
import re

def get_files(dir_src, dir_dest):
	relevant_log = []
	files = os.listdir(dir_src)
	for file in files:
		if "001.log" in file:
			 relevant_log.append(file)
	for file in relevant_log:
		file = dir_src + "/" + file
		extract_chat(file, dir_dest)

def extract_chat(file, dir_dest):
	log_name = os.path.basename(file).split('/')[-1]
	log_name = dir_dest + "/" + log_name.rsplit(".", 1)[0]
	log_all = log_name + "_world.csv"
	log_ct = log_name + "_ct.csv"
	log_ter = log_name + "_ter.csv"
	with open (file, "r") as lines:
		for line in lines:
			if "say" in line:
				pattern = r'L (\d{2}/\d{2}/\d{4} - \d{2}:\d{2}:\d{2}): "(.*?)<.*?><.*?><(.*?)>" say "(.*?)"'
				match = re.match(pattern, line)
				if match:
					line = [match.group(1),match.group(2),match.group(3),match.group(4)]
					write_to_file(log_all, line)
			if "say_team" in line and "<CT>" in line:
				pattern = r'L (\d{2}/\d{2}/\d{4} - \d{2}:\d{2}:\d{2}): "(.*?)<.*?><.*?><(.*?)>" say_team "(.*?)"'
				match = re.match(pattern, line)
				if match:
					line = [match.group(1),match.group(2),match.group(3),match.group(4)]
					write_to_file(log_ct, line)
			if "say_team" in line and "<TERRORIST>" in line:
				pattern = r'L (\d{2}/\d{2}/\d{4} - \d{2}:\d{2}:\d{2}): "(.*?)<.*?><.*?><(.*?)>" say_team "(.*?)"'
				match = re.match(pattern, line)
				if match:
					line = [match.group(1),match.group(2),match.group(3),match.group(4)]
					write_to_file(log_ter, line)

def write_to_file(file, line):
	file_exists = os.path.isfile(file)
	with open(file, 'a+') as f:
		writer = csv.writer(f)
		if not file_exists:
			writer.writerow(['Time', 'User', 'Team', 'Message'])
		writer.writerow(line)





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='cs2 logs parser for entire folder')
    parser.add_argument('--srcdir', type=util.dir_path, help='Path to the directory containing .log files')
    parser.add_argument('--dstdir', type=util.dir_path, required=True, help='Path to the directory for output')
    parser.add_argument('--srcfile', type=util.file_path, help='path to soruce file')
    args = parser.parse_args()
    if args.srcdir and args.dstdir:
        get_files(args.srcdir, args.dstdir)
    elif args.srcfile and args.dstdir:
        extract_chat(args.srcfile, args.dstdir)
    else:
        raise argparse.ArgumentTypeError(f"need either a source file or a source directory")
