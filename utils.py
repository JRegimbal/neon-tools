# Copyright (C) 2020 Juliette Regimbal
# SPDX-License-Identifier: GPL-3.0-or-later

from urllib import request

import base64
from datetime import datetime, timezone
import json
import uuid


PRESENTATION_CONTEXT = "http://iiif.io/api/presentation/2/context.json"
MANIFEST_TYPE = "sc:Manifest"
CANVAS_TYPE = "sc:Canvas"


def retrieve(url, type_val=None):
    print(url)
    with request.urlopen(url) as response:
        assert response.getcode() == 200
        raw_data = response.read()
    parsed = json.loads(raw_data)
    assert parsed["@context"] == PRESENTATION_CONTEXT
    if type_val:
        assert parsed["@type"] == type_val
    return parsed


def get_canvas_param_list(sequence):
    return ({
                "@id": canvas_data["@id"],
                "label": canvas_data["label"],
                "width": canvas_data["width"],
                "height": canvas_data["height"]
            }
            for canvas_data in sequence)


def generate_blank_mei(canvas, manifestID):
    template = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<?xml-model '
            'href="https://music-encoding.org/schema/4.0.0/mei-all.rng" '
            'type="application/xml" '
            'schematypens="http://relaxng.org/ns/structure/1.0"?>'
            '<?xml-model '
            'href="https://music-encoding.org/schema/4.0.0/mei-all.rng" '
            'type="application/xml" '
            'schematypens="http://purl.oclc.org/dsdl/schematron"?>'
            '<mei'
            ' xmlns="http://www.music-encoding.org/ns/mei" meiversion="4.0.0">'
            '<meiHead>'
            '<fileDesc>'
            '<titleStmt><title>{}</title></titleStmt>'
            '<pubStmt/>'
            '<sourceDesc>'
            '<source target="{}" recordtype="m" targettype="IIIFManifest"/>'
            '<source target="{}" recordtype="m" targettype="IIIFCanvas"/>'
            '</sourceDesc>'
            '</fileDesc>'
            '</meiHead>'
            '<music>'
            '<facsimile><surface ulx="0" uly="0" lrx="{}" lry="{}">'
            '<zone xml:id="delete-me" ulx="100" uly="100"'
            ' lrx="1000" lry="1000"/>'
            '</surface></facsimile>'
            '<body><mdiv><score><scoreDef><staffGrp>'
            '<staffDef n="1" notationtype="neume" lines="4"'
            ' clef.shape="C" clef.line="3"/>'
            '</staffGrp></scoreDef>'
            '<section><staff n="1"><layer n="1">'
            '<sb facs="#delete-me"/>'
            '</layer></staff></section></score></mdiv></body>'
            '</music></mei>'
    )
    return template.format(
            canvas["label"],
            manifestID,
            canvas["@id"],
            canvas["width"],
            canvas["height"]
    )


def create_data_uri(mei):
    b64 = base64.b64encode(mei.encode())
    return "data:application/mei+xml;base64,{}".format(b64.decode())


def generate_annotations(manifest):
    canvases = get_canvas_param_list(manifest["sequences"][0]["canvases"])
    return [
            {
                "id": "urn:uuid:{}".format(str(uuid.uuid4())),
                "type": "Annotation",
                "body": create_data_uri(
                    generate_blank_mei(canvas, manifest["@id"])
                ),
                "target": canvas["@id"]
            }
            for canvas in canvases
    ]


def generate_manifest(manifest):
    annotations = generate_annotations(manifest)
    return {
            "@context":
            "https://ddmal.music.mcgill.ca/Neon/contexts/1/manifest.jsonld",
            "@id": "urn:uuid:{}".format(str(uuid.uuid4())),
            "title": manifest["label"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "image": manifest["@id"],
            "mei_annotations": annotations
    }
