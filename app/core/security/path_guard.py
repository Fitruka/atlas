"""Dosya ve path guvenligi.

Path traversal engelleme, symlink korumasi,
arsiv guvenlik kontrolleri.
"""

import logging
import os
import uuid
from typing import Any

logger = logging.getLogger(__name__)

_MAX_ARCHIVE_ENTRIES = 10000
_MAX_ARCHIVE_SIZE = 500 * 1024 * 1024
_MAX_SINGLE_FILE = 100 * 1024 * 1024


class PathGuard:
    """Dosya ve path guvenlik koruyucu."""

    def __init__(self, base_dirs=None):
        """PathGuard baslatir."""
        self._base_dirs = base_dirs or []
        self._check_count = 0
        self._violation_count = 0

    def check_containment(self, path, base_dir=""):
        """Path containment kontrolu."""
        self._check_count += 1
        if not path:
            return False, "Bos path"
        try:
            real_path = os.path.realpath(path)
        except (OSError, ValueError):
            self._violation_count += 1
            return False, "Path resolve hatasi"
        dirs = [base_dir] if base_dir else self._base_dirs
        if not dirs:
            return True, "OK (kontrol yok)"
        for bdir in dirs:
            try:
                real_base = os.path.realpath(bdir)
                if real_path.startswith(real_base + os.sep) or real_path == real_base:
                    return True, "OK"
            except (OSError, ValueError):
                continue
        self._violation_count += 1
        return False, f"Path containment ihlali: {path}"
    def reject_symlink(self, path):
        """Symlink kontrolu."""
        self._check_count += 1
        if os.path.islink(path):
            self._violation_count += 1
            return False, f"Symlink reddedildi: {path}"
        return True, "OK"

    def check_path_traversal(self, path):
        """Path traversal kontrolu."""
        self._check_count += 1
        normalized = os.path.normpath(path)
        if ".." in normalized.split(os.sep):
            self._violation_count += 1
            return False, "Path traversal tespit edildi"
        if "\x00" in path:
            self._violation_count += 1
            return False, "Null byte tespit edildi"
        return True, "OK"

    def generate_safe_filename(self, extension=""):
        """UUID tabanli guvenli dosya adi uretir."""
        name = str(uuid.uuid4())
        if extension:
            ext = extension.lstrip(".")
            return f"{name}.{ext}"
        return name

    def check_archive_entry(self, entry_name, entry_size, entry_count):
        """Arsiv giris guvenlik kontrolu."""
        self._check_count += 1
        if entry_count > _MAX_ARCHIVE_ENTRIES:
            self._violation_count += 1
            return False, f"Cok fazla arsiv girisi: {entry_count}"
        if entry_size > _MAX_SINGLE_FILE:
            self._violation_count += 1
            return False, f"Dosya boyutu asimi: {entry_size}"
        ok, reason = self.check_path_traversal(entry_name)
        if not ok:
            return False, reason
        if entry_name.startswith("/"):
            self._violation_count += 1
            return False, "Mutlak yol arsiv girisi"
        return True, "OK"

    def check_config_include(self, include_path, config_dir):
        """Config include path kontrolu."""
        return self.check_containment(include_path, config_dir)

    def add_base_dir(self, directory):
        """Izin verilen temel dizin ekler."""
        if directory not in self._base_dirs:
            self._base_dirs.append(directory)

    def get_stats(self):
        """Istatistikleri dondurur."""
        return {
            "total_checks": self._check_count,
            "violations": self._violation_count,
            "base_dirs": len(self._base_dirs),
        }
