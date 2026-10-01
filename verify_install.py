"""Verify installed files against MANIFEST.txt (CRLF-normalised sha256 prefixes + bundle hash)."""
import hashlib, os, sys


def sha16(data: bytes) -> str:
    normalised = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return hashlib.sha256(normalised).hexdigest()[:16]


def bundle_hash(file_hashes: dict[str, str]) -> str:
    concatenated = "".join(sha for _, sha in sorted(file_hashes.items()))
    return hashlib.sha256(concatenated.encode()).hexdigest()[:24]


def load_manifest(path):
    bundle, files = None, {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n\r")
            if not line or line.startswith("#"):
                continue
            if line.startswith("bundle:"):
                bundle = line.split("\t", 1)[1].strip()
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                files[parts[1].strip()] = parts[0].strip()
    return bundle, files


def verify(manifest_path="MANIFEST.txt"):
    bundle_expected, files = load_manifest(manifest_path)
    ok, actual_hashes = True, {}
    for local_path, expected in files.items():
        win_path = local_path.replace("/", os.sep)
        if not os.path.exists(win_path):
            print("MISSING  %s" % local_path)
            ok = False
            actual_hashes[local_path] = "0" * 16
            continue
        with open(win_path, "rb") as f:
            actual = sha16(f.read())
        actual_hashes[local_path] = actual
        if actual == expected:
            print("OK       %s" % local_path)
        else:
            print("MISMATCH %s\n         expected: %s\n         actual:   %s" % (local_path, expected, actual))
            ok = False
    print()
    if bundle_expected:
        actual_bundle = bundle_hash(actual_hashes)
        if actual_bundle == bundle_expected:
            print("Bundle OK:       %s" % actual_bundle)
        else:
            print("Bundle MISMATCH\n  expected: %s\n  actual:   %s" % (bundle_expected, actual_bundle))
            ok = False
    print()
    if ok:
        print("All files match.")
    else:
        print("Some files are out of date or missing.")
        sys.exit(1)


if __name__ == "__main__":
    verify()
