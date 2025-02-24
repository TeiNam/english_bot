# apis/routes/small_talk.py
from enum import Enum
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from utils.auth import get_current_user
from utils.mysql_connector import MySQLConnector
from ..deps import get_db
from ..models.small_talk import (
    SmallTalk, SmallTalkCreate, SmallTalkUpdate, SmallTalkPatch
)

router = APIRouter(prefix="/api/v1/small-talk", tags=["small-talk"])


class PaginatedSmallTalk(BaseModel):
    items: List[SmallTalk]
    total: int
    page: int
    size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class Direction(str, Enum):
    CURRENT = "current"
    PREV = "prev"
    NEXT = "next"


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
        page: int = Query(default=1, ge=1),
        size: int = Query(default=10, le=100),
        db: MySQLConnector = Depends(get_db)
):
    """스몰톡 목록 조회 (페이지네이션)"""
    count_query = "SELECT COUNT(*) as total FROM small_talk WHERE 1=1"
    count_params = {}

    if tag:
        count_query += " AND tag = %(tag)s"
        count_params['tag'] = tag

    total = db.execute_raw_query(count_query, count_params)[0]['total']

    total_pages = (total + size - 1) // size
    offset = (page - 1) * size

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


@router.get("/search", response_model=PaginatedSmallTalk)
async def search_small_talks(
        query: Optional[str] = None,
        page: int = 1,
        size: int = 10,
        db: MySQLConnector = Depends(get_db)
):
    """스몰톡 풀텍스트 검색 (페이지네이션)"""
    try:
        # 검색어 유효성 검사
        if not query or len(query.strip()) == 0:
            return {
                "items": [],
                "total": 0,
                "page": page,
                "size": size,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }

        # 페이지 및 사이즈 유효성 검사
        page = max(1, page)
        size = min(max(1, size), 100)

        # 검색 방식 결정: 2글자 이상이면 풀텍스트 검색, 그렇지 않으면 LIKE 검색
        use_fulltext = len(query.strip()) >= 2

        if use_fulltext:
            try:
                # 풀텍스트 검색 쿼리
                count_query = """
                    SELECT COUNT(*) as total 
                    FROM small_talk 
                    WHERE MATCH(eng_sentence, kor_sentence, parenthesis, tag) 
                    AGAINST (%(query)s IN BOOLEAN MODE)
                """
                count_params = {'query': f"{query}*"}

                total_result = db.execute_raw_query(count_query, count_params)
                total = total_result[0]['total'] if total_result else 0

                # 결과가 있으면 풀텍스트 검색 쿼리 준비
                if total > 0:
                    search_query = """
                        SELECT talk_id, eng_sentence, kor_sentence, parenthesis, tag, create_at, update_at,
                               MATCH(eng_sentence, kor_sentence, parenthesis, tag) 
                               AGAINST (%(query)s IN BOOLEAN MODE) as relevance
                        FROM small_talk
                        WHERE MATCH(eng_sentence, kor_sentence, parenthesis, tag) 
                        AGAINST (%(query)s IN BOOLEAN MODE)
                        ORDER BY relevance DESC, talk_id DESC
                        LIMIT %(limit)s OFFSET %(offset)s
                    """
                    search_params = {
                        'query': f"{query}*",
                        'limit': size,
                        'offset': (page - 1) * size
                    }
                else:
                    # 풀텍스트 검색 결과가 없으면 LIKE 검색으로 전환
                    raise Exception("No results from fulltext search")
            except Exception as e:
                # 풀텍스트 검색 실패 시 LIKE 검색으로 전환
                use_fulltext = False

        # LIKE 검색 사용 (풀텍스트 검색 실패 또는 검색어가 짧을 경우)
        if not use_fulltext:
            search_term = f"%{query}%"

            count_query = """
                SELECT COUNT(*) as total 
                FROM small_talk 
                WHERE eng_sentence LIKE %(search)s 
                   OR kor_sentence LIKE %(search)s 
                   OR parenthesis LIKE %(search)s 
                   OR tag LIKE %(search)s
            """
            count_params = {'search': search_term}

            total_result = db.execute_raw_query(count_query, count_params)
            total = total_result[0]['total'] if total_result else 0

            search_query = """
                SELECT talk_id, eng_sentence, kor_sentence, parenthesis, tag, create_at, update_at
                FROM small_talk
                WHERE eng_sentence LIKE %(search)s 
                   OR kor_sentence LIKE %(search)s 
                   OR parenthesis LIKE %(search)s 
                   OR tag LIKE %(search)s
                ORDER BY talk_id DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """
            search_params = {
                'search': search_term,
                'limit': size,
                'offset': (page - 1) * size
            }

        # 검색 결과가 없으면 빈 결과 반환
        if total == 0:
            return {
                "items": [],
                "total": 0,
                "page": page,
                "size": size,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }

        # 페이지네이션 계산
        total_pages = (total + size - 1) // size

        # 결과 조회
        items = db.execute_raw_query(search_query, search_params)

        # relevance 필드 제거 (반환 구조를 일관되게 유지하기 위해)
        if use_fulltext:
            for item in items:
                if 'relevance' in item:
                    del item['relevance']

        # 결과 반환
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
        # 오류 로깅
        import traceback
        print(f"Search error: {str(e)}")
        print(traceback.format_exc())

        # 클라이언트에 오류 반환
        raise HTTPException(
            status_code=500,
            detail=f"검색 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/sentence")
async def get_sentence(
        current_user=Depends(get_current_user),
        direction: Direction = Direction.CURRENT,
        current_talk_id: Optional[int] = None,
        db: MySQLConnector = Depends(get_db)
):
    """사용자별 스몰톡 문장 조회 (현재/이전/다음)"""
    try:
        user_id = current_user.user_id

        if direction == Direction.CURRENT:
            query = """
                SELECT s.talk_id, s.eng_sentence, s.kor_sentence, s.parenthesis, s.tag,
                    (SELECT talk_id FROM small_talk WHERE talk_id < s.talk_id ORDER BY talk_id DESC LIMIT 1) as prev_id,
                    COALESCE(
                        (SELECT talk_id FROM small_talk WHERE talk_id > s.talk_id ORDER BY talk_id ASC LIMIT 1),
                        1
                    ) as next_id
                FROM small_talk s
                WHERE s.talk_id = COALESCE(
                    (SELECT talk_id FROM last_sentence WHERE user_id = %(user_id)s),
                    (SELECT MIN(talk_id) FROM small_talk)
                )
                LIMIT 1
            """
            params = {'user_id': user_id}
        else:
            if not current_talk_id:
                raise HTTPException(
                    status_code=400,
                    detail="current_talk_id is required for prev/next navigation"
                )

            if direction == Direction.NEXT:
                query = """
                    SELECT s.talk_id, s.eng_sentence, s.kor_sentence, s.parenthesis, s.tag,
                        (SELECT talk_id FROM small_talk WHERE talk_id < s.talk_id ORDER BY talk_id DESC LIMIT 1) as prev_id,
                        COALESCE(
                            (SELECT talk_id FROM small_talk WHERE talk_id > s.talk_id ORDER BY talk_id ASC LIMIT 1),
                            1
                        ) as next_id
                    FROM small_talk s
                    WHERE s.talk_id = CASE
                        WHEN EXISTS (SELECT 1 FROM small_talk WHERE talk_id > %(current_talk_id)s)
                        THEN (SELECT MIN(talk_id) FROM small_talk WHERE talk_id > %(current_talk_id)s)
                        ELSE 1
                    END
                """
            else:
                query = """
                    SELECT s.talk_id, s.eng_sentence, s.kor_sentence, s.parenthesis, s.tag,
                        (SELECT talk_id FROM small_talk WHERE talk_id < s.talk_id ORDER BY talk_id DESC LIMIT 1) as prev_id,
                        COALESCE(
                            (SELECT talk_id FROM small_talk WHERE talk_id > s.talk_id ORDER BY talk_id ASC LIMIT 1),
                            1
                        ) as next_id
                    FROM small_talk s
                    WHERE s.talk_id = (
                        SELECT MAX(talk_id) 
                        FROM small_talk 
                        WHERE talk_id < %(current_talk_id)s
                    )
                """
            params = {'current_talk_id': current_talk_id}

        result = db.execute_raw_query(query, params)

        if not result:
            # 데이터가 없는 경우 첫 번째 문장 가져오기
            query = """
                SELECT s.talk_id, s.eng_sentence, s.kor_sentence, s.parenthesis, s.tag,
                    NULL as prev_id,
                    COALESCE(
                        (SELECT talk_id FROM small_talk WHERE talk_id > s.talk_id ORDER BY talk_id ASC LIMIT 1),
                        1
                    ) as next_id
                FROM small_talk s
                ORDER BY s.talk_id ASC
                LIMIT 1
            """
            result = db.execute_raw_query(query)

            if not result:
                raise HTTPException(
                    status_code=404,
                    detail="No sentences found in the database"
                )

        # 히스토리 업데이트
        upsert_query = """
            INSERT INTO last_sentence 
                (user_id, talk_id)
            VALUES 
                (%(user_id)s, %(talk_id)s)
            ON DUPLICATE KEY UPDATE
                talk_id = VALUES(talk_id)
        """
        try:
            db.execute_raw_query(
                upsert_query,
                {'user_id': user_id, 'talk_id': result[0]['talk_id']}
            )
        except Exception as e:
            print(f"Failed to update history: {str(e)}")

        return {
            "data": {
                "talk_id": result[0]['talk_id'],
                "eng_sentence": result[0]['eng_sentence'],
                "kor_sentence": result[0]['kor_sentence'],
                "parenthesis": result[0]['parenthesis'],
                "tag": result[0]['tag']
            },
            "navigation": {
                "has_prev": result[0].get('prev_id') is not None,
                "has_next": True,
                "prev_id": result[0].get('prev_id'),
                "next_id": result[0].get('next_id') or 1
            }
        }

    except Exception as e:
        print(f"Error in get_sentence: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


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
        current_user=Depends(get_current_user),
        db: MySQLConnector = Depends(get_db)
):
    """스몰톡 생성 (관리자 권한 필요)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다"
        )
    data = small_talk.dict(exclude_unset=True)
    result = db.insert('small_talk', data)

    created = db.execute_raw_query(
        "SELECT * FROM small_talk WHERE talk_id = %(talk_id)s",
        {'talk_id': result['id']}
    )
    return created[0]


@router.put("/{talk_id}", response_model=SmallTalk)
async def update_small_talk(
        talk_id: int,
        small_talk: SmallTalkUpdate,
        current_user=Depends(get_current_user),
        db: MySQLConnector = Depends(get_db)
):
    """스몰톡 전체 수정 (관리자 권한 필요)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다"
        )
    data = small_talk.dict(exclude_unset=True)
    result = db.update('small_talk', data, {'talk_id': talk_id})

    if result['affected_rows'] == 0:
        raise HTTPException(status_code=404, detail="Small talk not found")

    updated = db.execute_raw_query(
        "SELECT * FROM small_talk WHERE talk_id = %(talk_id)s",
        {'talk_id': talk_id}
    )
    return updated[0]


@router.patch("/{talk_id}", response_model=SmallTalk)
async def patch_small_talk(
        talk_id: int,
        small_talk: SmallTalkPatch,
        current_user=Depends(get_current_user),
        db: MySQLConnector = Depends(get_db)
):
    """스몰톡 부분 수정 (관리자 권한 필요)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다"
        )
    update_data = {
        k: v for k, v in small_talk.dict(exclude_unset=True).items()
        if v is not None
    }

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = db.update('small_talk', update_data, {'talk_id': talk_id})

    if result['affected_rows'] == 0:
        raise HTTPException(status_code=404, detail="Small talk not found")

    updated = db.execute_raw_query(
        "SELECT * FROM small_talk WHERE talk_id = %(talk_id)s",
        {'talk_id': talk_id}
    )
    return updated[0]


@router.delete("/{talk_id}")
async def delete_small_talk(
        talk_id: int,
        current_user=Depends(get_current_user),
        db: MySQLConnector = Depends(get_db)
):
    """스몰톡 삭제 (관리자 권한 필요)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다"
        )
    try:
        exists = db.execute_raw_query(
            "SELECT talk_id FROM small_talk WHERE talk_id = %(talk_id)s",
            {'talk_id': talk_id}
        )

        if not exists:
            raise HTTPException(status_code=404, detail="Small talk not found")

        db.execute_raw_query(
            "DELETE FROM answer WHERE talk_id = %(talk_id)s",
            {'talk_id': talk_id}
        )

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


