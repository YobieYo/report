from routes import *
from flask import url_for
from .confest import client, app, mock_result_file

def test_index(client):
    response = client.get('/')

    assert response.status_code == 302
    assert response.location == url_for('merge_files')

def test_merge_page(client):
    response = client.get('/merge-files')

    assert response.status_code == 200

def test_doc_page(client):
    response = client.get('/documentation')
    
    assert response.status_code == 200

def test_format_page(client):
    response = client.get('/format-file')
    
    assert response.status_code == 200

def test_download(client, mock_result_file):

    assert os.path.exists(mock_result_file)

    response = client.get('/download&link=нет_такого_файла.xlsx')
    assert response.status_code == 404