import argparse
import csv
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

EXPECTED_HEADER = ["id", "name", "website", "message", "time"]
TIMEOUT = 30


def download(url: str, key: str, workdir: Path) -> Path:
    """downloads the csv from the url"""
    req = urllib.request.Request(
        url,
        headers={
            "x-export-key": key.strip(),
            "accept": "text/csv",
            "user-agent": "guestbook-export/1.0",
        },
    )

    fd, tmp_name = tempfile.mkstemp(dir=workdir, prefix=".messages-", suffix=".part")
    tmp = Path(tmp_name)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp, os.fdopen(
            fd, "wb"
        ) as out:
            ctype = resp.headers.get("content-type", "")
            if "csv" not in ctype:
                print(f"warning: unexpected content-type {ctype!r}", file=sys.stderr)
            shutil.copyfileobj(resp, out)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return tmp


def validate(path: Path) -> int:
    """validate the csv maches what we expect."""
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("file is empty")
        if header != EXPECTED_HEADER:
            raise ValueError(f"unexpected header: {header}")
        return sum(1 for _ in reader)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("GUESTBOOK_URL"))
    parser.add_argument("--out", type=Path, default=Path("messages.csv"))
    parser.add_argument(
        "--key",
        default=os.environ.get("GUESTBOOK_KEY"),
        help="export key (defaults to $GUESTBOOK_KEY)",
    )

    args = parser.parse_args()

    if not args.key:
        print("error: no key. set GUESTBOOK_KEY or pass --key", file=sys.stderr)
        return

    if not args.url:
        print("error: no url. set GUESTBOOK_URL or pass --url", file=sys.stderr)
        return

    out = args.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        tmp = download(args.url, args.key, out.parent)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("error: 404, got wrong key, or wrong URL", file=sys.stderr)
        else:
            print(f"error: HTTP {e.code} {e.reason}", file=sys.stderr)
        return
    except urllib.error.URLError as e:
        print(f"error: could not reach {args.url}: {e.reason}", file=sys.stderr)
        return

    try:
        rows = validate(tmp)
    except (ValueError, UnicodeDecodeError) as e:
        tmp.unlink(missing_ok=True)
        print(f"error: bad response ({e}). {args.out} left untouched", file=sys.stderr)
        return 1

    os.replace(tmp, out)
    print(f"wrote {rows} entries to {out}")

if __name__ == "__main__":
    main()
