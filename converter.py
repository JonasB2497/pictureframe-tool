#!/bin/python

import os
import threading
from PIL import Image, ExifTags
from shutil import copy2, rmtree

IMAGEEXTENSIONS=['.jpg', '.png']

def process(input_dir, output_dir, width, height, extension, cutouts, callback=None):
	if os.path.isdir(output_dir):
		rmtree(output_dir)

	os.makedirs(output_dir)

	cutout_dict = process_cutouts_file(cutouts, input_dir)
	file_params = {
		'width': width,
		'height': height,
		'input_dir': input_dir,
		'output_dir': output_dir,
		'extension': extension,
		'cutout_dict': cutout_dict
	}
	dir_params = {
		'input_dir': input_dir,
		'output_dir': output_dir
	}

	recursive_dir(input_dir, function_file, file_params, process_dir, dir_params, callback)

def process_async(input_dir, output_dir, width, height, extension, cutouts, callback=None):
	thread = threading.Thread(
		target=process,
		args=(input_dir, output_dir, width, height, extension, cutouts),
		kwargs={"callback": callback},
	)
	thread.start()
	return thread

def recursive_dir(dir, func_file, file_params, funcDir, dir_params, callback=None, params={}):
	if not params:
		# first run
		params['current'] = 0
		params['total'] = 0

	params['total'] += len([name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))])

	for filename in os.listdir(dir):
		path = os.path.join(dir, filename)
		if os.path.isdir(path):
			funcDir(path, **dir_params)
			recursive_dir(path, func_file, file_params, funcDir, dir_params, callback, params)
		else:
			func_file(path, **file_params)
			params['current'] += 1
			if callback:
				callback(params['current'], params['total'])

def function_file(path, width, height, input_dir, output_dir, extension, cutout_dict):
	output_file = path.replace(input_dir, output_dir)
	output_file = output_file[0:output_file.rfind('.')] + '.' + extension
	cutout = 0.5
	if path in cutout_dict:
		cutout = cutout_dict[path]
	process_file(width, height, path, output_file, cutout)

def process_cutouts_file(path, input_dir):
	cutout_dict = {}
	# read in the cutouts file
	if os.path.isfile(path):
		f = open(path, "r")
		lines = f.readlines()
		for l in lines:
			parts = l.split("\t")
			if len(parts) == 2:
				cutout_dict[input_dir + '/' + parts[0]] = float(parts[1])
	
	return cutout_dict

def process_file(width, height, input, output, cutout=0.5):
	extension = os.path.splitext(input)[1].lower()
	if extension in IMAGEEXTENSIONS:
		image = Image.open(input)
		try:
			for orientation in ExifTags.TAGS.keys():
				if ExifTags.TAGS[orientation]=='Orientation':
					break

			exif = image.getexif()

			if exif[orientation] == 3:
				image=image.rotate(180, expand=True)
			elif exif[orientation] == 6:
				image=image.rotate(270, expand=True)
			elif exif[orientation] == 8:
				image=image.rotate(90, expand=True)

		except (AttributeError, KeyError, IndexError):
			# cases: image don't have getexif
			pass

		xsize, ysize = image.size
		if (ysize/xsize) > (height/width):
			# image is higher than needed
			# resize to width then crop
			image = image.resize((width, int(ysize * (width/xsize))))
			cutoff = (image.size[1] - width) * cutout
			image = image.crop((0, cutoff, width, cutoff+height))
		elif (ysize/xsize) < (height/width):
			# image is wider than needed
			# resize to height then crop
			image = image.resize((int(xsize * (height/ysize)), height))
			cutoff = (image.size[0] - width) * cutout
			image = image.crop((cutoff, 0, cutoff + width, height))
		else:
			# image has the correct aspect ratio
			# just resize
			image = image.resize((width, height))
			pass
		image = image.convert('RGB')
		image.save(output, quality=95)
		image.close()


def process_dir(path, input_dir, output_dir):
	path = path.replace(input_dir, output_dir)
	os.makedirs(path)