# apis/routes/vocabulary.py
from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from apis.deps import get_db
from apis.models.vocabulary import VocabularyCreate, VocabularyUpdate, Vocabulary
from utils.mysql_connector import MySQLConnector

router = APIRouter(prefix="/api/v1/vocabulary", tags=["vocabulary"])


# 페이지네이션 응답 모델
class PaginatedVocabulary(BaseModel):
    items: List[Vocabulary]
    total: int
    page: int
    size: int
    total_pages: int
    has_next: bool
    has_prev: bool


@router.get("/text-search", response_model=PaginatedVocabulary)
async def search_vocabularies(
        q: str = Query(..., description="검색어"),
        page: int = Query(default=1, ge=1),
        size: int = Query(default=10, le=100),
        db: MySQLConnector = Depends(get_db)
):
    """단어 전문 검색 (영어 단어)"""
    try:
        # 먼저 모든 vocabulary_id를 가져옵니다 (중복 없이)
        id_query = """
            SELECT DISTINCT v.vocabulary_id, v.create_at,
                   MATCH(v.word) AGAINST(%(query)s IN BOOLEAN MODE) as relevance
            FROM vocabulary v
            WHERE MATCH(v.word) AGAINST(%(query)s IN BOOLEAN MODE)
            ORDER BY relevance DESC, v.create_at DESC
        """
        all_ids = db.execute_raw_query(id_query, {'query': q})

        # 전체 고유 단어 수 계산
        total = len(all_ids)

        # 페이지네이션 계산
        total_pages = (total + size - 1) // size if total > 0 else 1
        offset = (page - 1) * size

        # 현재 페이지에 해당하는 ID만 필터링
        page_ids = [row['vocabulary_id'] for row in all_ids[offset:offset + size]]

        if not page_ids:
            return {
                "items": [],
                "total": total,
                "page": page,
                "size": size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }

        # ID 목록으로 상세 정보 쿼리
        placeholders = ','.join(['%s'] * len(page_ids))
        query = f"""
            SELECT 
                v.vocabulary_id, v.word, v.past_tense, v.past_participle, v.rule, 
                v.cycle, v.create_at, v.update_at,
                vm.meaning_id, vm.meaning, vm.classes, vm.example, vm.parenthesis, 
                vm.order_no, vm.create_at as meaning_create_at, vm.update_at as meaning_update_at
            FROM vocabulary v
            LEFT JOIN vocabulary_meaning vm ON v.vocabulary_id = vm.vocabulary_id
            WHERE v.vocabulary_id IN ({placeholders})
            ORDER BY FIELD(v.vocabulary_id, {placeholders})
        """

        # 파라미터를 두 번 포함시켜야 합니다 (IN 절과 ORDER BY FIELD 절)
        results = db.execute_raw_query(query, page_ids + page_ids)

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
            detail=f"단어 검색 실패: {str(e)}"
        )


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
        # 먼저 모든 vocabulary_id를 가져옵니다 (중복 없이)
        id_query = """
            SELECT DISTINCT vocabulary_id, create_at 
            FROM vocabulary
            ORDER BY create_at DESC
        """
        all_ids = db.execute_raw_query(id_query)

        # 전체 고유 단어 수 계산
        total = len(all_ids)

        # 페이지네이션 계산
        total_pages = (total + size - 1) // size if total > 0 else 1
        offset = (page - 1) * size

        # 현재 페이지에 해당하는 ID만 필터링
        page_ids = [row['vocabulary_id'] for row in all_ids[offset:offset + size]]

        if not page_ids:
            return {
                "items": [],
                "total": total,
                "page": page,
                "size": size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }

        # ID 목록으로 상세 정보 쿼리
        placeholders = ','.join(['%s'] * len(page_ids))
        query = f"""
            SELECT 
                v.*, 
                vm.meaning_id,
                vm.meaning,
                vm.classes,
                vm.example,
                vm.parenthesis,
                vm.order_no,
                vm.create_at as meaning_create_at,
                vm.update_at as meaning_update_at
            FROM vocabulary v
            LEFT JOIN vocabulary_meaning vm 
                ON v.vocabulary_id = vm.vocabulary_id
            WHERE v.vocabulary_id IN ({placeholders})
            ORDER BY FIELD(v.vocabulary_id, {placeholders})
        """

        # 파라미터를 두 번 포함시켜야 합니다 (IN 절과 ORDER BY FIELD 절)
        results = db.execute_raw_query(query, page_ids + page_ids)

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
            SELECT 
                v.*, 
                vm.meaning_id,
                vm.meaning,
                vm.classes,
                vm.example,
                vm.parenthesis,
                vm.order_no,
                vm.create_at as meaning_create_at,
                vm.update_at as meaning_update_at
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
                'example': meaning.example or "예문 없음.",  # 기본값 처리
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


@router.get("/meanings/counts")  # 라우트 경로 변경
async def get_vocabulary_meaning_counts_by_ids(
        vocabulary_ids: List[int] = Query(
            ...,  # ... means required
            description="조회할 어휘 ID 목록",
            example=[1, 2, 3]
        ),
        db: MySQLConnector = Depends(get_db)
):
    try:
        if not vocabulary_ids:
            return {}

        query = """
            SELECT 
                vocabulary_id, 
                COUNT(*) as count 
            FROM vocabulary_meaning 
            WHERE vocabulary_id IN ({})
            GROUP BY vocabulary_id
        """.format(','.join(['%s'] * len(vocabulary_ids)))

        result = db.execute_raw_query(query, tuple(vocabulary_ids))

        return {row['vocabulary_id']: row['count'] for row in result}  # int 변환 제거 (이미 int 타입)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"의미 개수 조회 실패: {str(e)}"
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
                'vocabulary_id': vocab_id,
                'meaning': row['meaning'],
                'classes': row['classes'],
                'example': row['example'],
                'parenthesis': row['parenthesis'],
                'order_no': row['order_no'],
                'create_at': row['meaning_create_at'],  # 변경된 이름 사용
                'update_at': row['meaning_update_at']  # 변경된 이름 사용
            })

    return list(vocabularies.values())