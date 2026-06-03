import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import SessionLocal, engine
from db_models.action_analysis import ActionAnalysisRecord

logger = logging.getLogger(__name__)
_table_ready = False


def _ensure_table() -> None:
    global _table_ready
    if _table_ready:
        return
    ActionAnalysisRecord.__table__.create(bind=engine, checkfirst=True)
    _table_ready = True


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _first_segment(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    return segments[0] if segments else {}


def _first_analysis(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    segment = _first_segment(segments)
    analysis = segment.get("analysis") or segment.get("dtw_analysis") or segment.get("result") or {}
    return analysis if isinstance(analysis, dict) else {}


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
            if record is None:
                record = ActionAnalysisRecord(analysis_id=analysis_id)
                db.add(record)

            record.user_id = int(metadata.get("user_id") or 1)
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
