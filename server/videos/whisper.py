import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

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


def load_model(model_size: Optional[str] = None,
               vad_options: Optional[Dict[str, Any]] = None,
               asr_options: Optional[Dict[str, Any]] = None):
    """Loads a WhisperX model using config defaults for any unspecified options."""
    config_opts = CONFIG("whisper")

    m_size = model_size or config_opts.get("model_size")
    vad_opts = vad_options or config_opts.get("vad_options")
    asr_opts = asr_options or config_opts.get("asr_options")

    # TODO: other device support
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "float32"

    diag.info(f"load_model: Loading WhisperX model: {m_size} on {device}.")
    return whisperx.load_model(
        m_size,
        device=device,
        compute_type=compute_type,
        asr_options=asr_opts,
        vad_options=vad_opts
    )


def generate_subtitles(
    audio_path: Union[str, Path],
    output_srt_path: Union[str, Path],
    model=None,
    batch_size: Optional[int] = None,
) -> None:
    """
    Transcribes an audio file and writes an SRT subtitle file using WhisperX.
    Raises on failure.

    Args:
        audio_path: Path to the audio file.
        output_srt_path: Path where the resulting .srt file should be saved.
        model: A pre-loaded whisperx model object; loaded from config if None.
        batch_size: Batch size for transcription.
    """
    b_size = batch_size or CONFIG("whisper.batch_size")

    if model is None:
        model = load_model()

    diag.info(f"generate_subtitles: Transcribing using WhisperX: '{audio_path}'.")
    audio = whisperx.load_audio(str(audio_path))
    result = model.transcribe(audio, batch_size=b_size, chunk_size=7)

    srt_segments = map_to_srt(result.get("segments") or [])
    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(srt_segments))
    diag.info(f"generate_subtitles: Subtitles saved to {output_srt_path}")

