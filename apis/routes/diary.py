# apis/routes/diary.py
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from apis.models.diary import DiaryCreate, DiaryUpdate, DiaryResponse
from diary.ai import DiaryAnalyzer
from diary.diary import DiaryService
from utils.auth import get_current_user, User
from utils.error_handler import handle_errors
from utils.pagination import PageResponse

router = APIRouter(prefix="/api/v1/diary", tags=["diary"])


@router.get("", response_model=PageResponse[DiaryResponse])
@handle_errors
async def get_diaries(
        page: int = 1,
        size: int = 10,
        current_user: User = Depends(get_current_user)
):
    """일기 목록 조회"""
    service = DiaryService()
    return service.get_diaries(page, size)


@router.post("", response_model=DiaryResponse)
@handle_errors
async def create_diary(
        diary: DiaryCreate,
        current_user: User = Depends(get_current_user)
):
    """새 일기 작성"""
    service = DiaryService()

    if not diary.body.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Diary body cannot be empty"
        )

    existing = service.get_diary_by_date(diary.date)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A diary for this date already exists"
        )

    diary_data = diary.model_dump()
    return service.create_diary(diary_data)


@router.get("/date/{date}", response_model=DiaryResponse)
@handle_errors
async def get_diary_by_date(
        date: date,
        current_user: User = Depends(get_current_user)
):
    """날짜로 일기 조회"""
    service = DiaryService()
    diary = service.get_diary_by_date(date)
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary not found for this date"
        )
    return diary


@router.get("/{diary_id}", response_model=DiaryResponse)
@handle_errors
async def get_diary(
        diary_id: int,
        current_user: User = Depends(get_current_user)
):
    """특정 일기 조회"""
    service = DiaryService()
    diary = service.get_diary(diary_id)
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary not found"
        )
    return diary


@router.put("/{diary_id}", response_model=DiaryResponse)
@handle_errors
async def update_diary(
        diary_id: int,
        diary: DiaryUpdate,
        current_user: User = Depends(get_current_user)
):
    service = DiaryService()
    existing = service.get_diary(diary_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary not found"
        )

    update_data = {
        "body": diary.body
    }

    if diary.date is not None:
        try:
            # 문자열을 date 객체로 변환
            date_obj = date.fromisoformat(diary.date)
            # 중복 체크
            existing_diary = service.get_diary_by_date(date_obj)
            if existing_diary and existing_diary.diary_id != diary_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A diary for this date already exists"
                )
            update_data["date"] = date_obj
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

    if diary.feedback is not None:
        update_data["feedback"] = diary.feedback

    return service.update_diary(diary_id, update_data)


@router.delete("/{diary_id}")
@handle_errors
async def delete_diary(
        diary_id: int,
        current_user: User = Depends(get_current_user)
):
    """일기 삭제"""
    service = DiaryService()
    existing = service.get_diary(diary_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary not found"
        )

    success = service.delete_diary(diary_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete diary"
        )

    return {"message": "Diary deleted successfully"}


@router.post("/{diary_id}/feedback", response_model=DiaryResponse)
@handle_errors
async def generate_feedback(
        diary_id: int,
        current_user: User = Depends(get_current_user)
):
    """AI를 사용하여 일기 피드백 생성"""
    service = DiaryService()
    diary = service.get_diary(diary_id)
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary not found"
        )

    analyzer = DiaryAnalyzer()
    feedback = await analyzer.analyze_diary(diary.body)

    # 피드백 업데이트
    return service.update_feedback(diary_id, feedback)
