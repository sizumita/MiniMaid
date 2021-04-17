#  type: ignore
"""
Code by https://github.com/20tab/mpg123-python
"""
import ctypes
from ctypes.util import find_library
import sys

from lib.errors import *

VERBOSE = 0

OK = 0
NEED_MORE = -10
NEW_FORMAT = -11
DONE = -12

MONO = 1
STEREO = 2

ENC_8 = 0x00f
ENC_16 = 0x040
ENC_24 = 0x4000
ENC_32 = 0x100
ENC_SIGNED = 0x080
ENC_FLOAT = 0xe00
ENC_SIGNED_16 = (ENC_16 | ENC_SIGNED | 0x10)
ENC_UNSIGNED_16 = (ENC_16 | 0x20)
ENC_UNSIGNED_8 = 0x01
ENC_SIGNED_8 = (ENC_SIGNED | 0x02)
ENC_ULAW_8 = 0x04
ENC_ALAW_8 = 0x08
ENC_SIGNED_32 = (ENC_32 | ENC_SIGNED | 0x1000)
ENC_UNSIGNED_32 = (ENC_32 | 0x2000)
ENC_SIGNED_24 = (ENC_24 | ENC_SIGNED | 0x1000)
ENC_UNSIGNED_24 = (ENC_24 | 0x2000)
ENC_FLOAT_32 = 0x200
ENC_FLOAT_64 = 0x400


class ID3v1(ctypes.Structure):
    _fields_ = [
        ('tag', ctypes.c_char * 3),
        ('title', ctypes.c_char * 30),
        ('artist', ctypes.c_char * 30),
        ('album', ctypes.c_char * 30),
        ('year', ctypes.c_char * 4),
        ('comment', ctypes.c_char * 30),
        ('genre', ctypes.c_ubyte),
    ]


class Mpg123:
    _lib = None

    def plain_strerror(self, errcode: int) -> str:
        self._lib.mpg123_plain_strerror.restype = ctypes.c_char_p
        return self._lib.mpg123_plain_strerror(errcode).decode()

    def init_library(self, library_path=None) -> ctypes.CDLL:
        if not library_path:
            library_path = find_library('mpg123')

        if not library_path:
            library_path = find_library('libmpg123-0')

        if not library_path:
            raise LibInitializationException('libmpg123 not found')

        lib = ctypes.CDLL(library_path)
        errcode = lib.mpg123_init()
        if errcode != OK:
            raise LibInitializationException(self.plain_strerror(errcode))
        return lib

    def __init__(self, filename: str = None, library_path: str = None) -> None:
        self.handle = None
        if not self._lib:
            self._lib = self.init_library(library_path)
        self._lib.mpg123_new.restype = ctypes.c_void_p
        self.c_handle = self._lib.mpg123_new(ctypes.c_char_p(None), None)
        self.handle = ctypes.c_void_p(self.c_handle)
        self.is_feed = filename is None
        self.offset = ctypes.c_size_t(0)
        if self.is_feed:
            errcode = self._lib.mpg123_open_feed(self.handle)
            if errcode != OK:
                raise OpenFeedException(self.plain_strerror(errcode))
        else:
            errcode = self._lib.mpg123_open(self.handle, filename.encode())
            if errcode != OK:
                raise OpenFileException(self.plain_strerror(errcode))

    def feed(self, data: str) -> None:
        if not self.is_feed:
            raise NotFeedException('instance is not in feed mode')
        # encode string to bytes in modern python
        if sys.version_info[0] >= 3 and isinstance(data, str):
            data = data.encode()
        data = memoryview(data)
        errcode = self._lib.mpg123_feed(self.handle,
                                        ctypes.c_char_p(data.tobytes()),
                                        len(data))
        if errcode != OK:
            raise FeedingException(self.plain_strerror(errcode))

    def get_format(self) -> tuple:
        rate = ctypes.c_int(0)
        channels = ctypes.c_int(0)
        encoding = ctypes.c_int(0)

        errcode = self._lib.mpg123_getformat(self.handle,
                                             ctypes.pointer(rate),
                                             ctypes.pointer(channels),
                                             ctypes.pointer(encoding))
        if errcode != OK:
            if errcode == NEED_MORE:
                raise NeedMoreException(self.plain_strerror(errcode))
            raise FormatException(self.plain_strerror(errcode))
        return rate.value, channels.value, encoding.value

    def get_width_by_encoding(self, encoding: str) -> int:
        return self._lib.mpg123_encsize(encoding)

    def length(self) -> int:
        errcode = self._lib.mpg123_length(self.handle)
        if errcode <= 0:
            if errcode == NEED_MORE:
                raise NeedMoreException(self.plain_strerror(errcode))
            raise LengthException(self.plain_strerror(errcode))
        return errcode

    def frame_length(self) -> int:
        errcode = self._lib.mpg123_framelength(self.handle)
        if errcode <= 0:
            if errcode == NEED_MORE:
                raise NeedMoreException(self.plain_strerror(errcode))
            raise LengthException(self.plain_strerror(errcode))
        return errcode

    def decode_frame(self) -> bytes:
        audio = ctypes.c_char_p()
        done = ctypes.c_size_t(0)
        errcode = self._lib.mpg123_decode_frame(self.handle,
                                                ctypes.pointer(self.offset),
                                                ctypes.pointer(audio),
                                                ctypes.pointer(done))
        if errcode == OK:
            return ctypes.string_at(audio, done.value)

        if errcode == NEED_MORE:
            raise NeedMoreException(self.plain_strerror(errcode))

        if errcode == NEW_FORMAT:
            return self.decode_frame()

        if errcode == DONE:
            raise DoneException(self.plain_strerror(errcode))

        raise DecodeException(self.plain_strerror(errcode))

    def iter_frames(self, new_format_callback: callable = None):
        self.offset = ctypes.c_size_t(0)
        audio = ctypes.c_char_p()
        done = ctypes.c_size_t(0)

        while True:
            errcode = self._lib.mpg123_decode_frame(
                self.handle,
                ctypes.pointer(self.offset),
                ctypes.pointer(audio),
                ctypes.pointer(done))
            if errcode == OK:
                yield ctypes.string_at(audio, done.value)
            else:
                if errcode in (NEED_MORE, DONE):
                    break
                if errcode == NEW_FORMAT:
                    if new_format_callback:
                        new_format_callback(*self.get_format())
                    continue
                raise DecodeException(self.plain_strerror(errcode))

    def __del__(self) -> None:
        if not self.handle:
            return
        errcode = self._lib.mpg123_close(self.handle)
        if errcode != OK:
            raise CloseException(self.plain_strerror(errcode))
