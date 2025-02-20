from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from apis.deps import get_db
from apis.models.opic import Opic, OpicCreate, OpicUpdate, OpicResponse, SectionType
from utils.mysql_connector import MySQLConnector

router = APIRouter(prefix="/api/v1/opic", tags=["opic"])


@router.get("/count", response_model=Dict[str, int])
async def get_opics_count(
        db: MySQLConnector = Depends(get_db)
) -> Dict[str, int]:
    """오픽 서베이 전체 개수 조회"""
    try:
        # section별 개수 및 전체 개수 조회
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN section = 'General-Topics' THEN 1 ELSE 0 END) as general_topics_count,
                SUM(CASE WHEN section = 'Role-Play' THEN 1 ELSE 0 END) as role_play_count
            FROM opic
        """
        result = db.execute_raw_query(query)[0]
        return {
            "total": result['total'],
            "general_topics_count": result['general_topics_count'],
            "role_play_count": result['role_play_count']
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"오픽 서베이 수 조회 실패: {str(e)}"
        )


@router.post("/", response_model=Opic)
async def create_opic(
        opic: OpicCreate,
        db: MySQLConnector = Depends(get_db)
):
    """오픽 서베이 생성"""
    try:
        db.begin_transaction()
        opic_data = opic.dict(exclude_unset=True)
        result = db.insert('opic', opic_data)
        opic_id = result['id']

        created = db.execute_raw_query(
            "SELECT * FROM opic WHERE opic_id = %(opic_id)s",
            {'opic_id': opic_id}
        )
        db.commit_transaction()
        return created[0]
    except Exception as e:
        db.rollback_transaction()
        raise HTTPException(
            status_code=500,
            detail=f"오픽 서베이 생성 실패: {str(e)}"
        )


@router.get("/", response_model=OpicResponse)
async def get_opics(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=10, le=100),
        section: Optional[SectionType] = Query(None, description="섹션별 필터링"),
        db: MySQLConnector = Depends(get_db)
):
    """오픽 서베이 목록 조회 (페이지네이션)"""
    try:
        # 전체 데이터 수 조회
        count_query = "SELECT COUNT(*) as total FROM opic"
        count_params = {}

        # 섹션 필터링이 있는 경우
        if section:
            count_query += " WHERE section = %(section)s"
            count_params['section'] = section.value

        total = db.execute_raw_query(count_query, count_params)[0]['total']
        total_pages = (total + size - 1) // size
        offset = (page - 1) * size

        # 데이터 조회
        query = """
            SELECT * FROM opic
        """
        params = {'limit': size, 'offset': offset}

        if section:
            query += " WHERE section = %(section)s"
            params['section'] = section.value

        query += """
            ORDER BY create_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """

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
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"오픽 서베이 목록 조회 실패: {str(e)}"
        )


@router.get("/{opic_id}", response_model=Opic)
async def get_opic(
        opic_id: int,
        db: MySQLConnector = Depends(get_db)
):
    """오픽 서베이 상세 조회"""
    result = db.execute_raw_query(
        "SELECT * FROM opic WHERE opic_id = %(opic_id)s",
        {'opic_id': opic_id}
    )
    if not result:
        raise HTTPException(status_code=404, detail="오픽 서베이를 찾을 수 없습니다")
    return result[0]


@router.put("/{opic_id}", response_model=Opic)
async def update_opic(
        opic_id: int,
        opic: OpicUpdate,
        db: MySQLConnector = Depends(get_db)
):
    """오픽 서베이 수정"""
    try:
        db.begin_transaction()

        exists = db.execute_raw_query(
            "SELECT opic_id FROM opic WHERE opic_id = %(opic_id)s",
            {'opic_id': opic_id}
        )
        if not exists:
            raise HTTPException(status_code=404, detail="오픽 서베이를 찾을 수 없습니다")

        update_data = opic.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="수정할 내용이 없습니다")

        db.update('opic', update_data, {'opic_id': opic_id})

        updated = db.execute_raw_query(
            "SELECT * FROM opic WHERE opic_id = %(opic_id)s",
            {'opic_id': opic_id}
        )

        db.commit_transaction()
        return updated[0]
    except HTTPException:
        db.rollback_transaction()
        raise
    except Exception as e:
        db.rollback_transaction()
        raise HTTPException(
            status_code=500,
            detail=f"오픽 서베이 수정 실패: {str(e)}"
        )


@router.delete("/{opic_id}")
async def delete_opic(
        opic_id: int,
        db: MySQLConnector = Depends(get_db)
):
    """오픽 서베이 삭제"""
    try:
        db.begin_transaction()

        exists = db.execute_raw_query(
            "SELECT opic_id FROM opic WHERE opic_id = %(opic_id)s",
            {'opic_id': opic_id}
        )
        if not exists:
            raise HTTPException(status_code=404, detail="오픽 서베이를 찾을 수 없습니다")

        db.execute_raw_query(
            "DELETE FROM opic WHERE opic_id = %(opic_id)s",
            {'opic_id': opic_id}
        )

        db.commit_transaction()
        return {"status": "success", "message": "오픽 서베이가 성공적으로 삭제되었습니다"}
    except HTTPException:
        db.rollback_transaction()
        raise
    except Exception as e:
        db.rollback_transaction()
        raise HTTPException(
            status_code=500,
            detail=f"오픽 서베이 삭제 실패: {str(e)}"
        )
