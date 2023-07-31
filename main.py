import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from collections import defaultdict
import folium

def get_geotagging(exif):
    if not exif:
        raise ValueError("No EXIF metadata found")

    geotagging = {}
    for (idx, tag) in TAGS.items():
        if tag == 'GPSInfo':
            if idx not in exif:
                raise ValueError("No EXIF geotagging found")

            for (t, v) in GPSTAGS.items():
                if t in exif[idx]:
                    geotagging[v] = exif[idx][t]

    return geotagging

def get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0

    if ref in ['S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds

    return round(degrees + minutes + seconds, 5)

def get_coordinates(geotags):
    lat = get_decimal_from_dms(geotags['GPSLatitude'], geotags['GPSLatitudeRef'])
    lon = get_decimal_from_dms(geotags['GPSLongitude'], geotags['GPSLongitudeRef'])

    return (lat, lon)

def load_images_from_folder(folder):
    images = {}
    for filename in os.listdir(folder):
        img_path = os.path.join(folder, filename)
        if os.path.isfile(img_path):
            img = Image.open(img_path)
            exif = img._getexif()
            if exif is not None:
                try:
                    geotags = get_geotagging(exif)
                    date = datetime.strptime(exif[36867], '%Y:%m:%d %H:%M:%S').date()  # 36867 is the tag for DateTimeOriginal
                    images[img_path] = {"date": date, "coords": get_coordinates(geotags)}
                except:
                    print(f"Skipping {img_path} due to missing GPS information")

    return images


def plot_on_map(images):
    map_osm = folium.Map(location=list(images.values())[0]['coords'], zoom_start=12)
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
              'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
    
    images_by_date = defaultdict(list)
    for img, data in images.items():
        images_by_date[data['date']].append((data['coords'], img))
    
    for idx, (date, imgs) in enumerate(sorted(images_by_date.items(), key=lambda x: x[0])):
        color = colors[idx % len(colors)]
        points = [img[0] for img in imgs]
        folium.PolyLine(points, color=color, weight=2.5, opacity=1).add_to(map_osm)
        for i, point in enumerate(points):
            folium.Marker(point, icon=folium.Icon(icon=str(i+1), prefix='fa', color=color), popup=f'<i>{imgs[i][1]}</i>').add_to(map_osm)
    
    return map_osm

folder_path = 'your_photo_directory'
images = load_images_from_folder(folder_path)
map_osm = plot_on_map(images)
map_osm.save('map.html')


