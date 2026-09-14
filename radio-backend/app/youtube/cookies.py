"""
YouTube Cookies Management Utility

Handles extraction, validation, and loading of browser cookies for yt-dlp.
Supports both raw Netscape format and Base64-encoded cookies.

Usage:
    1. Extract cookies from your browser using:
       - Chrome/Edge/Firefox: Install "Get cookies.txt" extension
       - Go to youtube.com (logged in)
       - Download cookies.txt

    2. Set environment variable or file:
       - Raw cookies: YOUTUBE_COOKIES={raw_cookies_content}
       - Base64 encoded: YOUTUBE_COOKIES_B64={base64_encoded_cookies}
       - File fallback: ./cookies_b64.txt

    3. yt-dlp will automatically use cookies for authentication
"""

import base64
import os
import re
from pathlib import Path
from typing import Optional

from app.logger.setup import get_logger

logger = get_logger("youtube_cookies")


class CookiesValidator:
    """Validates Netscape format cookies file."""

    # Netscape format: domain, flag, path, secure, expiration, name, value
    NETSCAPE_COOKIE_PATTERN = re.compile(
        r'^([^\s]+)\s+'
        r'(TRUE|FALSE)\s+'
        r'([^\s]+)\s+'
        r'(TRUE|FALSE)\s+'
        r'(\d+)\s+'
        r'([^\s]+)\s+'
        r'(.*)$'
    )

    @staticmethod
    def validate_netscape_format(content: str) -> tuple[bool, Optional[str]]:
        """
        Validate if content is in Netscape cookie format.

        Returns:
            (is_valid, error_message)
        """
        lines = content.strip().split('\n')
        if not lines:
            return False, "Cookies file is empty"

        valid_cookies = 0
        for i, line in enumerate(lines, 1):
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            if not CookiesValidator.NETSCAPE_COOKIE_PATTERN.match(line):
                return False, f"Invalid format at line {i}: {line[:50]}"
            valid_cookies += 1

        if valid_cookies == 0:
            return False, "No valid cookies found in file"

        return True, None

    @staticmethod
    def has_youtube_cookies(content: str) -> bool:
        """Check if cookies contain YouTube-related domains."""
        youtube_domains = ('.youtube.com', '.googlevideo.com', 'youtube.com', 'googlevideo.com')
        return any(domain in content for domain in youtube_domains)


class CookiesManager:
    """Manages YouTube cookies: load, validate, and setup for yt-dlp."""

    def __init__(self, cookies_path: str = "/tmp/youtube_cookies.txt"):
        self.cookies_path = cookies_path
        self.validator = CookiesValidator()

    def load_from_env_or_file(
        self,
        env_var_raw: str = "YOUTUBE_COOKIES",
        env_var_b64: str = "YOUTUBE_COOKIES_B64",
        fallback_file: Optional[str] = None,
    ) -> bool:
        """
        Load cookies from environment variable or file.

        Priority:
        1. Raw cookies from YOUTUBE_COOKIES env var
        2. Base64 cookies from YOUTUBE_COOKIES_B64 env var
        3. Base64 cookies from fallback_file (e.g., cookies_b64.txt)

        Returns:
            True if cookies were successfully loaded and written
        """
        raw_cookies = os.getenv(env_var_raw)
        if raw_cookies:
            return self._write_cookies(raw_cookies, source=f"env var {env_var_raw}")

        b64_cookies = os.getenv(env_var_b64)
        if b64_cookies:
            return self._write_cookies_from_b64(b64_cookies, source=f"env var {env_var_b64}")

        if fallback_file and os.path.exists(fallback_file):
            try:
                b64_cookies = Path(fallback_file).read_text(encoding="utf-8").strip()
                return self._write_cookies_from_b64(b64_cookies, source=f"file {fallback_file}")
            except Exception as exc:
                logger.error(f"Failed to read fallback cookies file {fallback_file}: {exc}")

        logger.warning("No YouTube cookies available (env var not set, fallback file missing)")
        return False

    def _write_cookies(self, raw_cookies: str, source: str = "unknown") -> bool:
        """Write raw cookies to file and validate."""
        try:
            # Validate before writing
            is_valid, error = self.validator.validate_netscape_format(raw_cookies)
            if not is_valid:
                logger.error(f"Invalid cookies format from {source}: {error}")
                return False

            # Warn if no YouTube cookies found
            if not self.validator.has_youtube_cookies(raw_cookies):
                logger.warning(f"Cookies from {source} don't contain YouTube domains")

            Path(self.cookies_path).write_text(raw_cookies, encoding="utf-8")
            logger.info(f"YouTube cookies written from {source} to {self.cookies_path}")
            return True
        except Exception as exc:
            logger.error(f"Failed to write cookies from {source}: {exc}")
            return False

    def _write_cookies_from_b64(self, b64_cookies: str, source: str = "unknown") -> bool:
        """Decode base64 cookies and write to file."""
        try:
            raw = base64.b64decode(b64_cookies).decode("utf-8", errors="replace")
            return self._write_cookies(raw, source=f"{source} (decoded)")
        except Exception as exc:
            logger.error(f"Failed to decode base64 cookies from {source}: {exc}")
            return False

    def cookies_exist(self) -> bool:
        """Check if cookies file exists and is readable."""
        return os.path.exists(self.cookies_path)

    def get_cookies_for_ytdlp(self) -> Optional[str]:
        """Get cookies path if available, None otherwise."""
        if self.cookies_exist():
            return self.cookies_path
        return None


# Singleton instance
_cookies_manager: Optional[CookiesManager] = None


def get_cookies_manager() -> CookiesManager:
    """Get or create the global cookies manager instance."""
    global _cookies_manager
    if _cookies_manager is None:
        _cookies_manager = CookiesManager()
    return _cookies_manager


def setup_youtube_cookies(
    cookies_path: str = "/tmp/youtube_cookies.txt",
    fallback_b64_file: Optional[str] = None,
) -> bool:
    """
    Initialize YouTube cookies once at module load.

    Args:
        cookies_path: Where to write cookies
        fallback_b64_file: Path to fallback base64 cookies file

    Returns:
        True if cookies were loaded successfully
    """
    manager = CookiesManager(cookies_path=cookies_path)
    return manager.load_from_env_or_file(fallback_file=fallback_b64_file)
