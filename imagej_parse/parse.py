"""
parse.py
-------------------------------------------------------------------------------------------------------------------
ABOUT:

Script to convert raw data from ImageJ into a convenient spreadsheet that can be opened from Excel for easy plotting.

-------------------------------------------------------------------------------------------------------------------
HOW TO USE:

Run within the directory that contains your input file.

Modify the variables in all caps below to customize the script.

Before starting, you need the following:
- INPUTFULE, the name of a tab-delimited text file from ImageJ. It should have a header row at the top
with the names of each column.
- OUTPUTFILE, a user-chosen name for the data that will be exported by this script
- ACTIVITY_THRESHHOLD, a change in pixel intensity above which a cell will be considered 'active' and incuded in the threshholded results 
- ROW_LABEL, a label for the rows in your excel sheet, which correspond to different cells
- COLUMN_LABEL, a label for the columns in your excel sheet, which correspond to image frames 
- FRAME_HEADER, the label in the header row of your raw data that corresponds to the item that indicates the frame or time point
- DATA_TO_EXTRACT, the label in the header row of your raw data that corresponds to the intensity value

-------------------------------------------------------------------------------------------------------------------
LICENSE:

Written by Phil Nova in 2016, under the MIT License:
'Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation 
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and 
to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial 
portions of the Software.'

Fork at: github.com/philnova
"""

##############################################################
##  MODIFY THESE VARIABLES ONLY! DO NOT MODIFY OTHER CODE!  ##
##############################################################

INPUTFILE = 'Results.txt'
OUTPUTFILE = 'Results_parsed'
ACTIVITY_THRESHHOLD = 15000
ROW_LABEL = 'roi'
COLUMN_LABEL = 'frame'

FRAME_HEADER = "Slice"
DATA_TO_EXTRACT = "IntDen"

##############################################################

import time

def get_indices_from_header(header_row, frame_header, data_to_extract, split_char = "\t"):
	"""Returns the positions within each line that hold the id of the frame and the 
	intensity data."""
	split_line = header_row.strip().split(split_char)
	frame_idx, data_idx = split_line.index(frame_header), split_line.index(data_to_extract)
	return (frame_idx, data_idx)


def extract_from_line(line, row_delim_idx, data_idx):
	return line.strip().split()[row_delim_idx], line.split()[data_idx]


def count_rows(filename, frame_header, data_to_extract):
	"""Count the regions of interest within the raw data file"""
	with open(filename, 'r') as fo:
		for idx, line in enumerate(fo):
			if idx == 0: # don't care about header
				delim_idx, data_idx = get_indices_from_header(line, frame_header, data_to_extract)
			else:
				slice_num = int(extract_from_line(line, delim_idx, data_idx)[0])
				if idx == 1:
					initial_slice_num = slice_num
				else:
					if slice_num != initial_slice_num:
						return idx - 1


def count_frames(filename, frame_header, data_to_extract):
	with open(filename, 'r') as fo:
		for idx, line in enumerate(fo):
			if idx == 0: 
				frame_idx, data_idx = get_indices_from_header(line, frame_header, data_to_extract)
			else:
				frame_num = int(extract_from_line(line, frame_idx, data_idx)[0])
				if idx == 1:
					prev_frame_num = frame_num
					frame_counter = 1
				else:
					if frame_num != prev_frame_num:
						frame_counter += 1
						prev_frame_num = frame_num
	return frame_counter


def file_parse(filename, frame_header, data_to_extract):
	n_roi = count_rows(filename, frame_header, data_to_extract)
	n_frames = count_frames(filename, frame_header, data_to_extract)
	data_matrix = [[None for j in xrange(n_roi)] for i in xrange(n_frames)]
	roi_ctr = 0
	frame_ctr = 0
	with open(filename, 'r') as fo:
		for idx, line in enumerate(fo):
			if idx == 0:
				frame_idx, data_idx = get_indices_from_header(line, frame_header, data_to_extract)
			else:
				current_frame, data = extract_from_line(line, frame_idx, data_idx)
				current_frame = int(current_frame)
				if idx == 1:
					prev_frame = int(extract_from_line(line, frame_idx, data_idx)[0])
					data_matrix[frame_ctr][roi_ctr] = float(data)
				else:
					if roi_ctr == n_roi:
						roi_ctr = 0
					if current_frame != prev_frame:
						frame_ctr+=1
					data_matrix[frame_ctr][roi_ctr] = float(data)
					prev_frame = current_frame
				roi_ctr += 1
	return transpose(data_matrix)


def transpose(list_of_lists):
	"""Given list of lists like [[a,b,c],[d,e,f]] return list of lists like [[a,d],[b,e],[c,f]]"""
	return map(list, zip(*list_of_lists))


def select_cells_with_activity(data, activity_threshhold = 15000):
	cleaned_data = []
	for row in data:
		if max(row) - min(row) >= activity_threshhold:
			cleaned_data.append(row)
	return cleaned_data


def write_file(data, output_filename, row_label_prefix = 'roi', col_label_prefix='t'):
	with open(output_filename, 'w') as fo:
		ncol = len(data[0])
		fo.write('\t') #first position is blank
		for i in xrange(ncol):
			fo.write(str(col_label_prefix) + str(i) + '\t')
		fo.write('\n')
		for idx, line in enumerate(data):
			fo.write(str(row_label_prefix) + str(idx) + '\t')
			for item in line:
				fo.write(str(item) + '\t')
			fo.write('\n')
	return


def main(input_filename, output_filename, frame_header, data_to_extract, activity_threshhold, row_label, column_label):
	start = time.time()
	n_roi, n_frames = count_rows(input_filename, frame_header, data_to_extract), count_frames(input_filename, frame_header, data_to_extract)
	raw_data = file_parse(input_filename, frame_header, data_to_extract)
	write_file(raw_data, output_filename+'_raw.txt', row_label, column_label)
	threshholded_data = select_cells_with_activity(raw_data, activity_threshhold)
	write_file(threshholded_data, output_filename+'_threshholded.txt', row_label, column_label)
	print "Data with {0} regions of interest and {1} time points parsed in {2} seconds.".format(n_roi, n_frames, time.time() - start)


if __name__ == "__main__":
	main(INPUTFILE, OUTPUTFILE, FRAME_HEADER, DATA_TO_EXTRACT, ACTIVITY_THRESHHOLD, ROW_LABEL, COLUMN_LABEL)