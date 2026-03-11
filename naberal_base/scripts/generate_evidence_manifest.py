#!/usr/bin/env python3
"""Generate SHA256 manifest for all evidence files."""

import os
import hashlib
from pathlib import Path


def sha256_file(filepath):
    """Calculate SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


def main():
    """Generate evidence manifest."""
    output_lines = []

    # Hash all files in out/evidence
    for root, dirs, files in os.walk('out/evidence'):
        for file in files:
            filepath = Path(root) / file
            try:
                hash_val = sha256_file(filepath)
                # Use forward slashes for consistency
                path_str = str(filepath).replace('\\', '/')
                output_lines.append(f'{hash_val}  {path_str}')
            except Exception as e:
                print(f'[WARN] Failed to hash {filepath}: {e}')

    # Sort for consistency
    output_lines.sort()

    # Write manifest
    with open('out/release/audit/EVIDENCE_SHA256.txt', 'w') as f:
        f.write('\n'.join(output_lines))
        f.write('\n')

    print(f'[SEAL-1] Generated hashes for {len(output_lines)} evidence files')


if __name__ == '__main__':
    main()
