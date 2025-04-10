import requests
import pytest

BASE_URL = "http://lx026:8080/api/v1"

HEADER = {'Authorization': f'Bearer {"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0ODgxMDgyLCJpYXQiOjE3NDQyNzYyODIsImp0aSI6IjYyMTVhYTEwMjFhODQ0YTliMTY2NjA0NDEyZDU0OWYwIiwidXNlcl9pZCI6MTd9.PRRxte3N1Enos2HeCxJz3GBs1_NzQKrJQ1MUzEfjMbY"}'}

JSON_DATA = {
    "families": [
        {
            "identifier": "F8303",
            "persons": [
                {
                    "identifier": "25-2716",
                    "sex": "female",
                    "firstName": "BUBULLE",
                    "lastName": "NEMO",
                    "birthday": "1990-12-25",
                    "note": "Test Sample"
                }
            ]
        }
    ],
    "files": [
        {
            "filename": "IOP_F8303.vcf.gz",
            "samples": [
                {
                    "name": "25-2716-A-04-00",
                    "person": "25-2716",
                    "bamPath": "N:/datagen/cytogen/EXOME/RESULTS/EXOME-99_HKGTCBGYW/IOP_F8303/bam/25-2716-A-04-00.mark_dup.bam"
                }
            ],
            "checksum": "393e3d89626987b9bc568d244b94b633",
            "assembly": "GRCh37"
        }
    ],
    "interpretations": [
        {
            "indexCase": "25-2716",
            "project": "iop",
            "title": "F8303 (25-2716) - test uploader",
            "assignee": "bnouyou",
            "priority": "normal",
            "datas": [
                {
                    "title": "SNV",
                    "type": "SNV",
                    "samples": [
                        {
                            "name": "25-2716-A-04-00",
                            "isAffected": True,
                            "checksum": "393e3d89626987b9bc568d244b94b633"
                        }
                    ]
                }
            ]
        }
    ]
}

@pytest.mark.parametrize("method, endpoint, payload, headers", [
    ("GET", "healthcheck", None, None),
    ("POST", "auth/login/", {"identifier": "pipeline", "password": "diagho123"}, None),
    ("GET", "users/me/", None, HEADER),
    ("GET", "bio-files/?checksum=c82a9d0082bede2952c69dd7f7ee7308", None, HEADER),
    ("GET", "projects/iop", None, HEADER),
    ("POST", "configurations/", JSON_DATA, HEADER)
])


def test_api_endpoints(method, endpoint, payload, headers):
    url = f"{BASE_URL}/{endpoint}"
    if headers:
        print(endpoint)
        response = requests.request(method, url, json=payload, headers=headers)
    else:
        print("No headers")
        response = requests.request(method, url, json=payload)
        
    assert response.status_code < 400, (
        f"{method} '{endpoint}' failed with code: {response.status_code}.\n"
        # f"Response: {response.json()}"
    )
