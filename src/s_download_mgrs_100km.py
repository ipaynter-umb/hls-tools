from pathlib import Path
from os import mkdir, rmdir, walk, rename
from os.path import exists
import lxml.html as lh
import requests
import zipfile

output_path = Path(r'F:/UMB/HLS/MGRS_100km')

# If there is no temp directory
if not exists(output_path / 'temp'):
    # Create temp directory
    mkdir(output_path / 'temp')

# Make a requests session
s = requests.session()

# Get the html of the page
r = s.get("https://earth-info.nga.mil/index.php?dir=coordsys&action=mgrs-100km-polyline-dloads")
# Retrieve the html as text
html = r.text
# Get the root object
root = lh.fromstring(html)

# For each element in the root
for element in root.iter():
    # If it's the imageMapTest (where the hrefs are stored)
    if element.attrib.get('name') == 'imageMapTest':
        # For each element in the map test
        for map_element in element.iter():
            # If the element has an href
            if map_element.attrib.get('href'):
                # Get the href
                href = map_element.attrib.get('href')
                # Make a reqeust for the file
                r = s.get('https://earth-info.nga.mil/' + href)
                # Get the file name
                file_name = href.split('=')[-1] + '.zip'
                # File path
                file_path = output_path / 'temp' / file_name
                # Write the content
                with open(file_path, 'wb') as f:
                    f.write(r.content)
                # Extract path
                extract_path = Path(str(file_path).replace('.zip', ''))
                # Unzip the file
                zipfile.ZipFile(file_path, mode='r').extractall(extract_path)
                # Walk the file directory
                for root, dirs, files in walk(extract_path):
                    # For each file
                    for file in files:
                        # Move the file to the outer directory
                        rename(Path(root, file), output_path / file)
# Remove the temp directory
rmdir(output_path / 'temp')
