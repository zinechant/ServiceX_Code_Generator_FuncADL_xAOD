# Copyright (c) 2019, IRIS-HEP
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from flask import request, Response
from flask_restful import Resource
from ast_language import text_ast_to_python_ast
from func_adl_xAOD.backend import use_executor_xaod_hash_cache
from tempfile import TemporaryDirectory
import zipfile
import os
import base64


def zipdir(path: str, zip_handle: zipfile.ZipFile):
    # zip_handle is zipfile handle
    for root, _, files in os.walk(path):
        for file in files:
            zip_handle.write(os.path.join(root, file), file)


class GenerateCode(Resource):
    def post(self):
        code = request.data.decode('utf8')

        # Turn the ast-language into a python AST we can easily process
        a = text_ast_to_python_ast(code).body[0].value

        # Generate the C++ code
        with TemporaryDirectory() as tempdir:
            r = use_executor_xaod_hash_cache(a, tempdir)

            # Zip up everything in the directory - we are going to ship it as back as part
            # of the message.
            z_filename = os.path.join(str(tempdir), f'{r.hash}.zip')
            zip_h = zipfile.ZipFile(z_filename, 'w', zipfile.ZIP_DEFLATED)
            zipdir(os.path.join(str(tempdir), r.hash), zip_h)
            zip_h.close()

            with open(z_filename, 'rb') as b_in:
                zip_data = b_in.read()
            # zip_data_b64 = bytes.decode(base64.b64encode(zip_data))

        # Send the response back to you-know-what.
        response = Response(
            response=zip_data,
            status=200, mimetype='application/octet-stream')
        return response
