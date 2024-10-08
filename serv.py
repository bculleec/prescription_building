from flask import Flask, request, send_file, render_template
from flask_cors import CORS, cross_origin
import rasterio
import prescription_build
import json
import io
import os

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/")
def status_on():
    return render_template('./index.html')

@app.route('/export_prescription/<num_subdivisions>', methods = ['POST', 'GET'])
def export_prescription(num_subdivisions):
    files = request.files
    file = files.get('file')
    print(file)
    
    print(files)

    file.save('./export.tiff')
    
    # f = open('./export.tiff', 'w')
    # f.write(file.content)
    # f.close()
    raster = rasterio.open('./export.tiff')
    print(raster.meta)

    file2 = files.get('file2')
    # print(json.loads(file2.read()))

    zone_info = json.loads(file2.read())

    print(zone_info)

    # Get the shapefile
    shape_response_path = prescription_build.export_shapefile('./export.tiff', zone_info=zone_info)

    return_data = io.BytesIO()
    with open(shape_response_path, 'rb') as fo:
        return_data.write(fo.read())
    # (after writing, cursor will be at last byte, so move it to start)
    return_data.seek(0)

    raster.close()

    if os.path.exists(shape_response_path):
        os.remove(shape_response_path)
    
    if os.path.exists('demo.tiff'):
        os.remove('demo.tiff')
    
    if os.path.exists('export.tiff'):
        os.remove('export.tiff')
    
    if os.path.exists('reprojected.tiff'):
        os.remove('reprojected.tiff')

    return send_file(return_data, mimetype='application/zip')


@app.route('/post_raster_data/<num_subdivisions>', methods = ['POST', 'GET'])
def get_post_raster_data(num_subdivisions):
    
    files = request.files
    file = files.get('file')
    print(file)

    file.save('./demo.tiff')
    
    # f = open('./demo.tiff', 'w')
    # f.write(file.content)
    # f.close()
    raster = rasterio.open('./demo.tiff')


    print(raster.meta)
    print('Number of subdivisions: ' + num_subdivisions)

    z = prescription_build.read_zones('./demo.tiff', num_subdivisions)

    print(z.to_dataframe())

    return (z.to_dataframe().to_json())

if __name__ == "__main__":
    app.run(debug=True, port=8080)