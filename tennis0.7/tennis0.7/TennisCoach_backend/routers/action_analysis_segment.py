from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.action_analysis_segment import ActionAnalysisSegment
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/action_analysis_segment", tags=["action_analysis_segment"])


@router.post("/")
def create_segment(
    analysis_id: str,
    user_id: int,
    segment_index: int = 1,
    shot_type: Optional[str] = None,
    record_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    try:
        segment = ActionAnalysisSegment(
            analysis_id=analysis_id,
            user_id=user_id,
            record_id=record_id,
            segment_index=segment_index,
            shot_type=shot_type,
            create_time=datetime.now()
        )
        db.add(segment)
        db.commit()
        db.refresh(segment)
        return success(message="创建成功", data={"id": segment.id})
    except Exception as exc:
        db.rollback()
        logger.exception("Create segment failed")
        return error(f"创建失败：{exc}", code=400)


@router.get("/list")
def list_segments(
    analysis_id: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    try:
        query = db.query(ActionAnalysisSegment)
        if analysis_id:
            query = query.filter(ActionAnalysisSegment.analysis_id == analysis_id)
        if user_id:
            query = query.filter(ActionAnalysisSegment.user_id == user_id)
        segments = query.order_by(
            ActionAnalysisSegment.segment_index
        ).all()
        return success(
            message="查询成功",
            data=[
                {
                    "id": s.id,
                    "record_id": s.record_id,
                    "analysis_id": s.analysis_id,
                    "user_id": s.user_id,
                    "segment_index": s.segment_index,
                    "shot_type": s.shot_type,
                    "grade": s.grade,
                    "score": s.score,
                    "duration_seconds": s.duration_seconds,
                    "create_time": s.create_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                for s in segments
            ]
        )
    except Exception as exc:
        logger.exception("List segments failed")
        return error(f"查询失败：{exc}", code=400)


@router.get("/{segment_id}")
def get_segment(segment_id: int, db: Session = Depends(get_db)):
    try:
        segment = db.query(ActionAnalysisSegment).filter(
            ActionAnalysisSegment.id == segment_id
        ).first()
        if not segment:
            return error("片段不存在", code=404)
        return success(
            message="查询成功",
            data={
                "id": segment.id,
                "record_id": segment.record_id,
                "analysis_id": segment.analysis_id,
                "user_id": segment.user_id,
                "segment_index": segment.segment_index,
                "shot_type": segment.shot_type,
                "grade": segment.grade,
                "distance": segment.distance,
                "score": segment.score,
                "best_match": segment.best_match,
                "start_frame": segment.start_frame,
                "end_frame": segment.end_frame,
                "impact_frame": segment.impact_frame,
                "fps": segment.fps,
                "duration_seconds": segment.duration_seconds,
                "pose_video_url": segment.pose_video_url,
                "standard_video_url": segment.standard_video_url,
                "worst_phase": segment.worst_phase,
                "worst_keyframe": segment.worst_keyframe,
                "coach_advice": segment.coach_advice
            }
        )
    except Exception as exc:
        logger.exception("Get segment failed")
        return error(f"查询失败：{exc}", code=400)


@router.put("/{segment_id}")
def update_segment(
    segment_id: int,
    grade: Optional[str] = None,
    distance: Optional[float] = None,
    score: Optional[float] = None,
    best_match: Optional[str] = None,
    start_frame: Optional[int] = None,
    end_frame: Optional[int] = None,
    impact_frame: Optional[int] = None,
    fps: Optional[float] = None,
    duration_seconds: Optional[float] = None,
    pose_video_url: Optional[str] = None,
    standard_video_url: Optional[str] = None,
    worst_phase: Optional[str] = None,
    worst_keyframe: Optional[str] = None,
    phase_distances_json: Optional[str] = None,
    keyframe_distances_json: Optional[str] = None,
    top_issues_json: Optional[str] = None,
    coach_advice: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        segment = db.query(ActionAnalysisSegment).filter(
            ActionAnalysisSegment.id == segment_id
        ).first()
        if not segment:
            return error("片段不存在", code=404)

        if grade is not None:
            segment.grade = grade
        if distance is not None:
            segment.distance = distance
        if score is not None:
            segment.score = score
        if best_match is not None:
            segment.best_match = best_match
        if start_frame is not None:
            segment.start_frame = start_frame
        if end_frame is not None:
            segment.end_frame = end_frame
        if impact_frame is not None:
            segment.impact_frame = impact_frame
        if fps is not None:
            segment.fps = fps
        if duration_seconds is not None:
            segment.duration_seconds = duration_seconds
        if pose_video_url is not None:
            segment.pose_video_url = pose_video_url
        if standard_video_url is not None:
            segment.standard_video_url = standard_video_url
        if worst_phase is not None:
            segment.worst_phase = worst_phase
        if worst_keyframe is not None:
            segment.worst_keyframe = worst_keyframe
        if phase_distances_json is not None:
            segment.phase_distances_json = phase_distances_json
        if keyframe_distances_json is not None:
            segment.keyframe_distances_json = keyframe_distances_json
        if top_issues_json is not None:
            segment.top_issues_json = top_issues_json
        if coach_advice is not None:
            segment.coach_advice = coach_advice

        db.commit()
        return success(message="更新成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Update segment failed")
        return error(f"更新失败：{exc}", code=400)


@router.delete("/{segment_id}")
def delete_segment(segment_id: int, db: Session = Depends(get_db)):
    try:
        segment = db.query(ActionAnalysisSegment).filter(
            ActionAnalysisSegment.id == segment_id
        ).first()
        if not segment:
            return error("片段不存在", code=404)
        db.delete(segment)
        db.commit()
        return success(message="删除成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Delete segment failed")
        return error(f"删除失败：{exc}", code=400)