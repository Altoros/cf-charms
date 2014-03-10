# Edit file functions
import os


def replace(file_name, replaces=[]):
    tmp_file_name = '{}.next'.format(file_name)
    with open(tmp_file_name, "wt") as fout:
        with open(file_name, "rt") as fin:
            for line in fin:
                new_line = line
                for replace in replaces:
                    new_line = new_line.replace(replace[0], replace[1])
                fout.write(new_line)
    os.rename(tmp_file_name, file_name)


def insert_line(file_name, new_line, substring, below=True, match_number=0):
    tmp_file_name = '{}.next'.format(file_name)
    i = 0
    with open(tmp_file_name, "wt") as fout:
        with open(file_name, "rt") as fin:
            for line in fin:
                add = ''
                if line.find(substring) > -1:
                    i += 1
                    if match_number == 0 or i == match_number:
                        if below:
                            add = new_line + "\n"
                        else:
                            fout.write(new_line)
                            fout.write("\n")
                fout.write(line + add)
    os.rename(tmp_file_name, file_name)
