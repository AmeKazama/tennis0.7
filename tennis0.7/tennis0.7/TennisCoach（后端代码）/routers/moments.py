"""
朋友圈API路由
包含动态发布、社交互动、数据统计等接口
"""
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database import get_db
from db_models.moments import Moments, MomentLike, MomentComment, MomentShare, MomentStats
from utils.response import success_response, error_response

router = APIRouter(prefix="/api/moments", tags=["朋友圈"])


def get_current_user_id() -> int:
    """获取当前用户ID（临时实现，后续接入认证系统）"""
    return 1


# ===== 动态相关接口 =====

@router.get("/list")
async def get_moments_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    visibility: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取朋友圈动态列表"""
    query = db.query(Moments).filter(Moments.is_top == 0)
    
    if visibility:
        query = query.filter(Moments.visibility == visibility)
    
    total = query.count()
    moments = query.order_by(desc(Moments.create_time)).offset((page - 1) * page_size).limit(page_size).all()
    
    # 获取置顶动态
    top_moments = db.query(Moments).filter(Moments.is_top == 1).order_by(desc(Moments.create_time)).all()
    
    result = []
    for m in top_moments + moments:
        result.append({
            "id": m.id,
            "user_id": m.user_id,
            "content": m.content,
            "images": json.loads(m.images) if m.images else [],
            "video_url": m.video_url,
            "location": m.location,
            "likes_count": m.likes_count,
            "comments_count": m.comments_count,
            "shares_count": m.shares_count,
            "is_top": m.is_top,
            "visibility": m.visibility,
            "create_time": m.create_time.isoformat() if m.create_time else None
        })
    
    return success_response({
        "list": result,
        "total": total + len(top_moments),
        "page": page,
        "page_size": page_size
    })


@router.post("/publish")
async def publish_moment(
    content: str,
    images: Optional[str] = None,
    video_url: Optional[str] = None,
    location: Optional[str] = None,
    visibility: str = "public",
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """发布朋友圈动态"""
    if not content or len(content.strip()) == 0:
        return error_response("动态内容不能为空")
    
    moment = Moments(
        user_id=user_id,
        content=content,
        images=images,
        video_url=video_url,
        location=location,
        visibility=visibility
    )
    db.add(moment)
    
    # 更新统计数据
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    stats = db.query(MomentStats).filter(
        MomentStats.user_id == user_id,
        MomentStats.stat_date == today
    ).first()
    
    if stats:
        stats.posts_count += 1
    else:
        stats = MomentStats(user_id=user_id, stat_date=today, posts_count=1)
        db.add(stats)
    
    db.commit()
    db.refresh(moment)
    
    return success_response({
        "id": moment.id,
        "message": "发布成功"
    })


@router.delete("/{moment_id}")
async def delete_moment(
    moment_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除朋友圈动态"""
    moment = db.query(Moments).filter(Moments.id == moment_id, Moments.user_id == user_id).first()
    if not moment:
        return error_response("动态不存在或无权限删除")
    
    db.delete(moment)
    db.commit()
    
    return success_response({"message": "删除成功"})


@router.get("/{moment_id}")
async def get_moment_detail(
    moment_id: int,
    db: Session = Depends(get_db)
):
    """获取动态详情"""
    moment = db.query(Moments).filter(Moments.id == moment_id).first()
    if not moment:
        return error_response("动态不存在")
    
    return success_response({
        "id": moment.id,
        "user_id": moment.user_id,
        "content": moment.content,
        "images": json.loads(moment.images) if moment.images else [],
        "video_url": moment.video_url,
        "location": moment.location,
        "likes_count": moment.likes_count,
        "comments_count": moment.comments_count,
        "shares_count": moment.shares_count,
        "visibility": moment.visibility,
        "create_time": moment.create_time.isoformat() if moment.create_time else None
    })


# ===== 点赞相关接口 =====

@router.post("/{moment_id}/like")
async def like_moment(
    moment_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """点赞动态"""
    moment = db.query(Moments).filter(Moments.id == moment_id).first()
    if not moment:
        return error_response("动态不存在")
    
    # 检查是否已点赞
    existing_like = db.query(MomentLike).filter(
        MomentLike.moment_id == moment_id,
        MomentLike.user_id == user_id
    ).first()
    
    if existing_like:
        return error_response("已点赞过该动态")
    
    like = MomentLike(moment_id=moment_id, user_id=user_id)
    db.add(like)
    moment.likes_count += 1
    
    # 更新统计数据
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    owner_stats = db.query(MomentStats).filter(
        MomentStats.user_id == moment.user_id,
        MomentStats.stat_date == today
    ).first()
    if owner_stats:
        owner_stats.likes_received += 1
    else:
        owner_stats = MomentStats(user_id=moment.user_id, stat_date=today, likes_received=1)
        db.add(owner_stats)
    
    user_stats = db.query(MomentStats).filter(
        MomentStats.user_id == user_id,
        MomentStats.stat_date == today
    ).first()
    if user_stats:
        user_stats.likes_given += 1
    else:
        user_stats = MomentStats(user_id=user_id, stat_date=today, likes_given=1)
        db.add(user_stats)
    
    db.commit()
    
    return success_response({"likes_count": moment.likes_count})


@router.delete("/{moment_id}/like")
async def unlike_moment(
    moment_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """取消点赞"""
    like = db.query(MomentLike).filter(
        MomentLike.moment_id == moment_id,
        MomentLike.user_id == user_id
    ).first()
    
    if not like:
        return error_response("未点赞过该动态")
    
    moment = db.query(Moments).filter(Moments.id == moment_id).first()
    if moment:
        moment.likes_count = max(0, moment.likes_count - 1)
    
    db.delete(like)
    db.commit()
    
    return success_response({"likes_count": moment.likes_count if moment else 0})


@router.get("/{moment_id}/likes")
async def get_moment_likes(
    moment_id: int,
    db: Session = Depends(get_db)
):
    """获取动态点赞列表"""
    likes = db.query(MomentLike).filter(MomentLike.moment_id == moment_id).order_by(desc(MomentLike.create_time)).all()
    
    return success_response({
        "list": [
            {
                "id": like.id,
                "user_id": like.user_id,
                "create_time": like.create_time.isoformat() if like.create_time else None
            }
            for like in likes
        ],
        "total": len(likes)
    })


# ===== 评论相关接口 =====

@router.post("/{moment_id}/comment")
async def comment_moment(
    moment_id: int,
    content: str,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """评论动态"""
    if not content or len(content.strip()) == 0:
        return error_response("评论内容不能为空")
    
    moment = db.query(Moments).filter(Moments.id == moment_id).first()
    if not moment:
        return error_response("动态不存在")
    
    comment = MomentComment(
        moment_id=moment_id,
        user_id=user_id,
        parent_id=parent_id,
        content=content
    )
    db.add(comment)
    moment.comments_count += 1
    
    # 更新统计数据
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    owner_stats = db.query(MomentStats).filter(
        MomentStats.user_id == moment.user_id,
        MomentStats.stat_date == today
    ).first()
    if owner_stats:
        owner_stats.comments_received += 1
    else:
        owner_stats = MomentStats(user_id=moment.user_id, stat_date=today, comments_received=1)
        db.add(owner_stats)
    
    user_stats = db.query(MomentStats).filter(
        MomentStats.user_id == user_id,
        MomentStats.stat_date == today
    ).first()
    if user_stats:
        user_stats.comments_given += 1
    else:
        user_stats = MomentStats(user_id=user_id, stat_date=today, comments_given=1)
        db.add(user_stats)
    
    db.commit()
    db.refresh(comment)
    
    return success_response({
        "id": comment.id,
        "comments_count": moment.comments_count
    })


@router.get("/{moment_id}/comments")
async def get_moment_comments(
    moment_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取动态评论列表"""
    query = db.query(MomentComment).filter(
        MomentComment.moment_id == moment_id,
        MomentComment.parent_id.is_(None)
    )
    
    total = query.count()
    comments = query.order_by(desc(MomentComment.create_time)).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for c in comments:
        # 获取回复
        replies = db.query(MomentComment).filter(
            MomentComment.parent_id == c.id
        ).order_by(MomentComment.create_time).all()
        
        result.append({
            "id": c.id,
            "user_id": c.user_id,
            "content": c.content,
            "likes_count": c.likes_count,
            "parent_id": c.parent_id,
            "create_time": c.create_time.isoformat() if c.create_time else None,
            "replies": [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "content": r.content,
                    "likes_count": r.likes_count,
                    "parent_id": r.parent_id,
                    "create_time": r.create_time.isoformat() if r.create_time else None
                }
                for r in replies
            ]
        })
    
    return success_response({
        "list": result,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.delete("/comment/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除评论"""
    comment = db.query(MomentComment).filter(
        MomentComment.id == comment_id,
        MomentComment.user_id == user_id
    ).first()
    
    if not comment:
        return error_response("评论不存在或无权限删除")
    
    moment = db.query(Moments).filter(Moments.id == comment.moment_id).first()
    if moment:
        moment.comments_count = max(0, moment.comments_count - 1)
    
    db.delete(comment)
    db.commit()
    
    return success_response({"message": "删除成功"})


# ===== 分享相关接口 =====

@router.post("/{moment_id}/share")
async def share_moment(
    moment_id: int,
    share_type: str = "internal",
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """分享动态"""
    moment = db.query(Moments).filter(Moments.id == moment_id).first()
    if not moment:
        return error_response("动态不存在")
    
    share = MomentShare(
        moment_id=moment_id,
        user_id=user_id,
        share_type=share_type
    )
    db.add(share)
    moment.shares_count += 1
    
    # 更新统计数据
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    owner_stats = db.query(MomentStats).filter(
        MomentStats.user_id == moment.user_id,
        MomentStats.stat_date == today
    ).first()
    if owner_stats:
        owner_stats.shares_received += 1
    else:
        owner_stats = MomentStats(user_id=moment.user_id, stat_date=today, shares_received=1)
        db.add(owner_stats)
    
    db.commit()
    
    return success_response({"shares_count": moment.shares_count})


# ===== 数据统计接口 =====

@router.get("/stats/summary")
async def get_stats_summary(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """获取朋友圈数据统计摘要"""
    # 获取最近30天的统计数据
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    stats = db.query(MomentStats).filter(
        MomentStats.user_id == user_id,
        MomentStats.stat_date >= today
    ).order_by(desc(MomentStats.stat_date)).all()
    
    total_posts = sum(s.posts_count for s in stats)
    total_likes_received = sum(s.likes_received for s in stats)
    total_comments_received = sum(s.comments_received for s in stats)
    total_shares_received = sum(s.shares_received for s in stats)
    
    return success_response({
        "total_posts": total_posts,
        "total_likes_received": total_likes_received,
        "total_comments_received": total_comments_received,
        "total_shares_received": total_shares_received,
        "daily_stats": [
            {
                "date": s.stat_date.isoformat() if s.stat_date else None,
                "posts_count": s.posts_count,
                "likes_received": s.likes_received,
                "comments_received": s.comments_received,
                "shares_received": s.shares_received,
                "likes_given": s.likes_given,
                "comments_given": s.comments_given
            }
            for s in stats
        ]
    })


@router.get("/stats/trend")
async def get_stats_trend(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """获取朋友圈数据趋势"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today
    
    stats = db.query(MomentStats).filter(
        MomentStats.user_id == user_id,
        MomentStats.stat_date >= start_date
    ).order_by(MomentStats.stat_date).all()
    
    return success_response({
        "trend": [
            {
                "date": s.stat_date.isoformat() if s.stat_date else None,
                "posts_count": s.posts_count,
                "likes_received": s.likes_received,
                "comments_received": s.comments_received,
                "shares_received": s.shares_received
            }
            for s in stats
        ]
    })


@router.get("/stats/overview")
async def get_stats_overview(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """获取朋友圈数据总览"""
    # 获取总发布数
    total_posts = db.query(func.count(Moments.id)).filter(Moments.user_id == user_id).scalar() or 0
    
    # 获取总点赞数
    total_likes = db.query(func.count(MomentLike.id)).filter(
        MomentLike.moment_id.in_(
            db.query(Moments.id).filter(Moments.user_id == user_id)
        )
    ).scalar() or 0
    
    # 获取总评论数
    total_comments = db.query(func.count(MomentComment.id)).filter(
        MomentComment.moment_id.in_(
            db.query(Moments.id).filter(Moments.user_id == user_id)
        )
    ).scalar() or 0
    
    # 获取总分享数
    total_shares = db.query(func.count(MomentShare.id)).filter(
        MomentShare.moment_id.in_(
            db.query(Moments.id).filter(Moments.user_id == user_id)
        )
    ).scalar() or 0
    
    return success_response({
        "total_posts": total_posts,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_shares": total_shares
    })
