import SiteScraper
from flask import Flask, render_template, jsonify, request
from flask_restful import Api, Resource

app = Flask(__name__, template_folder='templates')
api = Api(app)

# TODO: Route for downloading single file
class SingleFile(Resource):
    def post(self):
        posted_data = request.get_data()
        response_json = {
            'status_code': 200
        }
        return jsonify(response_json)

# TODO: Route for downloading range of files
class FileRange(Resource):
    def post(self):
        posted_data = request.get_data()
        response_json = {
            'status_code': 201
        }
        return jsonify(response_json)

# TODO: Route for starting download of all un-downloaded files
class AllFiles(Resource):
    def post(self):
        posted_data = request.get_data()
        response_json = {
            'status_code': 202
        }
        return jsonify(response_json)


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
