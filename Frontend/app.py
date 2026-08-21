import os
import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("AWS_S3_BUCKET")

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION
)

test_file = "test_resume.txt"
s3_key = "test/test_resume.txt"


# Create a dummy file
with open(test_file, "w") as file:
    file.write("This is a test file for Resume-Dangal S3.")


# Upload
print("Uploading...")
s3.upload_file(
    test_file,
    BUCKET_NAME,
    s3_key
)

print("✅ Upload successful!")


# List objects
print("\nFiles in test/:")

response = s3.list_objects_v2(
    Bucket=BUCKET_NAME,
    Prefix="test/"
)

for obj in response.get("Contents", []):
    print(" -", obj["Key"])


# Delete the test object
print("\nDeleting test object...")

s3.delete_object(
    Bucket=BUCKET_NAME,
    Key=s3_key
)

print("✅ Test object deleted!")