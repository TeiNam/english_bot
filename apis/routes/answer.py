# apis/routes/answer.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from ..models.answer import Answer, AnswerCreate, AnswerUpdate
from utils.mysql_connector import MySQLConnector
from utils.auth import get_current_user
from ..deps import get_db

router = APIRouter(prefix="/api/v1/answers", tags=["answers"])

# 조회는 인증 없이 가능
@router.get("/{talk_id}", response_model=List[Answer])
async def get_answers(
        talk_id: int,
        db: MySQLConnector = Depends(get_db)
):
    """답변 목록 조회"""
    query = """
        SELECT 
            answer_id, talk_id, eng_sentence, kor_sentence, update_at
        FROM answer
        WHERE talk_id = %(talk_id)s
        ORDER BY answer_id
    """
    return db.execute_raw_query(query, {'talk_id': talk_id})

@router.get("/{talk_id}/count", response_model=dict)
async def get_answers_count(
        talk_id: int,
        db: MySQLConnector = Depends(get_db)
):
    """답변 개수 조회"""
    query = """
        SELECT 
            talk_id,
            COUNT(*) as answer_count
        FROM answer
        WHERE talk_id = %(talk_id)s
        GROUP BY talk_id
    """
    result = db.execute_raw_query(query, {'talk_id': talk_id})
    if not result:
        return {
            "talk_id": talk_id,
            "answer_count": 0
        }
    return {
        "talk_id": result[0]['talk_id'],
        "answer_count": result[0]['answer_count']
    }

# 생성/수정/삭제는 인증 필요
@router.post("/", response_model=Answer)
async def create_answer(
        answer: AnswerCreate,
        current_user = Depends(get_current_user),
        db: MySQLConnector = Depends(get_db)
):
    """답변 생성"""
    data = answer.dict()
    result = db.insert('answer', data)

    created = db.execute_raw_query(
        """
        SELECT answer_id, talk_id, eng_sentence, kor_sentence, update_at
        FROM answer 
        WHERE answer_id = %(answer_id)s
        """,
        {'answer_id': result['id']}
    )

    if not created:
        raise HTTPException(status_code=500, detail="Failed to create answer")

    return created[0]

@router.put("/{answer_id}", response_model=Answer)
async def update_answer(
        answer_id: int,
        answer: AnswerUpdate,
        current_user = Depends(get_current_user),
        db: MySQLConnector = Depends(get_db)
):
    """답변 수정"""
    data = answer.dict()
    result = db.update(
        'answer',
        data,
        {'answer_id': answer_id}
    )

    if result['affected_rows'] == 0:
        raise HTTPException(status_code=404, detail="Answer not found")

    updated = db.execute_raw_query(
        """
        SELECT answer_id, talk_id, eng_sentence, kor_sentence, update_at
        FROM answer 
        WHERE answer_id = %(answer_id)s
        """,
        {'answer_id': answer_id}
    )

    if not updated:
        raise HTTPException(status_code=500, detail="Failed to fetch updated answer")

    return updated[0]

@router.delete("/{answer_id}")
async def delete_answer(
        answer_id: int,
        current_user = Depends(get_current_user),
        db: MySQLConnector = Depends(get_db)
):
    """답변 삭제"""
    result = db.delete('answer', {'answer_id': answer_id})
    if result['affected_rows'] == 0:
        raise HTTPException(status_code=404, detail="Answer not found")
    return {"message": "Answer deleted"}