#!/usr/bin/env python3
"""
Backup all configuration files to Cloud Storage
"""

import json
import os
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
BACKUP_BUCKET = f"gs://{PROJECT_ID}-config-backups"

# Configuration files and directories to backup
CONFIG_PATHS = [
    "config/",
    "deploy/",
    "agents/*/Dockerfile",
    "agents/*/requirements.txt",
    "cloud-run-service.yaml",
    "cloudbuild*.yaml",
    ".github/workflows/",
    "Makefile",
    "pyproject.toml",
    "pytest.ini",
    "mypy.ini",
    "requirements.txt",
    "scripts/*.yaml",
    "scripts/*.json",
    "terraform/",
    "docs/checklists/",
]


def create_backup_bucket():
    """Create a GCS bucket for configuration backups"""
    print("🪣 Creating configuration backup bucket...")

    # Check if bucket exists
    check_cmd = ["gsutil", "ls", BACKUP_BUCKET]
    result = subprocess.run(check_cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("   ✓ Bucket already exists: {BACKUP_BUCKET}")
        return True

    # Create bucket
    create_cmd = [
        "gsutil",
        "mb",
        "-p",
        PROJECT_ID,
        "-c",
        "STANDARD",
        "-l",
        "us-central1",
        "-b",
        "on",  # Uniform bucket-level access
        BACKUP_BUCKET,
    ]

    try:
        subprocess.run(create_cmd, check=True, capture_output=True, text=True)
        print("   ✅ Created bucket: {BACKUP_BUCKET}")

        # Set lifecycle rule to delete old backups after 90 days
        lifecycle_config = """
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 90,
          "matchesPrefix": ["config_backup/"]
        }
      }
    ]
  }
}
"""
        lifecycle_file = "/tmp/config_backup_lifecycle.json"
        with open(lifecycle_file, "w") as f:
            f.write(lifecycle_config)

        lifecycle_cmd = ["gsutil", "lifecycle", "set", lifecycle_file, BACKUP_BUCKET]
        subprocess.run(lifecycle_cmd, check=True, capture_output=True, text=True)
        print("   ✅ Set 90-day retention policy")

        return True

    except subprocess.CalledProcessError as e:
        print("   ❌ Failed to create bucket: {e.stderr}")
        return False


def collect_config_files():
    """Collect all configuration files for backup"""
    print("\n📂 Collecting configuration files...")

    project_root = Path(__file__).parent.parent
    config_files = []

    for pattern in CONFIG_PATHS:
        if "*" in pattern:
            # Handle glob patterns
            for path in project_root.glob(pattern):
                if path.is_file():
                    config_files.append(path.relative_to(project_root))
        else:
            path = project_root / pattern
            if path.exists():
                if path.is_dir():
                    # Add all files in directory recursively
                    for file_path in path.rglob("*"):
                        if file_path.is_file() and not file_path.name.startswith("."):
                            config_files.append(file_path.relative_to(project_root))
                else:
                    config_files.append(path.relative_to(project_root))

    # Remove duplicates and sort
    config_files = sorted(set(config_files))
    print("   ✅ Found {len(config_files)} configuration files")

    return config_files


def create_backup_archive(config_files):
    """Create a tar.gz archive of configuration files"""
    print("\n📦 Creating backup archive...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"config_backup_{timestamp}.tar.gz"
    archive_path = Path("/tmp") / archive_name
    project_root = Path(__file__).parent.parent

    with tarfile.open(archive_path, "w:gz") as tar:
        for config_file in config_files:
            full_path = project_root / config_file
            tar.add(full_path, arcname=config_file)

    print("   ✅ Created archive: {archive_path}")
    print("   📊 Archive size: {archive_path.stat().st_size / 1024 / 1024:.2f} MB")

    return archive_path, timestamp


def upload_to_gcs(archive_path, timestamp):
    """Upload backup archive to Google Cloud Storage"""
    print("\n☁️  Uploading to Cloud Storage...")

    gcs_path = f"{BACKUP_BUCKET}/config_backup/{timestamp}/{archive_path.name}"

    upload_cmd = ["gsutil", "cp", str(archive_path), gcs_path]

    try:
        subprocess.run(upload_cmd, check=True, capture_output=True, text=True)
        print("   ✅ Uploaded to: {gcs_path}")

        # Create metadata file
        metadata = {
            "timestamp": timestamp,
            "backup_date": datetime.now().isoformat(),
            "project_id": PROJECT_ID,
            "file_count": len(config_files),
            "archive_name": archive_path.name,
        }

        metadata_path = archive_path.parent / f"metadata_{timestamp}.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        metadata_gcs_path = f"{BACKUP_BUCKET}/config_backup/{timestamp}/metadata.json"
        subprocess.run(
            ["gsutil", "cp", str(metadata_path), metadata_gcs_path],
            check=True,
            capture_output=True,
            text=True,
        )

        # Clean up local files
        archive_path.unlink()
        metadata_path.unlink()

        return gcs_path

    except subprocess.CalledProcessError as e:
        print("   ❌ Upload failed: {e.stderr}")
        return None


def create_restore_script():
    """Create script to restore configurations from backup"""
    print("\n📝 Creating restore script...")

    restore_script = f"""#!/bin/bash
# Restore configuration from backup

if [ $# -eq 0 ]; then
    echo "Usage: $0 <timestamp>"
    echo "Example: $0 20240529_120000"
    echo ""
    echo "Available backups:"
    gsutil ls {BACKUP_BUCKET}/config_backup/ | grep -E '[0-9]{{8}}_[0-9]{{6}}'
    exit 1
fi

TIMESTAMP=$1
BACKUP_PATH="{BACKUP_BUCKET}/config_backup/${{TIMESTAMP}}"

echo "🔄 Restoring configuration backup..."
echo "   Timestamp: $TIMESTAMP"
echo "   Source: $BACKUP_PATH"
echo ""
echo "⚠️  WARNING: This will overwrite existing configuration files!"
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create temp directory
    TEMP_DIR=$(mktemp -d)

    # Download archive
    echo "📥 Downloading backup..."
    gsutil cp "${{BACKUP_PATH}}/config_backup_${{TIMESTAMP}}.tar.gz" "${{TEMP_DIR}}/"

    if [ $? -ne 0 ]; then
        echo "❌ Failed to download backup"
        rm -rf "${{TEMP_DIR}}"
        exit 1
    fi

    # Extract archive
    echo "📦 Extracting archive..."
    tar -xzf "${{TEMP_DIR}}/config_backup_${{TIMESTAMP}}.tar.gz" -C .

    if [ $? -eq 0 ]; then
        echo "✅ Configuration restored successfully!"

        # Download and show metadata
        gsutil cp "${{BACKUP_PATH}}/metadata.json" "${{TEMP_DIR}}/"
        echo ""
        echo "📊 Backup metadata:"
        cat "${{TEMP_DIR}}/metadata.json"
    else
        echo "❌ Restore failed!"
    fi

    # Clean up
    rm -rf "${{TEMP_DIR}}"
else
    echo "Restore cancelled."
fi
"""

    script_path = Path(__file__).parent / "restore_configuration.sh"
    with open(script_path, "w") as f:
        f.write(restore_script)
    os.chmod(script_path, 0o755)

    print("   ✅ Created restore script: {script_path}")

    return True


def create_scheduled_backup_script():
    """Create script for scheduled configuration backups"""
    print("\n⏰ Creating scheduled backup script...")

    scheduled_script = f"""#!/bin/bash
# Deploy scheduled configuration backup

echo "🚀 Setting up scheduled configuration backup..."

# Create Cloud Function for configuration backup
cat > /tmp/config_backup_function.py << 'EOF'
import subprocess
import json
from datetime import datetime

def config_backup(request):
    \"\"\"Cloud Function to backup configurations\"\"\"

    try:
        # Run the backup script
        result = subprocess.run([
            "python3", "-m", "scripts.backup_configurations", "--auto"
        ], capture_output=True, text=True, check=True)

        return {{
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "output": result.stdout
        }}
    except subprocess.CalledProcessError as e:
        return {{
            "status": "error",
            "error": str(e),
            "stderr": e.stderr
        }}, 500
EOF

# Deploy function
gcloud functions deploy config-backup \\
    --runtime python311 \\
    --trigger-http \\
    --entry-point config_backup \\
    --source /tmp \\
    --project {PROJECT_ID} \\
    --region us-central1 \\
    --service-account sentinelops-sa@{PROJECT_ID}.iam.gserviceaccount.com \\
    --allow-unauthenticated

# Create weekly Cloud Scheduler job
gcloud scheduler jobs create http config-weekly-backup \\
    --location us-central1 \\
    --schedule "0 3 * * 0" \\
    --uri https://us-central1-{PROJECT_ID}.cloudfunctions.net/config-backup \\
    --http-method GET \\
    --project {PROJECT_ID} \\
    --description "Weekly configuration backup at 3 AM Sunday"

echo "✅ Scheduled backup configured!"
"""

    script_path = Path(__file__).parent / "deploy_config_backup.sh"
    with open(script_path, "w") as f:
        f.write(scheduled_script)
    os.chmod(script_path, 0o755)

    print("   ✅ Created deployment script: {script_path}")

    return True


def main():
    """Main backup function"""
    print("🔄 Backing up SentinelOps configurations")
    print("=" * 60)

    # Check if running in auto mode
    auto_mode = "--auto" in sys.argv

    # Create backup bucket
    if not create_backup_bucket():
        return False

    # Collect configuration files
    global config_files
    config_files = collect_config_files()

    # Create backup archive
    archive_path, timestamp = create_backup_archive(config_files)

    # Upload to GCS
    gcs_path = upload_to_gcs(archive_path, timestamp)

    if gcs_path:
        print("\n✅ Configuration backup completed!")
        print("   Location: {gcs_path}")

        if not auto_mode:
            # Create restore script
            create_restore_script()

            # Create scheduled backup script
            create_scheduled_backup_script()

            print("\nNext steps:")
            print(
                "1. Test restore with: ./scripts/restore_configuration.sh <timestamp>"
            )
            print("2. Enable scheduled backups: ./scripts/deploy_config_backup.sh")

        return True
    else:
        print("\n❌ Configuration backup failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
