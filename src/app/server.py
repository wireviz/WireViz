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
ns = api.namespace('', description='wireviz server')
@ns.route('/wireviz/')
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
            filename=os.path.splitext(os.path.basename(os.path.normpath(args['yml_file'].filename)))[0]
            print(filename)
            file_temp.seek(0)
            yaml_input = file_temp.read().decode()
            file_out=tempfile.NamedTemporaryFile()
            fon="%s%s" % (file_out.name, '.png')
            outputname = "%s%s" % (fon, '.png')
            resultfilename="%s%s" % (filename, '.png')
            mimetype='image/png'
            if request.headers["accept"] == "image/svg+xml":
                fon="%s%s" % (file_out.name, '.svg')
                outputname="%s%s" % (fon, '.svg')
                mimetype='image/svg+xml'
                resultfilename="%s%s" % (filename, '.svg')
            wireviz.parse(yaml_input, file_out=fon)
            return send_file(outputname,
                                     as_attachment=True,
                                     attachment_filename=resultfilename,
                                     mimetype=mimetype)
        except Exception as e:
            print(e)
            return make_response(jsonify({
                'message': 'internal error',
                'exception': str(e)
            }), 500)
