# diary/diary.py
import logging
from datetime import date  # datetime 추가
from typing import List, Optional

from apis.models.diary import DiaryResponse
from utils.mysql_connector import MySQLConnector
from utils.pagination import PageResponse

logger = logging.getLogger(__name__)


class DiaryService:
    def __init__(self):
        self.db = MySQLConnector()

    def execute_query(self, query: str, params: dict = None) -> List[dict]:
        """공통 쿼리 실행 메서드"""
        try:
            return self.db.execute_raw_query(query, params or {})
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    def get_by_condition(self, condition: dict) -> Optional[dict]:
        """조건에 따른 일기 조회"""
        conditions = " AND ".join(f"{k} = %({k})s" for k in condition.keys())
        query = f"""
            SELECT diary_id, date, body, feedback, create_at, update_at
            FROM diary
            WHERE {conditions}
        """
        result = self.execute_query(query, condition)
        return result[0] if result else None

    def get_diary(self, diary_id: int) -> Optional[DiaryResponse]:
        """특정 일기 조회"""
        result = self.get_by_condition({"diary_id": diary_id})
        return DiaryResponse(**result) if result else None

    def get_diary_by_date(self, date: date) -> Optional[DiaryResponse]:
        """날짜로 일기 조회"""
        result = self.get_by_condition({"date": date})
        return DiaryResponse(**result) if result else None

    # diary/diary.py
    def create_diary(self, data: dict) -> DiaryResponse:  # 리턴 타입 수정
        """일기 생성"""
        logger.info(f"Service creating diary with data: {data}")

        diary_data = {
            "date": data["date"].strftime('%Y-%m-%d') if isinstance(data["date"], date) else data["date"],
            "body": data["body"]
        }
        logger.info(f"Formatted diary data: {diary_data}")

        try:
            result = self.db.insert("diary", diary_data)
            logger.info(f"Insert result: {result}")

            created_diary = self.get_diary(result['id'])
            logger.info(f"Created diary: {created_diary}")

            if not created_diary:
                raise Exception("Failed to fetch created diary")

            return created_diary
        except Exception as e:
            logger.error(f"Error in create_diary: {str(e)}")
            raise

    def update_diary(self, diary_id: int, data: dict) -> DiaryResponse:
        """일기 수정"""
        try:
            where = {"diary_id": diary_id}
            self.db.update("diary", data, where)
            return self.get_diary(diary_id)
        except Exception as e:
            logger.error(f"Failed to update diary: {str(e)}")
            raise

    def get_diaries(self, page: int, size: int) -> PageResponse[DiaryResponse]:
        """페이지네이션된 일기 목록 조회"""
        try:
            offset = (page - 1) * size

            # 전체 개수 조회
            total_result = self.execute_query("SELECT COUNT(*) as total FROM diary")
            total = total_result[0]['total'] if total_result else 0

            # 페이지네이션된 목록 조회
            items = self.execute_query("""
                SELECT diary_id, date, body, feedback, create_at, update_at
                FROM diary
                ORDER BY date DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """, {"limit": size, "offset": offset})

            # dict를 DiaryResponse 모델로 변환
            diary_items = [DiaryResponse(**item) for item in items]

            return PageResponse(
                items=diary_items,
                total=total,
                page=page,
                size=size
            )
        except Exception as e:
            logger.error(f"Failed to get diary list: {str(e)}")
            raise

    def delete_diary(self, diary_id: int) -> bool:
        """일기 삭제"""
        try:
            where = {"diary_id": diary_id}
            result = self.db.delete("diary", where)
            return result.get('affected_rows', 0) > 0
        except Exception as e:
            logger.error(f"Failed to delete diary: {str(e)}")
            raise

    def update_feedback(self, diary_id: int, feedback: str) -> DiaryResponse:
        """피드백 업데이트"""
        try:
            where = {"diary_id": diary_id}
            update_data = {"feedback": feedback}
            self.db.update("diary", update_data, where)
            return self.get_diary(diary_id)
        except Exception as e:
            logger.error(f"Failed to update feedback: {str(e)}")
            raise
