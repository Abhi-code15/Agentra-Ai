"""Private local file storage manager with path traversal defense and SHA-256 integrity calculation."""
import hashlib
import os
import re
import uuid
from typing import Tuple
from app.core.config import settings
from app.core.exceptions import AgentraException, NotFoundException


class LocalStorageManager:
    """Manages secure reading, writing, and deletion of files on local disk."""

    SAFE_KEY_PATTERN = re.compile(r"^[a-f0-9]{32}\.dat$")

    def __init__(self, base_directory: str = settings.STORAGE_DIRECTORY):
        self.base_dir = os.path.abspath(base_directory)
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_absolute_path(self, storage_key: str) -> str:
        """Validates storage key and resolves absolute path, preventing path traversal."""
        if not self.SAFE_KEY_PATTERN.match(storage_key):
            raise AgentraException(
                code="INVALID_STORAGE_KEY",
                message="Storage key is invalid or contains prohibited characters.",
                status_code=400,
            )

        resolved_path = os.path.abspath(os.path.join(self.base_dir, storage_key))
        # Ensure path does not escape the configured base directory
        if not resolved_path.startswith(self.base_dir):
            raise AgentraException(
                code="PATH_TRAVERSAL_DETECTED",
                message="Security violation: Path traversal attempt detected.",
                status_code=403,
            )
        return resolved_path

    def save_file(self, file_bytes: bytes) -> Tuple[str, str, int]:
        """Saves file bytes to disk using a random UUID filename and computes SHA-256."""
        size = len(file_bytes)
        checksum = hashlib.sha256(file_bytes).hexdigest()

        # Generate unique storage key: <uuid4_hex>.dat
        storage_key = f"{uuid.uuid4().hex}.dat"
        file_path = self._get_absolute_path(storage_key)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        return storage_key, checksum, size

    def read_file(self, storage_key: str) -> bytes:
        """Reads and returns file bytes from disk."""
        file_path = self._get_absolute_path(storage_key)
        if not os.path.exists(file_path):
            raise NotFoundException(
                code="FILE_NOT_FOUND_ON_DISK",
                message="The requested file payload was not found on disk.",
            )
        with open(file_path, "rb") as f:
            return f.read()

    def delete_file(self, storage_key: str) -> bool:
        """Securely removes a file from disk."""
        try:
            file_path = self._get_absolute_path(storage_key)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
