# apis/routes/small_talk.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict
from pydantic import BaseModel
from ..models.small_talk import (
    SmallTalk, SmallTalkCreate, SmallTalkUpdate, SmallTalkPatch
)
from utils.mysql_connector import MySQLConnector
from ..deps import get_db

router = APIRouter(prefix="/small-talk", tags=["small-talk"])

# 페이지네이션 응답을 위한 모델 추가
class PaginatedSmallTalk(BaseModel):
    items: List[SmallTalk]
    total: int
    page: int
    size: int
    total_pages: int
    has_next: bool
    has_prev: bool


@router.get("/count", response_model=Dict[str, int])
async def get_small_talks_count(
    tag: Optional[str] = None,
    db: MySQLConnector = Depends(get_db)
) -> Dict[str, int]:
    """스몰톡 전체 개수 조회"""
    try:
        query = "SELECT COUNT(*) as total FROM small_talk WHERE 1=1"
        params = {}

        if tag:
            query += " AND tag = %(tag)s"
            params['tag'] = tag

        result = db.execute_raw_query(query, params)
        return {"total": result[0]['total']}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get count: {str(e)}"
        )


@router.get("/", response_model=PaginatedSmallTalk)
async def get_small_talks(
        tag: Optional[str] = None,
        page: int = Query(default=1, ge=1),  # 페이지는 1부터 시작
        size: int = Query(default=10, le=100),
        db: MySQLConnector = Depends(get_db)
):
    """스몰톡 목록 조회 (페이지네이션)"""
    # 전체 데이터 수 조회
    count_query = "SELECT COUNT(*) as total FROM small_talk WHERE 1=1"
    count_params = {}

    if tag:
        count_query += " AND tag = %(tag)s"
        count_params['tag'] = tag

    total = db.execute_raw_query(count_query, count_params)[0]['total']

    # 페이지네이션 계산
    total_pages = (total + size - 1) // size
    offset = (page - 1) * size

    # 데이터 조회
    query = """
        SELECT talk_id, eng_sentence, kor_sentence, parenthesis, tag, create_at, update_at
        FROM small_talk
        WHERE 1=1
    """
    params = {}

    if tag:
        query += " AND tag = %(tag)s"
        params['tag'] = tag

    query += " ORDER BY talk_id DESC LIMIT %(limit)s OFFSET %(offset)s"
    params.update({'limit': size, 'offset': offset})

    items = db.execute_raw_query(query, params)

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


@router.get("/{talk_id}", response_model=SmallTalk)
async def get_small_talk(talk_id: int, db: MySQLConnector = Depends(get_db)):
    """스몰톡 상세 조회"""
    result = db.execute_raw_query(
        "SELECT * FROM small_talk WHERE talk_id = %(talk_id)s",
        {'talk_id': talk_id}
    )
    if not result:
        raise HTTPException(status_code=404, detail="Small talk not found")
    return result[0]


@router.post("/", response_model=SmallTalk)
async def create_small_talk(
        small_talk: SmallTalkCreate,
        db: MySQLConnector = Depends(get_db)
):
    """스몰톡 생성"""
    data = small_talk.dict(exclude_unset=True)
    result = db.insert('small_talk', data)

    # 생성된 데이터 조회
    created = db.execute_raw_query(
        "SELECT * FROM small_talk WHERE talk_id = %(talk_id)s",
        {'talk_id': result['id']}
    )
    return created[0]


@router.put("/{talk_id}", response_model=SmallTalk)
async def update_small_talk(
        talk_id: int,
        small_talk: SmallTalkUpdate,
        db: MySQLConnector = Depends(get_db)
):
    """스몰톡 전체 수정"""
    data = small_talk.dict(exclude_unset=True)
    result = db.update('small_talk', data, {'talk_id': talk_id})

    if result['affected_rows'] == 0:
        raise HTTPException(status_code=404, detail="Small talk not found")

    # 수정된 데이터 조회
    updated = db.execute_raw_query(
        "SELECT * FROM small_talk WHERE talk_id = %(talk_id)s",
        {'talk_id': talk_id}
    )
    return updated[0]


@router.patch("/{talk_id}", response_model=SmallTalk)
async def patch_small_talk(
        talk_id: int,
        small_talk: SmallTalkPatch,
        db: MySQLConnector = Depends(get_db)
):
    """스몰톡 부분 수정"""
    update_data = {
        k: v for k, v in small_talk.dict(exclude_unset=True).items()
        if v is not None
    }

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = db.update('small_talk', update_data, {'talk_id': talk_id})

    if result['affected_rows'] == 0:
        raise HTTPException(status_code=404, detail="Small talk not found")

    # 수정된 데이터 조회
    updated = db.execute_raw_query(
        "SELECT * FROM small_talk WHERE talk_id = %(talk_id)s",
        {'talk_id': talk_id}
    )
    return updated[0]


@router.delete("/{talk_id}")
async def delete_small_talk(
        talk_id: int,
        db: MySQLConnector = Depends(get_db)
):
    """스몰톡 삭제"""
    try:
        # 삭제하기 전에 존재 여부 확인
        exists = db.execute_raw_query(
            "SELECT talk_id FROM small_talk WHERE talk_id = %(talk_id)s",
            {'talk_id': talk_id}
        )

        if not exists:
            raise HTTPException(status_code=404, detail="Small talk not found")

        # answer 테이블의 관련 데이터 삭제
        db.execute_raw_query(
            "DELETE FROM answer WHERE talk_id = %(talk_id)s",
            {'talk_id': talk_id}
        )

        # small_talk 테이블의 데이터 삭제
        result = db.execute_raw_query(
            "DELETE FROM small_talk WHERE talk_id = %(talk_id)s",
            {'talk_id': talk_id}
        )

        return {"status": "success", "message": "Small talk deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete small talk: {str(e)}"
        )