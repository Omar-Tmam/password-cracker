"""SHA-256 hashing used by all cracker variants."""
import hashlib


def hash_word(word: str) -> str:
    return hashlib.sha256(word.encode("utf-8")).hexdigest()


def normalize_hash(target: str) -> str:
    return target.strip().lower()
