import sys, getopt
from converter import process

def cb(current, total):
	print(str(current) + '/' + str(total))

if __name__ == '__main__':
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hi:o:e:c:', ['help', 'input=', 'output=', 'width=', 'height=', 'extension=', 'cutouts='])
	except getopt.GetoptError:
		print('error with parameters')

	width = 1920
	height = 1200
	input_dir = ''
	output_dir = ''
	extension = 'jpg'
	cutouts = ''


	for opt, arg in opts:
		if opt in ('-h', '--help'):
			print('This tool converts, resizes and cuts images of different sizes and formats to a given size.')
			print('Useful for digital pictureframes')
			print('Usage: ' + sys.argv[0] + ' [options(s)]')
			print('\t-h, --help:       prints this help message and quits')
			print('\t-i, --input=:     sets the input directory')
			print('\t-o, --output=:    sets the output directory (wipes content of directory!)')
			print('\t-e, --extension=: sets the image extension for the output images')
			print('\t-c, --cutouts=:   sets the cutouts file')
			print('\t--width=:         sets the target width of the images')
			print('\t--height=:        sets the target height of the images')
			quit()
		elif opt in ('-i', '--input'):
			input_dir = arg
		elif opt in ('-o', '--output'):
			output_dir = arg
		elif opt == '--width':
			width = int(arg)
		elif opt == '--height':
			height = int(arg)
		elif opt in ('-e' , '--extension'):
			extension = arg
		elif opt in ('-c', '--cutouts'):
			cutouts = arg

	if input_dir and output_dir and width != 0 and height != 0 and extension:
		process(input_dir, output_dir, width, height, extension, cutouts, cb)
	else:
		print('missing parameter. Use -h for help')
