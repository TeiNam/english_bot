# apis/routes/vocabulary.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict
from pydantic import BaseModel
from apis.models.vocabulary import VocabularyCreate, VocabularyUpdate, Vocabulary
from apis.deps import get_db
from utils.mysql_connector import MySQLConnector

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


# 페이지네이션 응답 모델
class PaginatedVocabulary(BaseModel):
    items: List[Vocabulary]
    total: int
    page: int
    size: int
    total_pages: int
    has_next: bool
    has_prev: bool


@router.get("/count", response_model=Dict[str, int])
async def get_vocabularies_count(
        db: MySQLConnector = Depends(get_db)
) -> Dict[str, int]:
    """단어 전체 개수 조회"""
    try:
        result = db.execute_raw_query("SELECT COUNT(*) as total FROM vocabulary")
        return {"total": result[0]['total']}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"단어 수 조회 실패: {str(e)}"
        )


@router.get("/", response_model=PaginatedVocabulary)
async def get_vocabularies(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=10, le=100),
        db: MySQLConnector = Depends(get_db)
):
    """단어 목록 조회 (페이지네이션)"""
    try:
        # 전체 데이터 수 조회
        total = db.execute_raw_query("SELECT COUNT(*) as total FROM vocabulary")[0]['total']
        total_pages = (total + size - 1) // size
        offset = (page - 1) * size

        # 데이터 조회
        query = """
                SELECT 
                    v.vocabulary_id, v.word, v.past_tense, v.past_participle, v.rule, 
                    v.cycle, v.create_at, v.update_at,
                    vm.meaning_id, vm.meaning, vm.classes, vm.example, vm.parenthesis, 
                    vm.order_no, vm.create_at as meaning_create_at, vm.update_at as meaning_update_at
                FROM vocabulary v
                LEFT JOIN vocabulary_meaning vm 
                    ON v.vocabulary_id = vm.vocabulary_id
                ORDER BY v.create_at DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """
        results = db.execute_raw_query(query, {'limit': size, 'offset': offset})
        items = _group_vocabulary_results(results)

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
            detail=f"단어 목록 조회 실패: {str(e)}"
        )


@router.get("/{vocabulary_id}", response_model=Vocabulary)
async def get_vocabulary(vocabulary_id: int, db: MySQLConnector = Depends(get_db)):
    """단어 상세 조회"""
    query = """
        SELECT v.*, vm.* 
        FROM vocabulary v
        LEFT JOIN vocabulary_meaning vm 
            ON v.vocabulary_id = vm.vocabulary_id 
        WHERE v.vocabulary_id = %(vocabulary_id)s
    """
    results = db.execute_raw_query(query, {'vocabulary_id': vocabulary_id})
    if not results:
        raise HTTPException(status_code=404, detail="단어를 찾을 수 없습니다")

    items = _group_vocabulary_results(results)
    return items[0]


@router.post("/", response_model=Vocabulary)
async def create_vocabulary(
    vocabulary: VocabularyCreate,
    db: MySQLConnector = Depends(get_db)
):
    """단어 생성"""
    try:
        db.begin_transaction()

        # 단어 추가
        vocab_data = {
            'word': vocabulary.word,
            'past_tense': vocabulary.past_tense,
            'past_participle': vocabulary.past_participle,
            'rule': vocabulary.rule.value  # Enum 값을 문자열로 변환
        }
        vocab_result = db.insert('vocabulary', vocab_data)
        vocabulary_id = vocab_result['id']

        # 의미 추가
        for idx, meaning in enumerate(vocabulary.meanings, 1):
            meaning_data = {
                'vocabulary_id': vocabulary_id,
                'meaning': meaning.meaning,
                'classes': meaning.classes or "기타",  # 기본값 처리
                'example': meaning.example or "예문 없음.",     # 기본값 처리
                'parenthesis': meaning.parenthesis,
                'order_no': idx
            }
            db.insert('vocabulary_meaning', meaning_data)

        db.commit_transaction()
        return await get_vocabulary(vocabulary_id, db)

    except Exception as e:
        db.rollback_transaction()
        raise HTTPException(
            status_code=500,
            detail=f"단어 생성 실패: {str(e)}"
        )


@router.put("/{vocabulary_id}", response_model=Vocabulary)
async def update_vocabulary(
        vocabulary_id: int,
        vocabulary: VocabularyUpdate,
        db: MySQLConnector = Depends(get_db)
):
    """단어 전체 수정"""
    try:
        db.begin_transaction()

        # 단어 정보 업데이트
        if word_update := vocabulary.dict(exclude={'meanings'}, exclude_unset=True):
            db.update('vocabulary', word_update, {'vocabulary_id': vocabulary_id})

        # 의미 업데이트/추가/삭제
        existing_meanings = db.execute_raw_query(
            "SELECT meaning_id FROM vocabulary_meaning WHERE vocabulary_id = %(vocabulary_id)s",
            {'vocabulary_id': vocabulary_id}
        )
        existing_meaning_ids = [m['meaning_id'] for m in existing_meanings]

        for idx, meaning in enumerate(vocabulary.meanings, 1):
            meaning_data = {
                'vocabulary_id': vocabulary_id,
                'meaning': meaning.meaning,
                'classes': meaning.classes,
                'example': meaning.example or "예문 없음",
                'parenthesis': meaning.parenthesis,
                'order_no': idx
            }

            if idx <= len(existing_meaning_ids):
                # 기존 의미 업데이트
                db.update('vocabulary_meaning', meaning_data,
                          {'meaning_id': existing_meaning_ids[idx - 1]})
            else:
                # 새로운 의미 추가
                db.insert('vocabulary_meaning', meaning_data)

        # 남은 의미 삭제
        if len(vocabulary.meanings) < len(existing_meaning_ids):
            delete_ids = existing_meaning_ids[len(vocabulary.meanings):]
            placeholders = ','.join(['%s'] * len(delete_ids))
            db.execute_raw_query(
                f"DELETE FROM vocabulary_meaning WHERE meaning_id IN ({placeholders})",
                delete_ids
            )

        db.commit_transaction()
        return await get_vocabulary(vocabulary_id, db)

    except Exception as e:
        db.rollback_transaction()
        raise HTTPException(
            status_code=500,
            detail=f"단어 수정 실패: {str(e)}"
        )


@router.delete("/{vocabulary_id}")
async def delete_vocabulary(
        vocabulary_id: int,
        db: MySQLConnector = Depends(get_db)
):
    """단어 삭제"""
    try:
        db.begin_transaction()

        # 단어 존재 여부 확인
        exists = db.execute_raw_query(
            "SELECT vocabulary_id FROM vocabulary WHERE vocabulary_id = %(vocabulary_id)s",
            {'vocabulary_id': vocabulary_id}
        )
        if not exists:
            raise HTTPException(status_code=404, detail="단어를 찾을 수 없습니다")

        # 의미 삭제
        db.execute_raw_query(
            "DELETE FROM vocabulary_meaning WHERE vocabulary_id = %(vocabulary_id)s",
            {'vocabulary_id': vocabulary_id}
        )

        # 단어 삭제
        db.execute_raw_query(
            "DELETE FROM vocabulary WHERE vocabulary_id = %(vocabulary_id)s",
            {'vocabulary_id': vocabulary_id}
        )

        db.commit_transaction()
        return {"status": "success", "message": "단어가 성공적으로 삭제되었습니다"}

    except HTTPException:
        db.rollback_transaction()
        raise
    except Exception as e:
        db.rollback_transaction()
        raise HTTPException(
            status_code=500,
            detail=f"단어 삭제 실패: {str(e)}"
        )


def _group_vocabulary_results(results: List[Dict]) -> List[Dict]:
    """쿼리 결과를 단어별로 그룹화"""
    vocabularies = {}
    for row in results:
        vocab_id = row['vocabulary_id']
        if vocab_id not in vocabularies:
            vocabularies[vocab_id] = {
                'vocabulary_id': vocab_id,
                'word': row['word'],
                'past_tense': row['past_tense'],
                'past_participle': row['past_participle'],
                'rule': row['rule'],
                'cycle': row['cycle'],
                'create_at': row['create_at'],
                'update_at': row['update_at'],
                'meanings': []
            }

        if meaning_id := row.get('meaning_id'):
            vocabularies[vocab_id]['meanings'].append({
                'meaning_id': meaning_id,
                'vocabulary_id': vocab_id,  # vocabulary_id 추가
                'meaning': row['meaning'],
                'classes': row['classes'],
                'example': row['example'],
                'parenthesis': row['parenthesis'],
                'order_no': row['order_no'],
                'create_at': row['create_at'],  # create_at 추가
                'update_at': row['update_at']   # update_at 추가
            })

    return list(vocabularies.values())