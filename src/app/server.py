from flask import send_file
from flask import request, jsonify, send_file, make_response
from app import app, api
import os
from flask_restplus import Resource, reqparse
import werkzeug
import tempfile
from wireviz import wireviz

file_upload = reqparse.RequestParser()
file_upload.add_argument('yml_file',
                         type=werkzeug.datastructures.FileStorage,
                         location='files',
                         required=True,
                         help='YAML file')
#curl -X POST "http://localhost:5000/wirewiz/" -H  "Content-Type: multipart/form-data" -F "yml_file=@/home/elbosso/Desktop/demo01.yml;type=application/x-yaml"
ns = api.namespace('', description='wirewiz server')
@ns.route('/wirewiz/')
class Render(Resource):
    @api.expect(file_upload)
    @ns.produces(['image/png', 'image/svg+xml'])
    def post(self):
        """
        """
        args = file_upload.parse_args()
        try:
            file_temp=tempfile.TemporaryFile()
            args['yml_file'].save(file_temp)
            file_temp.seek(0)
            yaml_input = file_temp.read().decode()
            file_out=tempfile.NamedTemporaryFile()
            fon="%s%s" % (file_out.name, '.png')
            outputname = "%s%s" % (fon, '.png')
            mimetype='image/png'
            if request.headers["accept"] == "image/svg+xml":
                fon="%s%s" % (file_out.name, '.svg')
                outputname="%s%s" % (fon, '.svg')
                mimetype='image/svg+xml'
            wireviz.parse(yaml_input, file_out=fon)
            return send_file(outputname,
                                     as_attachment=True,
                                     attachment_filename=outputname,
                                     mimetype=mimetype)
        except Exception as e:
            print(e)
            return make_response(jsonify({
                'message': 'internal error',
                'exception': str(e)
            }), 500)