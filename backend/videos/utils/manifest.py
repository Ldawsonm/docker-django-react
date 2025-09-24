def create_manifest_file(video: Video) -> str:
    """Create a manifest TSV file in GCS and return its URI."""
    client = storage.Client()
    bucket = client.bucket(MANIFEST_BUCKET)

    filename = f"{video.source}_{video.id}.tsv"
    blob = bucket.blob(filename)

    manifest = "TsvHttpData-1.0\n" + video.source_url + "\n"
    blob.upload_from_string(manifest, content_type="text/plain")

    blob.acl.all().grant_read()
    blob.acl.save()

    return f"gs://{MANIFEST_BUCKET}/{filename}"