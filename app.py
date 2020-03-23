import SiteScraper
import PageData

from flask import Flask, render_template, jsonify, request
from flask_restful import Api, Resource

app = Flask(__name__, template_folder='templates')
api = Api(app)

# TODO: Route for downloading single file
class SingleFile(Resource):
    def post(self):
        posted_data = request.json
        file_id = posted_data['file_id']
        file_data = SiteScraper.download_single_file(file_id)
        message = file_data['message']
        return render_template('singlefileconfirmation.html', message=message)

# TODO: Route for downloading range of files
class FileRange(Resource):
    def post(self):
        posted_data = request.json
        first_file_id = posted_data['first_file_id']
        last_file_id = posted_data['last_file_id']
        files = SiteScraper.download_file_range(first_file_id, last_file_id)
        return render_template('multiplefilesconfirmation.html', files=files)

# TODO: Route for starting download of all un-downloaded files
class AllFiles(Resource):
    def post(self):
        posted_data = request.get_data()
        message = "Doesn't work yet lol ¯\\_(ツ)_/¯"
        return render_template('singlefileconfirmation.html', message=message)


@app.route('/')
def greeting():
    return "Howdy!"


@app.route('/home')
def home_page():
    return render_template('index.html')


api.add_resource(SingleFile, '/singlefile')
api.add_resource(FileRange, '/filerange')
api.add_resource(AllFiles, '/allfiles')

if __name__ == "__main__":
    app.run(debug=True)
