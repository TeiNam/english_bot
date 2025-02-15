# apis/routes/prompt.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
from utils.auth import get_current_user, User
from chat.prompt_manager import PromptManager
from apis.models.chat import (
    PromptTemplateResponse,
    PromptTemplateCreate,
    PromptTemplateUpdate
)
from chat.exceptions import DatabaseError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat/prompts", tags=["chat"])

def get_prompt_manager():
    return PromptManager()

@router.get("/templates", response_model=List[PromptTemplateResponse])
async def get_prompt_templates(
    current_user: User = Depends(get_current_user)
):
    """프롬프트 템플릿 목록 조회"""
    logger.info(f"Fetching prompt templates for user {current_user.user_id}")
    try:
        manager = get_prompt_manager()
        templates = manager.get_all_templates()
        return templates
    except DatabaseError as e:
        logger.error(f"Database error in get_prompt_templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_prompt_templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching prompt templates"
        )

@router.get("/templates/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template_by_id(
    template_id: int,
    current_user: User = Depends(get_current_user)
):
    """특정 프롬프트 템플릿 조회"""
    logger.info(f"Fetching prompt template {template_id} for user {current_user.user_id}")
    try:
        manager = get_prompt_manager()
        template = manager.get_template_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt template not found"
            )
        return template
    except DatabaseError as e:
        logger.error(f"Database error in get_prompt_template_by_id: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_prompt_template_by_id: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching the prompt template"
        )

@router.post("/templates", response_model=PromptTemplateResponse)
async def create_prompt_template(
        template: PromptTemplateCreate,
        current_user: User = Depends(get_current_user)
):
    """새로운 프롬프트 템플릿 생성"""
    logger.info(f"Creating new prompt template by user {current_user.user_id}")

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create prompt templates"
        )

    try:
        manager = get_prompt_manager()
        new_template = manager.create_template(template.dict())
        return new_template
    except DatabaseError as e:
        logger.error(f"Database error in create_prompt_template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in create_prompt_template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating prompt template"
        )

@router.put("/templates/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
        template_id: int,
        template: PromptTemplateUpdate,
        current_user: User = Depends(get_current_user)
):
    """프롬프트 템플릿 수정"""
    logger.info(f"Updating prompt template {template_id} by user {current_user.user_id}")

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can update prompt templates"
        )

    try:
        manager = get_prompt_manager()
        updated_template = manager.update_template(
            template_id,
            template.dict(exclude_unset=True)
        )
        if not updated_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt template not found"
            )
        return updated_template
    except DatabaseError as e:
        logger.error(f"Database error in update_prompt_template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in update_prompt_template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating prompt template"
        )