import datetime
from typing import List, Dict, Any, Optional

import srt
import torch
import whisperx

from utils.config import CONFIG
import utils


diag = utils.gen_diag("subtitles")

def map_to_srt(segments: List[Dict[str, Any]], start_index: int = 1) -> List[srt.Subtitle]:
    """
    Converts WhisperX segments into srt.Subtitle objects.

    Args:
        segments: List of dictionaries containing 'start', 'end', and 'text' keys.
        start_index: The starting index for the subtitle numbering.

    Returns:
        A list of srt.Subtitle objects.
    """
    srt_segments = []
    for index, segment in enumerate(segments, start=start_index):
        start_time = segment.get("start", 0.0)
        end_time = segment.get("end", start_time + 1.0)

        srt_segments.append(
            srt.Subtitle(
                index=index,
                start=datetime.timedelta(seconds=start_time),
                end=datetime.timedelta(seconds=end_time),
                content=segment["text"].strip()
            )
        )
    return srt_segments


def generate_subtitles(
    audio_path: str,
    output_srt_path: str,
    model_size: Optional[str] = None,
    batch_size: Optional[int] = None,
    vad_options: Optional[Dict[str, Any]] = None,
    asr_options: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Transcribes an audio file and generates an SRT subtitle file using WhisperX.

    Args:
        audio_path: Path to the audio file.
        output_srt_path: Path where the resulting .srt file should be saved.
        model_size: Size of the Whisper model to use (e.g., 'large-v2').
        batch_size: Batch size for transcription.
        vad_options: Options for Voice Activity Detection.
        asr_options: Options for Automatic Speech Recognition.

    Returns:
        True if successful, False otherwise.
    """
    config_opts = CONFIG("whisper")

    m_size = model_size or config_opts.get("model_size")
    b_size = batch_size or config_opts.get("batch_size")
    vad_opts = vad_options or config_opts.get("vad_options")
    asr_opts = asr_options or config_opts.get("asr_options")

    # TODO: other device support
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "float32"

    diag.info(f"generate_subtitles: Loading WhisperX model: {m_size} on {device}.")
    model = whisperx.load_model(
        m_size,
        device=device,
        compute_type=compute_type,
        asr_options=asr_opts,
        vad_options=vad_opts
    )

    diag.info(f"generate_subtitles: Transcribing using WhisperX: '{audio_path}'.")
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, batch_size=b_size, chunk_size=7)

    try:
        segments = result.get("segments")
        srt_segments = map_to_srt(segments)
        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write(srt.compose(srt_segments))
        print(f"generate_subtitles: Subtitles saved to {output_srt_path}")
        return True
    except Exception as e:
        diag.error(f"generate_subtitles: Failed to create SRT file: {e}")
        return False

