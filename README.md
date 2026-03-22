# MEGA S4 Object Storage - Home Assistant Backup Integration

Custom integration for [Home Assistant](https://www.home-assistant.io/) that allows you to store backups in [MEGA S4](https://mega.io/objectstorage) Object Storage buckets.

MEGA S4 is an S3-compatible object storage service. The official Home Assistant AWS S3 integration explicitly blocks non-Amazon endpoints, so this custom integration was created to work directly with MEGA S4's S3-compatible API.

## Features

- **Native backup agent**: Integrates with Home Assistant's built-in backup system (2025.1+)
- **Automatic backups**: Works with HA's automatic backup scheduler
- **Multipart upload**: Large backups are uploaded using S3 multipart uploads
- **Region selection**: Supports all MEGA S4 regions (Amsterdam, Bettembourg, Montreal, Vancouver)
- **Prefix/folder support**: Organize backups in a specific folder within the bucket
- **PT-BR translation**: Includes Portuguese (Brazil) translation

## Requirements

- Home Assistant 2025.1 or later
- A MEGA account with an S4-enabled plan (Pro Flexi or Business)
- An existing S4 bucket
- IAM credentials (Access Key ID + Secret Access Key)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add this repository URL with category **Integration**
4. Search for "MEGA S4" and install
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/mega_s4` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **MEGA S4 Object Storage**
3. Fill in:
   - **Access Key ID**: Your MEGA S4 IAM access key
   - **Secret Access Key**: Your MEGA S4 IAM secret key
   - **Bucket name**: The name of your existing S4 bucket
   - **Region**: Select the data center region
   - **Prefix** (optional): Folder path within the bucket (e.g. `homeassistant/backups`)
4. The integration will test the connection and confirm access
5. Once configured, go to **Settings → System → Backups → Backup settings** and enable the MEGA S4 location

## MEGA S4 Setup

### 1. Enable S4

You need a MEGA Pro Flexi or Business plan. S4 Object Storage is included with these plans.

### 2. Create a Bucket

Go to the MEGA S4 dashboard and create a bucket in your preferred region.

### 3. Create IAM Credentials

Create an IAM user with an access key. The user needs the following S3 permissions on the bucket:

- `s3:ListBucket`
- `s3:GetObject`
- `s3:PutObject`
- `s3:DeleteObject`
- `s3:CreateMultipartUpload` / `s3:AbortMultipartUpload` / `s3:CompleteMultipartUpload` / `s3:ListMultipartUploadParts` / `s3:UploadPart`

### Available Regions

| Region | Location |
|--------|----------|
| `eu-central-1` | Amsterdam, Netherlands |
| `eu-central-2` | Bettembourg, Luxembourg |
| `ca-central-1` | Montreal, Canada |
| `ca-west-1` | Vancouver, Canada |

## How it works

The integration registers itself as a **backup agent** in Home Assistant's backup system. When a backup is created:

1. The `.tar` backup file is uploaded to S4 (using multipart upload for files > 20 MiB)
2. A `.metadata.json` file is uploaded alongside it with backup metadata
3. When listing backups, the integration reads the metadata files to reconstruct the backup list

Files are stored as:
```
<bucket>/<prefix>/
  ├── Home_Assistant_2025-03-22.tar
  ├── Home_Assistant_2025-03-22.metadata.json
  ├── Home_Assistant_2025-03-21.tar
  ├── Home_Assistant_2025-03-21.metadata.json
  └── ...
```

## Troubleshooting

### Connection errors

- Verify your MEGA S4 subscription is active and S4 is enabled
- Check that the bucket exists in the selected region
- Ensure your network allows HTTPS connections to `s3.<region>.s4.mega.io`

### Authentication errors

- Verify the Access Key ID and Secret Access Key are correct
- Ensure the IAM user has the required permissions on the bucket

### Debug logging

Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.mega_s4: debug
    aiobotocore: debug
    botocore: debug
```

## Technical details

- Uses `aiobotocore` (async S3 client) with path-style addressing and SigV4 signatures
- S3 endpoint: `https://s3.<region>.s4.mega.io`
- Implements the `BackupAgent` interface from `homeassistant.components.backup`
- Backup list is cached for 5 minutes to reduce API calls

## License

MIT
