from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.action_analysis_record import ActionAnalysisRecord
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/action_analysis_record", tags=["action_analysis_record"])


@router.post("/")
def create_analysis_record(
    analysis_id: str,
    user_id: int,
    source_page: Optional[str] = None,
    file_name: Optional[str] = None,
    selected_player: Optional[str] = None,
    selected_stroke: Optional[str] = None,
    detected_shot_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        existing = db.query(ActionAnalysisRecord).filter(
            ActionAnalysisRecord.analysis_id == analysis_id
        ).first()
        if existing:
            return error("分析记录已存在", code=400)

        record = ActionAnalysisRecord(
            analysis_id=analysis_id,
            user_id=user_id,
            source_page=source_page,
            file_name=file_name,
            selected_player=selected_player,
            selected_stroke=selected_stroke,
            detected_shot_type=detected_shot_type,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success(message="创建成功", data={"id": record.id})
    except Exception as exc:
        db.rollback()
        logger.exception("Create analysis record failed")
        return error(f"创建失败：{exc}", code=400)


@router.get("/{analysis_id}")
def get_analysis_record(analysis_id: str, db: Session = Depends(get_db)):
    try:
        record = db.query(ActionAnalysisRecord).filter(
            ActionAnalysisRecord.analysis_id == analysis_id
        ).first()
        if not record:
            return error("记录不存在", code=404)
        return success(
            message="查询成功",
            data={
                "id": record.id,
                "analysis_id": record.analysis_id,
                "user_id": record.user_id,
                "source_page": record.source_page,
                "file_name": record.file_name,
                "selected_player": record.selected_player,
                "selected_stroke": record.selected_stroke,
                "detected_shot_type": record.detected_shot_type,
                "best_match": record.best_match,
                "grade": record.grade,
                "distance": record.distance,
                "training_duration_seconds": record.training_duration_seconds,
                "segment_count": record.segment_count,
                "score": record.score,
                "forehand_score": record.forehand_score,
                "backhand_score": record.backhand_score,
                "serve_score": record.serve_score,
                "status": record.status,
                "create_time": record.create_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    except Exception as exc:
        logger.exception("Get analysis record failed")
        return error(f"查询失败：{exc}", code=400)


@router.get("/list")
def list_analysis_records(
    user_id: int,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(ActionAnalysisRecord).filter(
            ActionAnalysisRecord.user_id == user_id
        )
        if status:
            query = query.filter(ActionAnalysisRecord.status == status)
        total = query.count()
        records = query.order_by(
            ActionAnalysisRecord.create_time.desc()
        ).offset((page - 1) * size).limit(size).all()
        return success(
            message="查询成功",
            data=[
                {
                    "id": r.id,
                    "analysis_id": r.analysis_id,
                    "file_name": r.file_name,
                    "selected_stroke": r.selected_stroke,
                    "detected_shot_type": r.detected_shot_type,
                    "grade": r.grade,
                    "score": r.score,
                    "status": r.status,
                    "create_time": r.create_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                for r in records
            ],
            total=total,
            page=page,
            size=size
        )
    except Exception as exc:
        logger.exception("List analysis records failed")
        return error(f"查询失败：{exc}", code=400)


@router.put("/{analysis_id}")
def update_analysis_record(
    analysis_id: str,
    grade: Optional[str] = None,
    distance: Optional[float] = None,
    training_duration_seconds: Optional[float] = None,
    segment_count: Optional[int] = None,
    score: Optional[float] = None,
    forehand_score: Optional[float] = None,
    backhand_score: Optional[float] = None,
    serve_score: Optional[float] = None,
    pose_video_url: Optional[str] = None,
    standard_video_url: Optional[str] = None,
    worst_phase: Optional[str] = None,
    worst_keyframe: Optional[str] = None,
    report_text: Optional[str] = None,
    coach_advice: Optional[str] = None,
    segments_json: Optional[str] = None,
    summary_json: Optional[str] = None,
    status: Optional[str] = None,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        record = db.query(ActionAnalysisRecord).filter(
            ActionAnalysisRecord.analysis_id == analysis_id
        ).first()
        if not record:
            return error("记录不存在", code=404)

        if grade is not None:
            record.grade = grade
        if distance is not None:
            record.distance = distance
        if training_duration_seconds is not None:
            record.training_duration_seconds = training_duration_seconds
        if segment_count is not None:
            record.segment_count = segment_count
        if score is not None:
            record.score = score
        if forehand_score is not None:
            record.forehand_score = forehand_score
        if backhand_score is not None:
            record.backhand_score = backhand_score
        if serve_score is not None:
            record.serve_score = serve_score
        if pose_video_url is not None:
            record.pose_video_url = pose_video_url
        if standard_video_url is not None:
            record.standard_video_url = standard_video_url
        if worst_phase is not None:
            record.worst_phase = worst_phase
        if worst_keyframe is not None:
            record.worst_keyframe = worst_keyframe
        if report_text is not None:
            record.report_text = report_text
        if coach_advice is not None:
            record.coach_advice = coach_advice
        if segments_json is not None:
            record.segments_json = segments_json
        if summary_json is not None:
            record.summary_json = summary_json
        if status is not None:
            record.status = status
        if error_message is not None:
            record.error_message = error_message

        record.update_time = datetime.now()
        db.commit()
        return success(message="更新成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Update analysis record failed")
        return error(f"更新失败：{exc}", code=400)


@router.delete("/{analysis_id}")
def delete_analysis_record(analysis_id: str, db: Session = Depends(get_db)):
    try:
        record = db.query(ActionAnalysisRecord).filter(
            ActionAnalysisRecord.analysis_id == analysis_id
        ).first()
        if not record:
            return error("记录不存在", code=404)
        db.delete(record)
        db.commit()
        return success(message="删除成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Delete analysis record failed")
        return error(f"删除失败：{exc}", code=400)