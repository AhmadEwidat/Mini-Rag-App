from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseSiginal
from .ProjectController import ProjectController
import re
import os

class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.file_scaler = 1024 * 1024  # Convert MB to bytes

    def validate_file(self, file: UploadFile):
        if file.content_type not in self.settings.File_Allowed_Types:
            return False, ResponseSiginal.FILE_TYPE_NOT_SUPPORTED.value
        if file.size>self.settings.Max_File_Size * self.file_scaler:
            return False, ResponseSiginal.FILE_SIZE_EXCEEDED.value  
        return True, ResponseSiginal.FILE_VALIDATED_SUCCESS.value
    def genarate_unique_filepath(self, original_filename: str,project_id:str):
        random_key=self.genarate_random_string()
        project_path=ProjectController().get_project_path(project_id=project_id)
        cleaned_file_name=self.get_clean_filename(original_filename)
        new_file_name=os.path.join(project_path,random_key+"_"+cleaned_file_name)
        while os.path.exists(new_file_name):
            random_key=self.genarate_random_string()
            new_file_name=os.path.join(project_path,random_key+"_"+cleaned_file_name)

        return new_file_name,random_key+"_"+cleaned_file_name

    def get_clean_filename(self, orig_file_name: str):
        cleaned_file_name = re.sub(r'[^\w.]', '', orig_file_name.strip())
        cleaned_file_name=cleaned_file_name.replace(" ", "_")
        return cleaned_file_name