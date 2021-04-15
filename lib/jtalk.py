from ctypes import *
import platform
from typing import Optional


class HtsVoiceFilelist(Structure):
    _fields_ = [('succ', c_void_p), ('path', c_char_p), ('name', c_char_p)]


class JTalk:
    MAX_PATH = 260

    def __init__(self,
                 voice_path: Optional[str] = None,
                 voice_dir_path: Optional[str] = None,
                 dic_path: Optional[str] = None) -> None:
        voice_path = voice_path.encode('utf-8') if voice_path is not None else None
        voice_dir_path = voice_dir_path.encode('utf-8') if voice_dir_path is not None else None
        dic_path = dic_path.encode('utf-8') if dic_path is not None else None

        self._voices = []
        self._three = platform.python_version_tuple()[0] == '3'

        if platform.system() == 'Windows':
            lib = 'jtalk'
        elif platform.system() == 'Darwin':
            lib = 'libjtalk.dylib'
        else:
            lib = 'libjtalk.so'

        self.jtalk = cdll.LoadLibrary(lib)
        self.set_argtypes()
        self.h = self.jtalk.openjtalk_initialize(voice_path, voice_dir_path, dic_path)

    def set_argtypes(self) -> None:
        self.jtalk.openjtalk_clearHTSVoiceList.argtypes = [c_void_p, POINTER(HtsVoiceFilelist)]
        self.jtalk.openjtalk_getHTSVoiceList.argtypes = [c_void_p]
        self.jtalk.openjtalk_getHTSVoiceList.restype = POINTER(HtsVoiceFilelist)
        self.jtalk.openjtalk_initialize.argtypes = [c_char_p, c_char_p, c_char_p]
        self.jtalk.openjtalk_initialize.restype = c_void_p
        self.jtalk.openjtalk_clear.argtypes = [c_void_p]
        self.jtalk.openjtalk_refresh.argtypes = [c_void_p]
        self.jtalk.openjtalk_setSamplingFrequency.argtypes = [c_void_p, c_int]
        self.jtalk.openjtalk_getSamplingFrequency.argtypes = [c_void_p]
        self.jtalk.openjtalk_getSamplingFrequency.restype = c_int
        self.jtalk.openjtalk_setFperiod.argtypes = [c_void_p, c_int]
        self.jtalk.openjtalk_getFperiod.argtypes = [c_void_p]
        self.jtalk.openjtalk_getFperiod.restype = c_int
        self.jtalk.openjtalk_setAlpha.argtypes = [c_void_p, c_double]
        self.jtalk.openjtalk_getAlpha.argtypes = [c_void_p]
        self.jtalk.openjtalk_getAlpha.restype = c_double
        self.jtalk.openjtalk_setBeta.argtypes = [c_void_p, c_double]
        self.jtalk.openjtalk_getBeta.argtypes = [c_void_p]
        self.jtalk.openjtalk_getBeta.restype = c_double
        self.jtalk.openjtalk_setSpeed.argtypes = [c_void_p, c_double]
        self.jtalk.openjtalk_getSpeed.argtypes = [c_void_p]
        self.jtalk.openjtalk_getSpeed.restype = c_double
        self.jtalk.openjtalk_setAdditionalHalfTone.argtypes = [c_void_p, c_double]
        self.jtalk.openjtalk_getAdditionalHalfTone.argtypes = [c_void_p]
        self.jtalk.openjtalk_getAdditionalHalfTone.restype = c_double
        self.jtalk.openjtalk_setMsdThreshold.argtypes = [c_void_p, c_double]
        self.jtalk.openjtalk_getMsdThreshold.argtypes = [c_void_p]
        self.jtalk.openjtalk_getMsdThreshold.restype = c_double
        self.jtalk.openjtalk_setGvWeightForSpectrum.argtypes = [c_void_p, c_double]
        self.jtalk.openjtalk_getGvWeightForSpectrum.argtypes = [c_void_p]
        self.jtalk.openjtalk_getGvWeightForSpectrum.restype = c_double
        self.jtalk.openjtalk_setGvWeightForLogF0.argtypes = [c_void_p, c_double]
        self.jtalk.openjtalk_getGvWeightForLogF0.argtypes = [c_void_p]
        self.jtalk.openjtalk_getGvWeightForLogF0.restype = c_double
        self.jtalk.openjtalk_setVolume.argtypes = [c_void_p, c_double]
        self.jtalk.openjtalk_getVolume.argtypes = [c_void_p]
        self.jtalk.openjtalk_getVolume.restype = c_double
        self.jtalk.openjtalk_setDic.argtypes = [c_void_p, c_char_p]
        self.jtalk.openjtalk_getDic.argtypes = [c_void_p, c_char_p]
        self.jtalk.openjtalk_getDic.restype = c_char_p
        self.jtalk.openjtalk_setVoiceDir.argtypes = [c_void_p, c_char_p]
        self.jtalk.openjtalk_getVoiceDir.argtypes = [c_void_p, c_char_p]
        self.jtalk.openjtalk_getVoiceDir.restype = c_char_p

        self.jtalk.openjtalk_setVoice.argtypes = [c_void_p, c_char_p]
        self.jtalk.openjtalk_getVoice.argtypes = [c_void_p, c_char_p]
        self.jtalk.openjtalk_getVoice.restype = c_char_p

        self.jtalk.openjtalk_setVoicePath.argtypes = [c_void_p, c_char_p]
        self.jtalk.openjtalk_getVoicePath.argtypes = [c_void_p, c_char_p]
        self.jtalk.openjtalk_getVoicePath.restype = c_char_p

        self.jtalk.openjtalk_setVoiceName.argtypes = [c_void_p, c_char_p]
        self.jtalk.openjtalk_getVoiceName.argtypes = [c_void_p, c_char_p]
        self.jtalk.openjtalk_getVoiceName.restype = c_char_p

        self.jtalk.openjtalk_generatePCM.argtypes = [c_void_p, c_char_p, c_void_p, c_void_p]
        self.jtalk.openjtalk_generatePCM.restype = c_bool

        self.jtalk.openjtalk_waitUntilDone.argtypes = [c_void_p]

        self.jtalk.openjtalk_wait.argtypes = [c_void_p, c_int]
        self.jtalk.openjtalk_speakToFile.argtypes = [c_void_p, c_char_p, c_char_p]
        self.jtalk.openjtalk_setVerbose.argtypes = [c_bool]
        self.jtalk.openjtalk_test.argtypes = [c_void_p, c_void_p]

    def _generate_voice_list(self) -> None:
        if len(self._voices):
            self._voices.clear()
        link = self.jtalk.openjtalk_getHTSVoiceList(self.h)
        voice_list = link[0]
        while voice_list is not None:
            self._voices.append(dict(
                path=voice_list.path.decode('utf-8'),
                name=voice_list.name.decode('utf-8')
            ))
            if voice_list.succ is None:
                break

            voice_list = cast(voice_list.succ, POINTER(HtsVoiceFilelist))
        self.jtalk.openjtalk_clearHTSVoiceList(self.h, link)

    def _check_openjtalk_object(self) -> None:
        if self.h is None:
            raise Exception("Internal Error: OpenJTalk pointer is NULL")

    def generate_pcm(self, text: str) -> Optional[list]:
        data = c_void_p()
        length = c_size_t()
        r = self.jtalk.openjtalk_generatePCM(self.h, text.encode('utf-8'), byref(data), byref(length))
        print(length)
        if not r:
            self.jtalk.openjtalk_clearData(data, length)
            return None

        pcm = cast(data, POINTER(c_short))[:length.value]
        self.jtalk.openjtalk_clearData(data, length)
        return pcm
