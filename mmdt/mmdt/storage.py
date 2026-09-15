from botocore.exceptions import ClientError
from storages.backends.s3boto3 import S3Boto3Storage


class MediaS3Storage(S3Boto3Storage):
    """S3 media storage that does not crash when HeadObject is denied.

    django-storages calls ``exists()`` (HeadObject) when
    ``AWS_S3_FILE_OVERWRITE`` is False. Some IAM policies allow PutObject
    but not GetObject/HeadObject, which surfaces as 403 Forbidden on save.
    """

    def exists(self, name):
        try:
            return super().exists(name)
        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = str(error.get("Code", ""))
            status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status == 403 or code in {"403", "AccessDenied", "Forbidden"}:
                return False
            raise
