import logging
import os
import wave

logger = logging.getLogger(__name__)

PLACEHOLDER_PREFIXES = ("填写你的", "你的")


class SpeechRecognitionError(Exception):
    pass


class SpeechRecognitionService:
    def recognize(self, audio_path: str) -> str:
        raise NotImplementedError


class BaiduSpeechRecognitionService(SpeechRecognitionService):
    def __init__(self):
        self.app_id = os.getenv("BAIDU_SPEECH_APP_ID", "").strip()
        self.api_key = os.getenv("BAIDU_SPEECH_API_KEY", "").strip()
        self.secret_key = os.getenv("BAIDU_SPEECH_SECRET_KEY", "").strip()
        self.client = None
        self.client_init_error = None

        if not self._is_configured():
            logger.warning("Baidu speech recognition configuration is incomplete")
            return

        try:
            from aip import AipSpeech

            self.client = AipSpeech(self.app_id, self.api_key, self.secret_key)
        except Exception as exc:
            self.client_init_error = exc
            logger.exception("Initialize Baidu speech recognition client failed")

    def recognize(self, audio_path: str) -> str:
        if not os.path.exists(audio_path):
            logger.error("Audio file does not exist: %s", audio_path)
            raise SpeechRecognitionError("音频文件不存在")

        if not self._is_configured():
            raise SpeechRecognitionError("百度语音识别配置未完成")

        if self.client is None:
            detail = str(self.client_init_error) if self.client_init_error else "客户端未初始化"
            raise SpeechRecognitionError(f"百度语音识别客户端初始化失败：{detail}")

        file_size = os.path.getsize(audio_path)
        audio_params = {
            "file_size": file_size,
        }
        baidu_format = None
        actual_sample_rate = 16000

        logger.info("Audio file before Baidu ASR, audioPath=%s, fileSize=%s", audio_path, file_size)

        try:
            with open(audio_path, "rb") as audio_file:
                speech_data = audio_file.read()

            if not speech_data:
                raise SpeechRecognitionError("音频文件为空")

            if speech_data.startswith(b"RIFF"):
                detected_format = "wav"
                baidu_format = "wav"
                try:
                    with wave.open(audio_path, "rb") as wav_file:
                        channels = wav_file.getnchannels()
                        framerate = wav_file.getframerate()
                        sampwidth = wav_file.getsampwidth()
                        frames = wav_file.getnframes()
                        duration = frames / framerate if framerate else 0
                except wave.Error as exc:
                    logger.exception("Read WAV metadata failed, audioPath=%s, fileSize=%s", audio_path, file_size)
                    raise SpeechRecognitionError(f"语音识别失败：WAV 音频格式异常：{exc}") from exc

                audio_params.update(
                    {
                        "channels": channels,
                        "framerate": framerate,
                        "sampwidth": sampwidth,
                        "frames": frames,
                        "duration": duration,
                    }
                )
                actual_sample_rate = framerate
                logger.info("WAV audio params before Baidu ASR, audioPath=%s, audioParams=%r", audio_path, audio_params)

                if duration < 1.5:
                    raise SpeechRecognitionError("语音识别失败：录音时间太短")
            elif speech_data.startswith(b"#!AMR-WB"):
                detected_format = "amr-wb"
                baidu_format = "amr"
                audio_params["detected_format"] = detected_format
                logger.info("Detected AMR-WB audio, audioPath=%s, fileSize=%s", audio_path, file_size)
            elif speech_data.startswith(b"#!AMR"):
                detected_format = "amr"
                baidu_format = "amr"
                audio_params["detected_format"] = detected_format
            else:
                logger.error("Unsupported audio format, audioPath=%s, fileSize=%s, header=%r", audio_path, file_size, speech_data[:16])
                raise SpeechRecognitionError("语音识别失败：不支持的音频格式")

            audio_params["detected_format"] = detected_format
            logger.info(
                "Detected audio format before Baidu ASR, audioPath=%s, fileSize=%s, detectedFormat=%s, baiduFormat=%s",
                audio_path,
                file_size,
                detected_format,
                baidu_format,
            )

            result = self.client.asr(
                speech_data,
                baidu_format,
                actual_sample_rate,
                {
                    "dev_pid": 1537,
                },
            )
            logger.info(
                "Baidu speech recognition raw response, audioPath=%s, detectedFormat=%s, baiduFormat=%s, response=%r",
                audio_path,
                detected_format,
                baidu_format,
                result,
            )
        except SpeechRecognitionError:
            raise
        except Exception as exc:
            logger.exception("Call Baidu speech recognition SDK failed, audioPath=%s", audio_path)
            raise SpeechRecognitionError(f"百度语音识别调用失败：{exc}") from exc

        if not isinstance(result, dict):
            logger.error("Unexpected Baidu speech recognition response: %r", result)
            raise SpeechRecognitionError("百度语音识别返回格式异常")

        err_no = result.get("err_no")
        if err_no != 0:
            err_msg = result.get("err_msg", "未知错误")
            logger.error(
                "Baidu speech recognition failed, errNo=%s, errMsg=%s, response=%r",
                err_no,
                err_msg,
                result,
            )
            raise SpeechRecognitionError(f"语音识别失败：错误码 {err_no}，错误信息 {err_msg}")

        text = "".join(result.get("result") or []).strip()
        if not text:
            logger.error(
                "Baidu speech recognition returned empty text, detectedFormat=%s, baiduFormat=%s, audioParams=%r, response=%r",
                detected_format,
                baidu_format,
                audio_params,
                result,
            )
            raise SpeechRecognitionError("语音识别失败：未识别到文字")

        logger.info("Baidu speech recognition succeeded, audioPath=%s", audio_path)
        return text

    def _is_configured(self) -> bool:
        return all(
            value and not value.startswith(PLACEHOLDER_PREFIXES)
            for value in (self.app_id, self.api_key, self.secret_key)
        )
