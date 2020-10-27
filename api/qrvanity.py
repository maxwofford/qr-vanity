#!/usr/bin/env python3

# Copyright (c) 2018 Marco Zollinger
# Licensed under MIT, the license file shall be included in all copies

import requests
from PIL import Image
from io import BytesIO
import base64
import pyqrcode
import zbarlight
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        result = self.qr_codify()
        self.wfile.write(bytes(f"<h1>{result[0]}</h1>", "utf-8"))
        return

    def qr_codify(self):
        response = requests.get('https://cloud-ncs8fqr6s.vercel.app/0pixil-frame-0.png')
        input_image = Image.open(BytesIO(response.content)).convert("RGBA")
        payload = "https://hack.af"
        try:
            input_image.load()
        except (OSError, IOError) as e:
            print("Invalid image: {}".format(e))

        success = False
        results = []
        # try versions 1 to 40, smaller first
        for version in range(1, 41):
            try:
                qr_object = pyqrcode.create(payload, error='H', version=version)
            except ValueError:
                print("data payload too small (version {})".format(version))
                continue
            qr_file = BytesIO()
            # TODO: fix quiet zone overshoot problem
            qr_object.png(qr_file, quiet_zone=1)
            # TODO: error handling in case qr-code generation fails
            qr_image = Image.open(qr_file)
            qr_image.load()

            # try input image on every position on qr-code
            print("trying to fit in version {}".format(version))
            qr_width, qr_height = qr_image.size
            input_width, input_height = input_image.size
            for x in range(qr_width - input_width):
                for y in range(qr_height - input_height):
                    #print("DEBUG: qrsize:{}, x:{}, y:{}".format(qr_width, x, y))
                    output_image = qr_image.copy()
                    output_image.paste(input_image, (x, y), input_image)

                    # try to read the result as a qr-code and check
                    try:
                        qr_readback = zbarlight.scan_codes('qrcode', output_image)
                    except SyntaxError:
                        continue
                    for qrcode in (qr_readback or []):
                        qrcode = qrcode.decode('ascii', errors='replace')
                        if qrcode == payload:
                            success = True
                            output_image = output_image.resize((4*qr_width, 4*qr_height), Image.LANCZOS)
                            buf = BytesIO()
                            output_image.save(buf, format="JPEG")
                            img_str = base64.b64encode(buf.getvalue())
                            # img_base64 = bytes("data:image/jpeg;base64,",encoding="utf-8") + img_str
                            img_base64 = "data:image/jpeg;base64," + img_str
                            results.append(img_base64)
            if success:
                print("fit found in version {}".format(version))
                return results
                # sys.exit(0)
        print("sorry, no luck!")
        return results
