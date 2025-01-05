# apis/routes/small_talk.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..models.small_talk import (
    SmallTalk, SmallTalkCreate, SmallTalkUpdate, SmallTalkPatch
)
from utils.mysql_connector import MySQLConnector
from ..deps import get_db

router = APIRouter(prefix="/small-talk", tags=["small-talk"])


@router.get("/", response_model=List[SmallTalk])
async def get_small_talks(
        tag: Optional[str] = None,
        limit: int = Query(default=10, le=100),
        offset: int = Query(default=0, ge=0),
        db: MySQLConnector = Depends(get_db)
):
    """스몰톡 목록 조회"""
    query = """
        SELECT talk_id, eng_sentence, kor_sentence, parenthesis, tag, update_at
        FROM small_talk
        WHERE 1=1
    """
    params = {}

    if tag:
        query += " AND tag = %(tag)s"
        params['tag'] = tag

    query += " LIMIT %(limit)s OFFSET %(offset)s"
    params.update({'limit': limit, 'offset': offset})

    return db.execute_raw_query(query, params)


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
    # 삭제하기 전에 존재 여부 확인
    exists = db.execute_raw_query(
        "SELECT talk_id FROM small_talk WHERE talk_id = %(talk_id)s",
        {'talk_id': talk_id}
    )

    if not exists:
        raise HTTPException(status_code=404, detail="Small talk not found")

    # 관련된 answer 데이터도 함께 삭제 (CASCADE)
    try:
        # 트랜잭션 시작
        db.begin_transaction()

        # answer 테이블의 관련 데이터 먼저 삭제
        db.execute_raw_query(
            "DELETE FROM answer WHERE talk_id = %(talk_id)s",
            {'talk_id': talk_id}
        )

        # small_talk 테이블의 데이터 삭제
        result = db.execute_raw_query(
            "DELETE FROM small_talk WHERE talk_id = %(talk_id)s",
            {'talk_id': talk_id}
        )

        # 트랜잭션 커밋
        db.commit_transaction()

        return {"status": "success", "message": "Small talk deleted successfully"}

    except Exception as e:
        # 오류 발생 시 롤백
        db.rollback_transaction()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete small talk: {str(e)}"
        )