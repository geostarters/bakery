![alt text](https://github.com/geostarters/bakery/raw/master/data/logo.png "Logo")
Bakes lighting, computed from a normal map pyramid, into a raster layer.

## Usage
`python monothreaded.py zoomStart zoomEnd` to run the single threaded script

`python multithreaded.py zoomStart zoomEnd` to run the multi threaded script
For example `python multithreaded.py 0 12` would create a new pyramid with levels [0, 12] in the output directory

## Requirements
[Python](https://www.python.org/) 2.7

The [Python Imaging Library (PIL)](http://www.pythonware.com/products/pil/)

## Configuration
At the start of each script there are some parameters that can be changed to modify the outcome of the script

These parameters are the following ones:
|*Parameter*|*Description*|
|---|---|
|normalMapBaseURL| URL endpoint where the normal map pyramid can be found |
|destinationLayer8To12BaseURL| URL endpoint of the raster layer used between the 8th and 12th zoom levels |
|destinationLayerBaseURL| URL endpoint of the raster layer used on each of the zooms levels not in [8, 12] |
|tileSize| The tile size in pixels |
|lightDir| The normalized light direction in windows coordinates. The default light comes from NW as in classical maps |
|xMin| Minimum longitude of the tile layer|
|yMin| Minimum latitude of the tile layer|
|xMax| Maximum longitude of the tile layer|
|yMax| Maximum latitude of the tile layer|

## Results
You can find a live demo [here](http://betaserver.icgc.cat/visor/ortoaugmentada.html#14/42.3340/1.6530)