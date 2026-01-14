"""S3 router"""

from fastapi import APIRouter, HTTPException, UploadFile, File
import boto3
import uuid
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from os import environ

router = APIRouter()
load_dotenv()


def get_s3_client(app_name):

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=environ.get(f"{app_name.upper()}_AWS_S3_KEY"),
        aws_secret_access_key=environ.get(f"{app_name.upper()}_AWS_S3_SECRET"),
        region_name=environ.get(f"{app_name.upper()}_AWS_S3_REGION"),
    )
    return s3_client


@router.post("/s3/upload/public/{type}")
async def upload_file_s3_public(app_name: str, type: str, file: UploadFile = File(...)):
    # Public uploads do not require user authentication, so no request parameter needed.
    # bucket_name = get_app_key("AWS_S3_BUCKET_PUBLIC")

    bucket_name = environ.get(f"{app_name.upper()}_AWS_BUCKET_NAME")
    s3_client = get_s3_client(app_name)

    file_id = str(uuid.uuid4())
    file_path = f"public/{type}/{file_id}-{file.filename}"
    print(file_path)

    try:
        # Upload file to S3 with the correct content type
        s3_client.upload_fileobj(
            file.file,
            bucket_name,
            file_path,
            ExtraArgs={"ContentType": file.content_type},
        )

        # Return the S3 path of the uploaded file
        s3_url = f"https://{app_name}/{bucket_name}.s3.amazonaws.com/{file_path}"
        return JSONResponse(
            status_code=200,
            content={
                "message": "File uploaded successfully",
                "file_id": file_id,
                "s3_url": s3_url,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/s3/delete/public")
async def delete_file_s3_public(file_path: str, app_name: str):
    """
    Delete a file from the public S3 bucket.

    :param file_path: The path of the file in the S3 bucket.
    :return: Success message or error details.
    """
    bucket_name = environ.get(f"{app_name.upper()}_AWS_BUCKET_NAME")

    # AWS S3 setup
    s3_client = get_s3_client(app_name)

    try:
        # Delete the file from S3
        s3_client.delete_object(Bucket=bucket_name, Key=file_path)
        return {"message": "File deleted successfully", "file_path": file_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
