from binascii import hexlify, unhexlify
from struct import pack, unpack
import binascii
import os
import re
import tempfile


def out(x):
    print x

log = lambda x: out(x)


BLOB_SUFFIX = ".blob"
LAYOUT_MARKER = '.layout'


def p64(v):
    """Pack an integer or long into a 8-byte string"""
    return pack(">Q", v)


def u64(v):
    """Unpack an 8-byte string into a 64-bit long integer."""
    return unpack(">Q", v)[0]


def oid_repr(oid):
    if isinstance(oid, bytes) and len(oid) == 8:
        # Convert to hex and strip leading zeroes.
        as_hex = hexlify(oid).lstrip(b'0')
        # Ensure two characters per input byte.
        if len(as_hex) & 1:
            as_hex = b'0' + as_hex
        elif as_hex == b'':
            as_hex = b'00'
        return '0x' + as_hex.decode()
    else:
        return repr(oid)

serial_repr = oid_repr
tid_repr = serial_repr


def repr_to_oid(repr):
    repr = ascii_bytes(repr)
    if repr.startswith(b"0x"):
        repr = repr[2:]
    as_bin = unhexlify(repr)
    as_bin = b"\x00" * (8 - len(as_bin)) + as_bin
    return as_bin


def ascii_bytes(x):
    if isinstance(x, str):
        x = x.encode('ascii')
    return x


class BushyLayout(object):
    """A bushy directory layout for blob directories.

    Creates an 8-level directory structure (one level per byte) in
    big-endian order from the OID of an object.

    """

    blob_path_pattern = re.compile(
        r'(0x[0-9a-f]{1,2}\%s){7,7}0x[0-9a-f]{1,2}$' % os.path.sep)

    def oid_to_path(self, oid):
        directories = []
        # Create the bushy directory structure with the least significant byte
        # first
        for byte in ascii_bytes(oid):
            if isinstance(byte, long):  # Py3k iterates byte strings as ints
                hex_segment_bytes = b'0x' + binascii.hexlify(bytes([byte]))
                hex_segment_string = hex_segment_bytes.decode('ascii')
            else:
                hex_segment_string = '0x%s' % binascii.hexlify(byte)
            directories.append(hex_segment_string)

        return os.path.sep.join(directories)

    def path_to_oid(self, path):
        if self.blob_path_pattern.match(path) is None:
            raise ValueError("Not a valid OID path: `%s`" % path)
        path = [ascii_bytes(x) for x in path.split(os.path.sep)]
        # Each path segment stores a byte in hex representation. Turn it into
        # an int and then get the character for our byte string.
        oid = b''.join(binascii.unhexlify(byte[2:]) for byte in path)
        return oid

    def getBlobFilePath(self, oid, tid):
        """Given an oid and a tid, return the full filename of the
        'committed' blob file related to that oid and tid.

        """
        oid_path = self.oid_to_path(oid)
        filename = "%s%s" % (tid_repr(tid), BLOB_SUFFIX)
        return os.path.join(oid_path, filename)


class FilesystemHelper:
    """Copy of ZODB.blob.FilesystemHelper.
    Mainly """

    def __init__(self, base_dir):
        self.base_dir = os.path.abspath(base_dir) + os.path.sep
        self.temp_dir = os.path.join(base_dir, 'tmp')

        self.layout_name = 'bushy'
        self.layout = BushyLayout()

    def create(self):
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, 0o700)
            log("Blob directory '%s' does not exist. "
                "Created new directory." % self.base_dir)
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, 0o700)
            log("Blob temporary directory '%s' does not exist. "
                "Created new directory." % self.temp_dir)

        layout_marker_path = os.path.join(self.base_dir, LAYOUT_MARKER)
        if not os.path.exists(layout_marker_path):
            with open(layout_marker_path, 'w') as layout_marker:
                layout_marker.write(self.layout_name)
        else:
            with open(layout_marker_path, 'r') as layout_marker:
                layout = layout_marker.read().strip()
            if layout != self.layout_name:
                raise ValueError(
                    "Directory layout `%s` selected for blob directory %s, "
                    "but marker found for layout `%s`" %
                    (self.layout_name, self.base_dir, layout))

    def isSecure(self, path):
        """Ensure that (POSIX) path mode bits are 0700."""
        return (os.stat(path).st_mode & 0o77) == 0

    def checkSecure(self):
        if not self.isSecure(self.base_dir):
            log('Blob dir %s has insecure mode setting' % self.base_dir)

    def getPathForOID(self, oid, create=False):
        """Given an OID, return the path on the filesystem where
        the blob data relating to that OID is stored.

        If the create flag is given, the path is also created if it didn't
        exist already.

        """
        # OIDs are numbers and sometimes passed around as integers. For our
        # computations we rely on the 64-bit packed string representation.
        if isinstance(oid, int):
            oid = p64(oid)

        path = self.layout.oid_to_path(oid)
        path = os.path.join(self.base_dir, path)

        if create and not os.path.exists(path):
            try:
                os.makedirs(path, 0o700)
            except OSError:
                # We might have lost a race.  If so, the directory
                # must exist now
                assert os.path.exists(path)
        return path

    def getOIDForPath(self, path):
        """Given a path, return an OID, if the path is a valid path for an
        OID. The inverse function to `getPathForOID`.

        Raises ValueError if the path is not valid for an OID.

        """
        path = path[len(self.base_dir):]
        return self.layout.path_to_oid(path)

    def createPathForOID(self, oid):
        """Given an OID, creates a directory on the filesystem where
        the blob data relating to that OID is stored, if it doesn't exist.
        """
        return self.getPathForOID(oid, create=True)

    def getBlobFilename(self, oid, tid):
        """Given an oid and a tid, return the full filename of the
        'committed' blob file related to that oid and tid.

        """
        # TIDs are numbers and sometimes passed around as integers. For our
        # computations we rely on the 64-bit packed string representation
        if isinstance(oid, int):
            oid = p64(oid)
        if isinstance(tid, int):
            tid = p64(tid)
        return os.path.join(self.base_dir,
                            self.layout.getBlobFilePath(oid, tid),
                            )

    def blob_mkstemp(self, oid, tid):
        """Given an oid and a tid, return a temporary file descriptor
        and a related filename.

        The file is guaranteed to exist on the same partition as committed
        data, which is important for being able to rename the file without a
        copy operation.  The directory in which the file will be placed, which
        is the return value of self.getPathForOID(oid), must exist before this
        method may be called successfully.

        """
        oidpath = self.getPathForOID(oid)
        fd, name = tempfile.mkstemp(suffix='.tmp',
                                    prefix=tid_repr(tid),
                                    dir=oidpath)
        return fd, name

    def splitBlobFilename(self, filename):
        """Returns the oid and tid for a given blob filename.

        If the filename cannot be recognized as a blob filename, (None, None)
        is returned.

        """
        if not filename.endswith(BLOB_SUFFIX):
            return None, None
        path, filename = os.path.split(filename)
        oid = self.getOIDForPath(path)

        serial = filename[:-len(BLOB_SUFFIX)]
        serial = repr_to_oid(serial)
        return oid, serial

    def getOIDsForSerial(self, search_serial):
        """Return all oids related to a particular tid that exist in
        blob data.

        """
        oids = []
        for oid, oidpath in self.listOIDs():
            for filename in os.listdir(oidpath):
                blob_path = os.path.join(oidpath, filename)
                oid, serial = self.splitBlobFilename(blob_path)
                if search_serial == serial:
                    oids.append(oid)
        return oids

    def listOIDs(self):
        """Iterates over all paths under the base directory that contain blob
        files.
        """
        for path, dirs, files in os.walk(self.base_dir):
            # Make sure we traverse in a stable order. This is mainly to make
            # testing predictable.
            dirs.sort()
            files.sort()
            try:
                oid = self.getOIDForPath(path)
            except ValueError:
                continue
            yield oid, path
