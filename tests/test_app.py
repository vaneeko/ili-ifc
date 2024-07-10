# -*- coding: utf-8 -*-
import pytest
import json
import os
import logging
from app import app

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_index(client):
    response = client.get('/')
    logger.info('GET / request successful')
    assert response.status_code == 200
    assert b'XTF to IFC Converter' in response.data
    logger.info('Index page loaded successfully')

def test_convert_no_files(client):
    response = client.post('/convert', data={})
    logger.info('POST /convert request with no files')
    assert response.status_code == 400
    
    response_data = json.loads(response.data)
    assert 'Keine Dateien ausgewählt' in response_data['error']
    logger.info('No files error message validated')

def test_convert_success(client):
    data = {
        'default_sohlenkote': '100.0',
        'default_durchmesser': '0.8',
        'default_hoehe': '0.8',
        'default_wanddicke': '0.04',
        'default_bodendicke': '0.02',
        'default_rohrdicke': '0.02',
        'einfaerben': 'false'
    }
    with open('tests/testfile_complete.xtf', 'rb') as test_file:
        response = client.post('/convert', data={
            'xtfFiles': test_file,
            **data
        })

    logger.info('POST /convert request with valid file')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'Erfolgreich konvertierte Dateien' in response_data['message']
    assert len(response_data['downloadLinks']) > 0
    logger.info('Conversion success message validated')

    for link in response_data['downloadLinks']:
        filename = link['filename']
        file_path = os.path.join('/tmp/ifc_converter_temp', filename)
        assert os.path.exists(file_path)
        logger.info(f'File {file_path} exists')
