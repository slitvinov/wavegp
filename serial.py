import numpy as np
import struct


class UnknownFormatString(Exception):
    pass


dtype = np.dtype("uint8")
max_val = 256


def serial(fmt, *args):
    assert len(fmt) == len(args)
    buf = bytearray()
    for f, a in zip(fmt, args):
        if f == "i":
            buf.extend(struct.pack("<i", a))
        elif f == "S":
            buf.extend(struct.pack("<i", len(a)))
            for s in a:
                buf.extend(struct.pack("<i", len(s)))
                buf.extend(s.encode("utf-8"))
        elif f == "y":
            buf.extend(struct.pack("<i", len(a)))
            for s in a:
                assert s.dtype == dtype
                buf.extend(struct.pack("<i", s.ndim))
                buf.extend(struct.pack("<%ii" % s.ndim, *s.shape))
                buf.extend(s.tobytes())
        else:
            raise UnknownFormatString("Unknown format string: %s" % f)
    return buf


def deserial(fmt, buf):
    offset = 0
    ans = []
    for f in fmt:
        if f == "i":
            a, = struct.unpack_from("<i", buf, offset)
            offset += struct.calcsize("<i")
            ans.append(a)
        elif f == "S":
            n_strings, = struct.unpack_from("<i", buf, offset)
            offset += struct.calcsize("<i")
            strings = []
            for i in range(n_strings):
                size, = struct.unpack_from("<i", buf, offset)
                offset += struct.calcsize("<i")
                value, = struct.unpack_from("%ds" % size, buf, offset)
                offset += struct.calcsize("%ds" % size)
                strings.append(value.decode("utf-8"))
            ans.append(strings)
        elif f == "y":
            n_arrays, = struct.unpack_from("<i", buf, offset)
            offset += struct.calcsize("<i")
            arrays = []
            for i in range(n_arrays):
                ndim, = struct.unpack_from("<i", buf, offset)
                offset += struct.calcsize("<i")
                shape = []
                for i in range(ndim):
                    d, = struct.unpack_from("<i", buf, offset)
                    offset += struct.calcsize("<i")
                    shape.append(d)
                array = np.ndarray(shape, dtype, buf, offset)
                arrays.append(array)
                offset += array.size
            ans.append(arrays)
        else:
            raise UnknownFormatString("Unknown format string: %s" % f)
    return ans
