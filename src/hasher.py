"""
Shared hashing module (DRY).
EN: All cracker variants import hash_word() from here so the hashing logic
    is identical across Sequential / Threaded / Pool / Worker-Pool / Pipeline.
AR: كل أنواع الكراكر بتستخدم نفس الدالة دي عشان المقارنة تبقى عادلة.
"""
import hashlib

ALGORITHM = "sha256"


def hash_word(word: str, algorithm: str = ALGORITHM) -> str:
    """Return SHA-256 hex digest of `word`."""
    return hashlib.sha256(word.encode("utf-8")).hexdigest()


def normalize_hash(target: str) -> str:
    return target.strip().lower()
