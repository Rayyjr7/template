"""In-memory TAR and ZIP construction and inspection helpers."""

import io
import tarfile
import zipfile

from .data_operations import to_bytes


def make_tar(
    files=None,
    symlinks=None,
    gzip=False,
    *,
    hardlinks=None,
    directories=None,
    compression=None,
):
    """Build a TAR archive containing custom paths, links, and raw file bytes."""
    if gzip:
        if compression not in (None, "gz"):
            raise ValueError("gzip=True conflicts with the selected compression")
        compression = "gz"

    modes = {None: "w", "gz": "w:gz", "bz2": "w:bz2", "xz": "w:xz"}
    if compression not in modes:
        raise ValueError("compression must be None, 'gz', 'bz2', or 'xz'")

    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode=modes[compression]) as archive:
        for path in directories or []:
            entry = tarfile.TarInfo(str(path).rstrip("/") + "/")
            entry.type = tarfile.DIRTYPE
            entry.mode = 0o755
            archive.addfile(entry)

        for path, content in (files or {}).items():
            content = to_bytes(content)
            entry = tarfile.TarInfo(str(path))
            entry.size = len(content)
            entry.mode = 0o644
            archive.addfile(entry, io.BytesIO(content))

        for path, target in (symlinks or {}).items():
            entry = tarfile.TarInfo(str(path))
            entry.type = tarfile.SYMTYPE
            entry.linkname = str(target)
            entry.mode = 0o777
            archive.addfile(entry)

        for path, target in (hardlinks or {}).items():
            entry = tarfile.TarInfo(str(path))
            entry.type = tarfile.LNKTYPE
            entry.linkname = str(target)
            archive.addfile(entry)

    return output.getvalue()


def make_zip(files=None, symlinks=None, directories=None, *, compression=True):
    """Build a ZIP archive containing custom paths and Unix symlink entries."""
    method = zipfile.ZIP_DEFLATED if compression else zipfile.ZIP_STORED
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", method) as archive:
        for path in directories or []:
            entry = zipfile.ZipInfo(str(path).rstrip("/") + "/")
            entry.external_attr = 0o40755 << 16
            archive.writestr(entry, b"")

        for path, content in (files or {}).items():
            archive.writestr(str(path), to_bytes(content))

        for path, target in (symlinks or {}).items():
            entry = zipfile.ZipInfo(str(path))
            entry.create_system = 3
            entry.external_attr = 0o120777 << 16
            archive.writestr(entry, to_bytes(target))

    return output.getvalue()


def list_tar(data):
    """Return metadata dictionaries without extracting a TAR archive."""
    with tarfile.open(fileobj=io.BytesIO(to_bytes(data)), mode="r:*") as archive:
        return [
            {
                "name": member.name,
                "size": member.size,
                "type": member.type.decode(errors="replace"),
                "linkname": member.linkname,
            }
            for member in archive.getmembers()
        ]


def list_zip(data):
    """Return metadata dictionaries without extracting a ZIP archive."""
    with zipfile.ZipFile(io.BytesIO(to_bytes(data))) as archive:
        return [
            {
                "name": member.filename,
                "size": member.file_size,
                "compressed_size": member.compress_size,
                "mode": member.external_attr >> 16,
            }
            for member in archive.infolist()
        ]
