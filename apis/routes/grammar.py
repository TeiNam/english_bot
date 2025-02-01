#apis/routrs/grammar.py
from fastapi import APIRouter, Depends, HTTPException, Query
from apis.models.grammar import Grammar, GrammarCreate, GrammarUpdate, GrammarResponse
from apis.deps import get_db
from utils.mysql_connector import MySQLConnector

router = APIRouter(prefix="/api/v1/grammar", tags=["grammar"])


@router.post("/", response_model=Grammar)
async def create_grammar(
        grammar: GrammarCreate,
        db: MySQLConnector = Depends(get_db)
):
    """문법 생성"""
    try:
        db.begin_transaction()
        grammar_data = grammar.dict(exclude_unset=True)
        result = db.insert('grammar', grammar_data)
        grammar_id = result['id']

        created = db.execute_raw_query(
            "SELECT * FROM grammar WHERE grammar_id = %(grammar_id)s",
            {'grammar_id': grammar_id}
        )
        db.commit_transaction()
        return created[0]
    except Exception as e:
        db.rollback_transaction()
        raise HTTPException(
            status_code=500,
            detail=f"문법 생성 실패: {str(e)}"
        )


@router.get("/", response_model=GrammarResponse)
async def get_grammars(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100),
        db: MySQLConnector = Depends(get_db)
):
    """문법 목록 조회"""
    try:
        # 전체 데이터 수 조회
        total = db.execute_raw_query("SELECT COUNT(*) as total FROM grammar")[0]['total']
        total_pages = (total + limit - 1) // limit

        # 데이터 조회
        query = """
            SELECT * FROM grammar
            ORDER BY create_at DESC
            LIMIT %(limit)s OFFSET %(skip)s
        """
        items = db.execute_raw_query(query, {'limit': limit, 'skip': skip})

        page = (skip // limit) + 1

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"문법 목록 조회 실패: {str(e)}"
        )


@router.get("/{grammar_id}", response_model=Grammar)
async def get_grammar(
        grammar_id: int,
        db: MySQLConnector = Depends(get_db)
):
    """문법 상세 조회"""
    result = db.execute_raw_query(
        "SELECT * FROM grammar WHERE grammar_id = %(grammar_id)s",
        {'grammar_id': grammar_id}
    )
    if not result:
        raise HTTPException(status_code=404, detail="문법을 찾을 수 없습니다")
    return result[0]


@router.put("/{grammar_id}", response_model=Grammar)
async def update_grammar(
        grammar_id: int,
        grammar: GrammarUpdate,
        db: MySQLConnector = Depends(get_db)
):
    """문법 수정"""
    try:
        db.begin_transaction()

        exists = db.execute_raw_query(
            "SELECT grammar_id FROM grammar WHERE grammar_id = %(grammar_id)s",
            {'grammar_id': grammar_id}
        )
        if not exists:
            raise HTTPException(status_code=404, detail="문법을 찾을 수 없습니다")

        update_data = grammar.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="수정할 내용이 없습니다")

        db.update('grammar', update_data, {'grammar_id': grammar_id})

        updated = db.execute_raw_query(
            "SELECT * FROM grammar WHERE grammar_id = %(grammar_id)s",
            {'grammar_id': grammar_id}
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
            detail=f"문법 수정 실패: {str(e)}"
        )


@router.delete("/{grammar_id}")
async def delete_grammar(
        grammar_id: int,
        db: MySQLConnector = Depends(get_db)
):
    """문법 삭제"""
    try:
        db.begin_transaction()

        exists = db.execute_raw_query(
            "SELECT grammar_id FROM grammar WHERE grammar_id = %(grammar_id)s",
            {'grammar_id': grammar_id}
        )
        if not exists:
            raise HTTPException(status_code=404, detail="문법을 찾을 수 없습니다")

        db.execute_raw_query(
            "DELETE FROM grammar WHERE grammar_id = %(grammar_id)s",
            {'grammar_id': grammar_id}
        )

        db.commit_transaction()
        return {"status": "success", "message": "문법이 성공적으로 삭제되었습니다"}
    except HTTPException:
        db.rollback_transaction()
        raise
    except Exception as e:
        db.rollback_transaction()
        raise HTTPException(
            status_code=500,
            detail=f"문법 삭제 실패: {str(e)}"
        )