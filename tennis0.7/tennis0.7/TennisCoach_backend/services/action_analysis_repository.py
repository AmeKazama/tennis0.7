import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import SessionLocal, engine
from db_models.action_analysis import ActionAnalysisRecord
from db_models.user_profile import UserProfile
from db_models.user_training_stats import UserTrainingStats

logger = logging.getLogger(__name__)
_table_ready = False


SHOT_ALIASES = {
    "forehand": "forehand",
    "正手": "forehand",
    "正手击球": "forehand",
    "backhand": "backhand",
    "反手": "backhand",
    "反手击球": "backhand",
    "serve": "serve",
    "server": "serve",
    "发球": "serve",
}
GRADE_SCORE = {
    "优秀": 90.0,
    "良好": 80.0,
    "一般": 65.0,
    "较差": 50.0,
}


def _ensure_table() -> None:
    global _table_ready
    if _table_ready:
        return
    ActionAnalysisRecord.__table__.create(bind=engine, checkfirst=True)
    UserTrainingStats.__table__.create(bind=engine, checkfirst=True)
    UserProfile.__table__.create(bind=engine, checkfirst=True)
    _table_ready = True


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _first_segment(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    return segments[0] if segments else {}


def _first_analysis(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    segment = _first_segment(segments)
    analysis = segment.get("analysis") or segment.get("dtw_analysis") or segment.get("result") or {}
    return analysis if isinstance(analysis, dict) else {}


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _score_from_distance(distance: Any, grade: Any = None) -> Optional[float]:
    numeric_distance = _to_float(distance)
    if numeric_distance is not None:
        return max(0.0, min(100.0, 100.0 - numeric_distance * 1.5))
    if grade in GRADE_SCORE:
        return GRADE_SCORE[grade]
    return None


def _normalize_shot_type(value: Any) -> Optional[str]:
    if value is None:
        return None
    key = str(value).strip().lower()
    return SHOT_ALIASES.get(key) or SHOT_ALIASES.get(str(value).strip())


def _get_segment_analysis(segment: Dict[str, Any]) -> Dict[str, Any]:
    analysis = segment.get("analysis") or segment.get("dtw_analysis") or segment.get("result") or {}
    return analysis if isinstance(analysis, dict) else {}


def _segment_score(segment: Dict[str, Any]) -> Optional[float]:
    analysis = _get_segment_analysis(segment)
    distance = (
        analysis.get("distance")
        or analysis.get("dtw_distance")
        or analysis.get("phase_dtw_distance")
        or segment.get("distance")
        or segment.get("dtw_distance")
    )
    grade = analysis.get("grade") or segment.get("grade")
    return _score_from_distance(distance, grade)


def _segment_duration(segment: Dict[str, Any]) -> float:
    time_range = segment.get("time_range")
    if isinstance(time_range, list) and len(time_range) >= 2:
        start = _to_float(time_range[0]) or 0.0
        end = _to_float(time_range[1]) or 0.0
        return max(0.0, end - start)

    frame_range = segment.get("frame_range") or segment.get("segment_range")
    fps = _to_float(segment.get("fps"))
    if isinstance(frame_range, list) and len(frame_range) >= 2 and fps and fps > 0:
        start = _to_float(frame_range[0]) or 0.0
        end = _to_float(frame_range[1]) or 0.0
        return max(0.0, (end - start) / fps)
    return 0.0


def _summary_duration(summary: Optional[Dict[str, Any]], segments: List[Dict[str, Any]]) -> float:
    summary = summary or {}
    for key in ("duration", "duration_seconds", "video_duration", "total_duration_seconds"):
        duration = _to_float(summary.get(key))
        if duration is not None and duration > 0:
            return duration

    num_frames = _to_float(summary.get("num_frames") or summary.get("total_frames"))
    fps = _to_float(summary.get("fps"))
    if num_frames and fps and fps > 0:
        return num_frames / fps

    return sum(_segment_duration(segment) for segment in segments)


def _average(values: List[float]) -> Optional[float]:
    values = [value for value in values if value is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _weighted_average(old_avg: float, old_count: int, new_avg: Optional[float], new_count: int) -> float:
    if not new_avg or new_count <= 0:
        return float(old_avg or 0)
    old_count = int(old_count or 0)
    if old_count <= 0:
        return float(new_avg)
    return ((float(old_avg or 0) * old_count) + (float(new_avg) * new_count)) / (old_count + new_count)


def _build_training_delta(segments: List[Dict[str, Any]], summary: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    scores_by_type = {"forehand": [], "backhand": [], "serve": []}
    all_scores = []

    for segment in segments:
        shot_type = _normalize_shot_type(segment.get("shot_type") or segment.get("shot_type_cn"))
        score = _segment_score(segment)
        if score is not None:
            all_scores.append(score)
        if shot_type in scores_by_type:
            if score is not None:
                scores_by_type[shot_type].append(score)
            else:
                scores_by_type[shot_type].append(0.0)

    return {
        "duration": _summary_duration(summary, segments),
        "score": _average(all_scores),
        "forehand_count": len(scores_by_type["forehand"]),
        "backhand_count": len(scores_by_type["backhand"]),
        "serve_count": len(scores_by_type["serve"]),
        "forehand_avg_score": _average(scores_by_type["forehand"]),
        "backhand_avg_score": _average(scores_by_type["backhand"]),
        "serve_avg_score": _average(scores_by_type["serve"]),
    }


def _apply_training_stats(db, user_id: int, segments: List[Dict[str, Any]], summary: Optional[Dict[str, Any]]) -> None:
    if not segments:
        return

    delta = _build_training_delta(segments, summary)
    current_score = delta.get("score")

    stats = db.query(UserTrainingStats).filter(UserTrainingStats.user_id == user_id).first()
    if stats is None:
        stats = UserTrainingStats(user_id=user_id)
        db.add(stats)
        db.flush()

    old_training_count = int(stats.training_count or 0)
    stats.training_count = old_training_count + 1
    stats.total_duration_seconds = float(stats.total_duration_seconds or 0) + float(delta.get("duration") or 0)
    if current_score is not None:
        stats.avg_score = _weighted_average(stats.avg_score or 0, old_training_count, current_score, 1)
        stats.best_score = max(float(stats.best_score or 0), float(current_score))

    old_forehand_count = int(stats.forehand_count or 0)
    old_backhand_count = int(stats.backhand_count or 0)
    old_serve_count = int(stats.serve_count or 0)

    forehand_count = int(delta.get("forehand_count") or 0)
    backhand_count = int(delta.get("backhand_count") or 0)
    serve_count = int(delta.get("serve_count") or 0)

    stats.forehand_avg_score = _weighted_average(
        stats.forehand_avg_score or 0,
        old_forehand_count,
        delta.get("forehand_avg_score"),
        forehand_count,
    )
    stats.backhand_avg_score = _weighted_average(
        stats.backhand_avg_score or 0,
        old_backhand_count,
        delta.get("backhand_avg_score"),
        backhand_count,
    )
    stats.serve_avg_score = _weighted_average(
        stats.serve_avg_score or 0,
        old_serve_count,
        delta.get("serve_avg_score"),
        serve_count,
    )

    stats.forehand_count = old_forehand_count + forehand_count
    stats.backhand_count = old_backhand_count + backhand_count
    stats.serve_count = old_serve_count + serve_count
    stats.last_training_time = datetime.now()
    stats.update_time = datetime.now()

    profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if profile is None:
        profile = UserProfile(id=user_id)
        db.add(profile)
        db.flush()

    profile.analysis_count = int(profile.analysis_count or 0) + 1
    profile.training_video_count = int(profile.training_video_count or 0) + 1
    profile.update_time = datetime.now()


def _build_report_text(segments: List[Dict[str, Any]], summary: Optional[Dict[str, Any]]) -> str:
    lines = []
    if summary:
        lines.append(
            "Summary: segments={segments}, fps={fps}, duration={duration}".format(
                segments=summary.get("num_segments", len(segments)),
                fps=summary.get("fps", ""),
                duration=summary.get("duration", ""),
            )
        )

    for index, segment in enumerate(segments, start=1):
        analysis = segment.get("analysis") or {}
        shot_type = segment.get("shot_type") or segment.get("shot_type_cn") or "unknown"
        grade = analysis.get("grade") or segment.get("grade") or ""
        distance = analysis.get("distance") or segment.get("distance") or ""
        advice = segment.get("coach_advice") or ""
        lines.append(f"Segment {index}: {shot_type}, grade={grade}, distance={distance}")
        if advice:
            lines.append(f"Advice: {advice}")

    return "\n".join(lines)


def save_action_analysis_record(
    metadata: Optional[Dict[str, Any]],
    segments: List[Dict[str, Any]],
    summary: Optional[Dict[str, Any]],
    status: str = "success",
    error_message: Optional[str] = None,
) -> Optional[int]:
    metadata = metadata or {}
    segments = segments or []
    analysis = _first_analysis(segments)
    first = _first_segment(segments)

    analysis_id = metadata.get("analysis_id")
    if not analysis_id:
        logger.warning("Skip action analysis persistence: missing analysis_id")
        return None

    try:
        _ensure_table()
        db = SessionLocal()
        try:
            record = db.query(ActionAnalysisRecord).filter(
                ActionAnalysisRecord.analysis_id == analysis_id
            ).first()
            is_new_record = record is None
            if record is None:
                record = ActionAnalysisRecord(analysis_id=analysis_id)
                db.add(record)

            user_id = int(metadata.get("user_id") or 1)
            record.user_id = user_id
            record.source_page = metadata.get("source_page") or metadata.get("source") or "action_comparison"
            record.file_name = metadata.get("file_name")
            record.selected_player = metadata.get("selected_player")
            record.selected_stroke = metadata.get("selected_stroke")
            record.detected_shot_type = first.get("shot_type") or first.get("shot_type_cn")
            record.best_match = (
                analysis.get("best_match")
                or analysis.get("standard")
                or analysis.get("matched_standard")
                or first.get("best_match")
            )
            record.grade = analysis.get("grade") or first.get("grade")
            distance = analysis.get("distance") or analysis.get("dtw_distance") or first.get("distance")
            record.distance = float(distance) if distance is not None and distance != "" else None
            record.coach_advice = "\n".join(
                [str(segment.get("coach_advice")) for segment in segments if segment.get("coach_advice")]
            ) or None
            record.report_text = _build_report_text(segments, summary)
            record.segments_json = _json_dumps(segments)
            record.summary_json = _json_dumps(summary or {})
            record.status = status
            record.error_message = error_message
            record.update_time = datetime.now()

            if is_new_record and status == "success" and segments:
                _apply_training_stats(db, user_id, segments, summary)

            db.commit()
            db.refresh(record)
            logger.info("Saved action analysis record: id=%s, analysis_id=%s", record.id, analysis_id)
            return record.id
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Save action analysis record failed: %s", exc)
        return None
