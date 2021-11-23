import SiteScraper

from flask import Flask, render_template, jsonify, request
from flask_restful import Api, Resource

app = Flask(__name__, template_folder='templates')
api = Api(app)


# download metadata and/or file
class SingleFile(Resource):
    def post(self):
        posted_data = request.json
        file_id = posted_data['file_id']
        metadata_only = posted_data['metadata_only']
        redownload = posted_data['redownload']
        file_data = SiteScraper.download_single_audio_file(file_id, metadata_only=metadata_only)
        message = file_data['message']
        return render_template('singlefileconfirmation.html', message=message)


# download metadata
class SingleFileMetaData(Resource):
    def post(self):
        posted_data = request.json
        file_id = posted_data['file_id']
        file_data = SiteScraper.download_single_audio_file(file_id, metadata_only=True)
        message = file_data['message']
        return render_template('singlefileconfirmation.html', message=message)


# download range of files and/or their metadata
class FileRange(Resource):
    def post(self):
        posted_data = request.json
        first_file_id = posted_data['first_file_id']
        last_file_id = posted_data['last_file_id']
        metadata_only = posted_data['metadata_only']
        redownload = posted_data['redownload']
        files = SiteScraper.download_audio_file_range(first_file_id, last_file_id, metadata_only=metadata_only, redownload=redownload)
        return render_template('multiplefilesconfirmation.html', files=files)


# download metadata for range of files
class FileMetaDataRange(Resource):
    def post(self):
        posted_data = request.json
        first_file_id = posted_data['first_file_id']
        last_file_id = posted_data['last_file_id']
        files = SiteScraper.download_audio_file_range(first_file_id, last_file_id, metadata_only=True)
        return render_template('multiplefilesconfirmation.html', files=files)


# TODO: Route for starting download of all un-downloaded files
# This should have a specification for ALL files or just those not successfully downloaded
class AllFiles(Resource):
    def post(self):
        posted_data = request.get_data()
        message = "Doesn't work yet lol ¯\\_(ツ)_/¯"
        return render_template('singlefileconfirmation.html', message=message)


class AllMetaData(Resource):
    def post(self):
        posted_data = request.get_data()
        message = "Doesn't work yet lol ¯\\_(ツ)_/¯"
        return render_template('singlefileconfirmation.html', message=message)


@app.route('/')
def home_page():
    return render_template('index.html')


api.add_resource(SingleFile, '/singlefile')
api.add_resource(FileRange, '/filerange')
api.add_resource(AllFiles, '/allfiles')
api.add_resource(SingleFileMetaData, '/singlefilemetadata')
api.add_resource(FileMetaDataRange, '/filemetadatarange')
api.add_resource(AllMetaData, '/allmetadata')

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
