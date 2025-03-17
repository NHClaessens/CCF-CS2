import os
import csv
import util
import argparse

def get_files(dir_src, dir_dest):
	relevant_log = []
	files = os.listdir(dir_src)
#	print(files)
	for file in files:
		if "001.log" in file:
			 relevant_log.append(file)
#	print(relevant_log)
	for file in relevant_log:
		file = dir_src + "/" + file
		extract_chat(file, dir_dest)

def extract_chat(file, dir_dest):
	log_name = os.path.basename(file).split('/')[-1]
	log_name = dir_dest + "/" + log_name.rsplit(".", 1)[0]
	log_all = log_name + "_all.csv"
	log_ct = log_name + "_ct.csv"
	log_ter = log_name + "_ter.csv"
	with open (file, "r") as lines:
		for line in lines:
			if "say" in line:
				print(line)
				write_to_file(log_all, line)
			if "say_team" in line and "<ct>" in line:
				write_to_file(log_ct, line)
			if "say_team" in line and "<TERRORIST>" in line:
				write_to_file(log_ter, line)

def write_to_file(file, line):
	with open(file, 'a+') as f:
		writer = csv.writer(f)
		writer.writerow([line])





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='cs2 logs parser for entire folder')
    parser.add_argument('--srcdir', type=util.dir_path, help='Path to the directory containing .log files')
    parser.add_argument('--dstdir', type=util.dir_path, help='Path to the directory for output')
    parser.add_argument('--srcfile', type=util.file_path, help='path to soruce file')
    args = parser.parse_args()
    if args.srcdir and args.dstdir:
        get_files(args.srcdir, args.dstdir)
    if args.srcfile and args.dstdir:
        extract_chat(args.srcfile, args.dstdir)

