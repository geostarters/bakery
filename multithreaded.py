from __future__ import division
from PIL import Image, ImageDraw
import urllib2, io, math, cStringIO, os, threading

normalMapBaseURL = u'http://betaserver.icgc.cat/tileserver3/tileserver.php?/norm2x2/{}/{}/{}.png'
destinationLayer8To12BaseURL = u'http://tilemaps.icgc.cat/mapfactory/wmts/orto_8_12/CAT3857/{}/{}/{}.png'
destinationLayerBaseURL = u'http://mapcache.icc.cat/map/bases_noutm/wmts/orto/GRID3857/{}/{}/{}.jpeg'
tileSize = 256
threadNumber = 32

lightDir = [-0.7071067811865476, 0.7071067811865476, 1.0]
xMin = 0.108700003
yMin = 40.470000001
xMax = 3.3618164062499996
yMax = 42.88401467044253

def toNormal(val):
	normal = [0, 0, 0]
	root = math.sqrt(val[0]*val[0] + val[1]*val[1] + val[2]*val[2]);
	if(0 != root):
		normal = [val[0]/root, val[1]/root, val[2]/root]
		normal = [normal[i]*2.0 - 1.0 for i in range(len(normal))]
	return normal

def lon2tile(lon,zoom):
	return int(math.floor((lon+180)/360*math.pow(2,zoom)))

def lat2tile(lat,zoom):  
	return int(math.floor((1-math.log(math.tan(lat*math.pi/180) + 1/math.cos(lat*math.pi/180))/math.pi)/2 *math.pow(2,zoom)))

def mixColorLess15(color, colorIn, normalPixel):
	color = [int(color[k]) for k in range(3)]
	color.append(colorIn[3] if (4 == len(colorIn)) else normalPixel[3])
	return color

def mixColor15(color, colorIn, normalPixel):
	color = [int(round(color[k]*0.8 + colorIn[k]*0.2)) for k in range(3)]
	color.append(normalPixel[3])
	return color

def mixColor16(color, colorIn, normalPixel):
	color = [int(round(color[k]*0.5 + colorIn[k]*0.5)) for k in range(3)]
	color.append(normalPixel[3])
	return color

def mixColor17(color, colorIn, normalPixel):
	color = [int(round(color[k]*0.2 + colorIn[k]*0.8)) for k in range(3)]
	color.append(normalPixel[3])
	return color

def mixColorBigger17(color, colorIn, normalPixel):
	color = [int(colorIn[k]) for k in range(3)]
	color.append(normalPixel[3])
	return color

def openFiles(ortoBaseURL, zoomLevel, x, y):
	normalURL = normalMapBaseURL.format(zoomLevel, x, y)
	ortoURL = ortoBaseURL.format(zoomLevel, x, y)
	normalPath = cStringIO.StringIO(urllib2.urlopen(normalURL).read())
	ortoPath = cStringIO.StringIO(urllib2.urlopen(ortoURL).read())
	normalImg = Image.open(normalPath)
	normal = normalImg.getdata()
	ortoImg = Image.open(ortoPath).convert("RGBA")
	orto = ortoImg.getdata()
	return (normal, orto)

def getPixelColor(normal, orto, lightDir, i, j):
	pixel = (j*tileSize + i)
	normalPixel = normal[pixel]
	normalValue = toNormal(normalPixel)
	colorIn = orto[pixel]
	shadowValue = sum( [lightDir[k]*normalValue[k] for k in range(len(normalValue))] )
	shadowValue = shadowValue if (shadowValue > 0.0) else 0.0
	color = [shadowValue*2.0, shadowValue*2.0, shadowValue*2.0]
	color = [color[0]*colorIn[0], color[1]*colorIn[1], color[2]*colorIn[2]]
	
	return (color, colorIn, normalPixel)

def saveFile(output, zoomLevel, x, y):
	newpath = './output/{}'.format(zoomLevel)
	try:
		if not os.path.exists(newpath):
			os.makedirs(newpath)
	except OSError, err:
		pass

	newpath = './output/{}/{}'.format(zoomLevel, x)
	try:
		if not os.path.exists(newpath):
			os.makedirs(newpath)
	except OSError, err:
		pass

	output.save('./output/{}/{}/{}.png'.format(zoomLevel, x, y))

def generateImage(zoomLevel, ortoBaseURL, x, y, lightDir, mixFunction):
	try:
		(normal, orto) = openFiles(ortoBaseURL, zoomLevel, x, y)
		output = Image.new('RGBA', normal.size)
		width, height = normal.size
		for i in range(0, width):
			for j in range(0, height):
				(color, colorIn, normalPixel) = getPixelColor(normal, orto, lightDir, i, j)
				color = mixFunction(color, colorIn, normalPixel)
				output.putpixel((i,j), tuple(color))

		saveFile(output, zoomLevel, x, y)
		output.close()
	except urllib2.HTTPError, err:
		print err, "(", zoomLevel, ", ", x, ", ", y, ")"
	except IOError, err:
		print err, "(", zoomLevel, ", ", x, ", ", y, ")"

def work():
	global zoomLevel, tileX, tileY
	(zoom, x, y) = getTileIndex()
	while(-1 != zoom):
		outputPath = './output/{}/{}/{}.png'.format(zoom, x, y)
		if not os.path.exists(outputPath):
			if(0 == (numDone % 100)):
				print "Working on (", zoom, ", ", x, ", ", y, ") (", numDone, " of ", totalTiles, "{0:.9f}".format((numDone/totalTiles)*100.0), "%)"

			ortoBaseURL = destinationLayer8To12BaseURL
			if(zoom > 12 or zoom < 8):
				ortoBaseURL = destinationLayerBaseURL

			if(zoom <15):
				generateImage(zoom, ortoBaseURL, x, y, lightDir, mixColorLess15)
			elif(15 == zoom):
				generateImage(zoom, ortoBaseURL, x, y, lightDir, mixColor15)
			elif(16 == zoom):
				generateImage(zoom, ortoBaseURL, x, y, lightDir, mixColor16)
			elif(17 == zoom):
				generateImage(zoom, ortoBaseURL, x, y, lightDir, mixColor17)
			else:
				generateImage(zoom, ortoBaseURL, x, y, lightDir, mixColorBigger17)
		(zoom, x, y) = getTileIndex()

def dispatcher(numThreads):
	threads = []
	for threadIndex in range(numThreads):
		t = threading.Thread(target=work)
		threads.append(t)
		t.start()
	
	for thread in threads:
		thread.join()

def getTileIndex():
	global numDone, tileZoom, tileX, tileY, levelTiles
	numDone = numDone+1
	if(len(levelTiles) > tileZoom):
		(top, left, bottom, right) = levelTiles[tileZoom]
		if(tileX < right):
			tileX = tileX+1
		else:
			tileX = left
			tileY = tileY+1
			if(tileY > bottom+1):
				tileZoom = tileZoom+1
				if(len(levelTiles) > tileZoom):
					print "----", tileZoom, "----"
					print "Top: ", top, " bottom: ", bottom, " left: ", left, " right ", right
					total = (bottom-top +1)*(right-left+1)
					print total, " tiles to generate"
					(top, left, bottom, right) = levelTiles[tileZoom]
					tileX = left
					tileY = top
				else:
					return (-1, -1, -1)

		return (tileZoom, tileX, tileY)
	else:
		return (-1, -1, -1)

if (1 != len(sys.argv)):
	startZoom = int(sys.argv[1])
	endZoom = int(sys.argv[2])

	tileZoom = startZoom
	tileX = lon2tile(xMin, tileZoom)
	tileY = lat2tile(yMax, tileZoom)

	numDone = 0
	totalTiles = 0
	levelTiles = []

	for zoomLevel in range(startZoom, endZoom):
		top_tile    = lat2tile(yMax, zoomLevel)
		left_tile   = lon2tile(xMin, zoomLevel)
		bottom_tile = lat2tile(yMin, zoomLevel)
		right_tile  = lon2tile(xMax, zoomLevel)
		numTiles = (bottom_tile-top_tile +1)*(right_tile-left_tile+1)
		totalTiles = totalTiles + numTiles
		levelTiles.append((top_tile, left_tile, bottom_tile, right_tile))

	dispatcher(threadNumber)
else:
	print "Not enough parameters (startZoom endZoom)"