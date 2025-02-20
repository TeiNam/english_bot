# apis/routes/answer.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from utils.auth import get_current_user
from utils.mysql_connector import MySQLConnector
from ..deps import get_db
from ..models.answer import Answer, AnswerCreate, AnswerUpdate

router = APIRouter(prefix="/api/v1/answers", tags=["answers"])


@router.get("/counts")
async def get_answers_counts(
        talk_ids: str = Query(..., description="콤마로 구분된 talk_id 목록"),
        db: MySQLConnector = Depends(get_db)
):
    """현재 페이지의 답변 개수 일괄 조회"""
    try:
        id_list = [int(id.strip()) for id in talk_ids.split(',') if id.strip()]

        if not id_list:
            return []

        # IN 절에서 직접 문자열로 변환
        ids_string = ','.join(str(id) for id in id_list)

        query = f"""
            SELECT 
                talk_id,
                COUNT(*) as answer_count
            FROM answer
            WHERE talk_id IN ({ids_string})
            GROUP BY talk_id
        """

        results = db.execute_raw_query(query)

        counts = {row['talk_id']: row['answer_count'] for row in results}
        return [
            {
                "talk_id": talk_id,
                "answer_count": counts.get(talk_id, 0)
            }
            for talk_id in id_list
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid talk_ids format")
    except Exception as e:
        print(f"Error in get_answers_counts: {str(e)}")  # 로그 추가
        raise HTTPException(status_code=500, detail="Failed to get answer counts")


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


# 생성/수정/삭제는 인증 필요
@router.post("/", response_model=Answer)
async def create_answer(
        answer: AnswerCreate,
        current_user=Depends(get_current_user),
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
        current_user=Depends(get_current_user),
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
        current_user=Depends(get_current_user),
        db: MySQLConnector = Depends(get_db)
):
    """답변 삭제"""
    result = db.delete('answer', {'answer_id': answer_id})
    if result['affected_rows'] == 0:
        raise HTTPException(status_code=404, detail="Answer not found")
    return {"message": "Answer deleted"}
