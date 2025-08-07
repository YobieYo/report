from sequences.merge_seq import MergeSequence
from data_loaders.excel_loader.excel_loader import ExcelLoader
from report_builders.merge_report_drawer import MergeReportBuilder
from flask import jsonify
import os
import uuid

class MergeController:

    @staticmethod
    def merge(web_file, bitrix_file):
        upl = os.environ.get('UPLOAD_FOLDER')
        file_id = uuid.uuid4()


        web_path = save_uploaded_file(web_file, upl, file_id)
        bitrix_path = save_uploaded_file(bitrix_file, upl, file_id)
        
        data_loader = ExcelLoader(bitrix_path, web_path)
        reporrt_builder = MergeReportBuilder()
        manager = MergeSequence(
            data_loader,
            reporrt_builder
        )

        manager.run()

        return jsonify({'dfd': 'dfd'}), 200



@staticmethod
def save_uploaded_file(file, upload_folder, file_id):
    """
    Saves an uploaded file with a unique UUID prefix in the specified folder.
    
    Args:
        file: The file object to be saved
        upload_folder: The path to the upload directory
    
    Returns:
        tuple: (generated_filename, full_file_path)
    """
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    return file_path