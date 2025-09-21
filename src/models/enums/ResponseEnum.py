from enum import Enum
class ResponseSiginal(Enum):
    FILE_VALIDATED_SUCCESS="File validation successful."
    FILE_VALIDATED_FAILED="File validation failed."
    FILE_TYPE_NOT_SUPPORTED="File type is not supported."
    FILE_SIZE_EXCEEDED="File size exceeds the maximum limit."
    FILE_UPLOADED_SUCCESS="File uploaded successfully."
    FILE_UPLOADED_FAILED="File upload failed."
    PROCESSING_FAILED="File processing failed."
    PROCESSING_SUCCESS="File processed successfully."
    NO_FILES_TO_PROCESS="No files available to process."