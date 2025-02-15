# chat/exceptions.py
class ChatBaseException(Exception):
    """채팅 시스템 기본 예외 클래스"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class DatabaseError(ChatBaseException):
    """데이터베이스 작업 중 발생하는 예외"""
    pass

class ConversationNotFound(ChatBaseException):
    """대화를 찾을 수 없을 때 발생하는 예외"""
    pass

class ChatAccessDenied(ChatBaseException):
    """대화에 대한 접근 권한이 없을 때 발생하는 예외"""
    pass

class UserSettingsError(ChatBaseException):
    """사용자 설정 관련 예외"""
    pass

class PromptTemplateError(ChatBaseException):
    """프롬프트 템플릿 관련 예외"""
    pass

class OpenAIError(ChatBaseException):
    """OpenAI API 관련 예외"""
    pass

class SmallTalkError(ChatBaseException):
    """SmallTalk 관련 예외"""
    pass

class ChatValidationError(ChatBaseException):
    """입력값 검증 실패 시 발생하는 예외"""
    pass