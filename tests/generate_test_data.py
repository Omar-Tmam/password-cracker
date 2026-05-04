"""
Generate a test wordlist + a known target hash for demos.

Usage:
    python tests/generate_test_data.py [size] [algo]

Outputs:
    data/wordlist.txt          (one word per line)
    data/sample_target_hash.txt (single line: <algo>:<hex>:<plaintext>)
"""
import os
import random
import string
import sys
import hashlib

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
    algo = sys.argv[2] if len(sys.argv) > 2 else "sha256"

    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(here), "data")
    os.makedirs(data_dir, exist_ok=True)

    wordlist_path = os.path.join(data_dir, "wordlist.txt")
    target_path = os.path.join(data_dir, "sample_target_hash.txt")

    print(f"Generating {size:,} words -> {wordlist_path}")
    words = list(COMMON_PASSWORDS) + [random_word() for _ in range(size - len(COMMON_PASSWORDS))]
    random.shuffle(words)

    # Pick the target password from somewhere in the second half so neither
    # sequential nor parallel "wins by luck" in the first chunk.
    target_idx = random.randint(size // 2, size - 1)
    target_password = words[target_idx]

    with open(wordlist_path, "w", encoding="utf-8") as f:
        f.write("\n".join(words))

    h = hashlib.new(algo)
    h.update(target_password.encode("utf-8"))
    digest = h.hexdigest()

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(f"{algo}:{digest}:{target_password}\n")

    print(f"Target password: {target_password!r} (at line ~{target_idx + 1:,})")
    print(f"{algo} digest:   {digest}")
    print(f"Saved to:        {target_path}")
    print("\nQuick test:")
    print(f"  python -m src.sequential_cracker {wordlist_path} {digest} {algo}")


if __name__ == "__main__":
    main()
