"""
Generate a test wordlist + a known SHA-256 target hash for demos.

Usage:
    python tests/generate_test_data.py [size]

Outputs:
    data/wordlist.txt           (one word per line)
    data/sample_target_hash.txt (single line: sha256:<hex>:<plaintext>)
"""
import hashlib
import os
import random
import string
import sys

COMMON_PASSWORDS = [
    "password", "123456", "qwerty", "letmein", "admin", "welcome",
    "monkey", "dragon", "iloveyou", "trustno1", "master", "shadow",
    "football", "baseball", "superman", "batman", "starwars",
    "abc123", "password1", "passw0rd",
]


def random_word(min_len=4, max_len=12) -> str:
    n = random.randint(min_len, max_len)
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def main():
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000

    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(here), "data")
    os.makedirs(data_dir, exist_ok=True)

    wordlist_path = os.path.join(data_dir, "wordlist.txt")
    target_path = os.path.join(data_dir, "sample_target_hash.txt")

    print(f"Generating {size:,} words -> {wordlist_path}")
    words = list(COMMON_PASSWORDS) + [random_word() for _ in range(size - len(COMMON_PASSWORDS))]
    random.shuffle(words)

    target_idx = random.randint(size // 2, size - 1)
    target_password = words[target_idx]

    with open(wordlist_path, "w", encoding="utf-8") as f:
        f.write("\n".join(words))

    digest = hashlib.sha256(target_password.encode("utf-8")).hexdigest()
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(f"sha256:{digest}:{target_password}\n")

    print(f"Target password: {target_password!r} (line ~{target_idx + 1:,})")
    print(f"sha256 digest:   {digest}")
    print(f"Saved to:        {target_path}")


if __name__ == "__main__":
    main()
