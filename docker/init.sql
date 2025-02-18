-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS eng_base;
-- 기본 charset 설정
ALTER DATABASE eng_base CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci;
USE eng_base;

-- eng_base.answer definition

CREATE TABLE `answer` (
  `answer_id` smallint unsigned NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `talk_id` smallint unsigned NOT NULL COMMENT '주체 문장 ID',
  `eng_sentence` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '영어 문장',
  `kor_sentence` text COLLATE utf8mb4_general_ci COMMENT '한국어 문장',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '등록 수정일',
  PRIMARY KEY (`answer_id`),
  KEY `answer_talk_id_IDX` (`talk_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='답변';


-- eng_base.chat_history definition

CREATE TABLE `chat_history` (
  `chat_history_id` int unsigned NOT NULL AUTO_INCREMENT,
  `conversation_id` char(18) COLLATE utf8mb4_general_ci NOT NULL COMMENT '대화 세션 식별자',
  `user_id` tinyint unsigned NOT NULL COMMENT '사용자 식별자',
  `user_message` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '사용자 메시지',
  `bot_response` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '봇 응답',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시간',
  PRIMARY KEY (`chat_history_id`),
  KEY `chat_history_conversation_id_IDX` (`conversation_id`),
  KEY `chat_history_user_id_IDX` (`user_id`),
  KEY `chat_history_create_at_IDX` (`create_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='OpenAI 챗봇 대화 이력';


-- eng_base.conversation_session definition

CREATE TABLE `conversation_session` (
  `conversation_id` char(18) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT (uuid_short()),
  `user_id` tinyint unsigned NOT NULL COMMENT '사용자 식별자',
  `title` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '대화 제목',
  `status` enum('active','archived','deleted') COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'active' COMMENT '대화 상태',
  `message_count` int NOT NULL DEFAULT '0' COMMENT '메시지 수',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
  `last_message_at` datetime NOT NULL COMMENT '마지막 메시지 시간',
  PRIMARY KEY (`conversation_id`),
  KEY `conversation_sessions_user_id_status_IDX` (`user_id`,`status`),
  KEY `conversation_sessions_last_message_at_IDX` (`last_message_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='대화 세션 메타데이터';


-- eng_base.grammar definition

CREATE TABLE `grammar` (
  `grammar_id` int unsigned NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `title` varchar(100) COLLATE utf8mb4_general_ci NOT NULL COMMENT '타이틀',
  `body` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '내용 정리',
  `url` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '강의 링크 URL',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록일자',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일자',
  PRIMARY KEY (`grammar_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='문법';


-- eng_base.last_sentence definition

CREATE TABLE `last_sentence` (
  `sentence_id` int unsigned NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `user_id` tinyint unsigned NOT NULL COMMENT '사용자 ID',
  `talk_id` smallint unsigned NOT NULL COMMENT '마지막으로 본 문장 ID',
  `viewed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '조회 시간',
  PRIMARY KEY (`sentence_id`),
  UNIQUE KEY `last_sentence_user_id_UIDX` (`user_id`) USING BTREE,
  KEY `last_sentence_user_id_talk_id_IDX` (`user_id`,`talk_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='사용자별 마지막 조회 문장';


-- eng_base.opic definition

CREATE TABLE `opic` (
  `opic_id` int unsigned NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `section` enum('General-Topics','Role-Play') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '섹션',
  `survey` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '서베이',
  `question` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '질문',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록일자',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일자',
  PRIMARY KEY (`opic_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='오픽 서베이';


-- eng_base.prompt_template definition

CREATE TABLE `prompt_template` (
  `prompt_template_id` tinyint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_general_ci NOT NULL COMMENT '템플릿 이름',
  `description` text COLLATE utf8mb4_general_ci COMMENT '템플릿 설명',
  `system_prompt` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '시스템 프롬프트',
  `user_prompt` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '사용자 프롬프트 템플릿',
  `is_active` char(1) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Y' COMMENT '활성화 여부',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시간',
  PRIMARY KEY (`prompt_template_id`),
  UNIQUE KEY `prompt_template_name_IDX` (`name`),
  KEY `prompt_template_is_active_IDX` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='프롬프트 템플릿';


-- eng_base.small_talk definition

CREATE TABLE `small_talk` (
  `talk_id` smallint unsigned NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `eng_sentence` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '영어 문장',
  `kor_sentence` text COLLATE utf8mb4_general_ci COMMENT '의미',
  `parenthesis` text COLLATE utf8mb4_general_ci COMMENT '추가설명',
  `tag` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '태그',
  `cycle_number` int unsigned NOT NULL DEFAULT '0' COMMENT '사이클 횟수',
  `last_sent_at` datetime DEFAULT NULL COMMENT '마지막 발송일',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록일',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '등록 수정일',
  PRIMARY KEY (`talk_id`),
  KEY `small_talk_cycle_number_IDX` (`cycle_number`,`last_sent_at` DESC) USING BTREE,
  KEY `small_talk_create_at_IDX` (`create_at` DESC) USING BTREE,
  FULLTEXT KEY `small_talk_eng_sentence_FTX` (`eng_sentence`,`kor_sentence`,`parenthesis`,`tag`) /*!50100 WITH PARSER `ngram` */
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='스몰토크 문장';


-- eng_base.`user` definition

CREATE TABLE `user` (
  `user_id` tinyint unsigned NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `username` varchar(20) COLLATE utf8mb4_general_ci NOT NULL COMMENT '유저명',
  `password` varchar(255) COLLATE utf8mb4_general_ci NOT NULL COMMENT '패스워드',
  `email` varchar(100) COLLATE utf8mb4_general_ci NOT NULL COMMENT '이메일',
  `is_active` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Y' COMMENT '활성화 여부',
  `is_admin` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'N' COMMENT '관리자 여부',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록일',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일자',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `user_username_UIDX` (`username`) USING BTREE,
  UNIQUE KEY `user_email_UIDX` (`email`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='유저 테이블';

INSERT INTO `user` (username, password, email, is_active, is_admin) VALUES('admin', '$pbkdf2-sha256$29000$yZlzbm3N2fvfW8tZ611rDQ$qXtiZPr/XBpR6TXRGqTpyFStnFpN0J/naB47DAsPvIU', 'admin', 'Y', 'Y');

-- eng_base.user_chat_setting definition

CREATE TABLE `user_chat_setting` (
  `user_id` tinyint unsigned NOT NULL,
  `default_prompt_template_id` tinyint unsigned DEFAULT NULL COMMENT '기본 프롬프트 템플릿 ID',
  `model` enum('gpt-4o-mini','gpt-4o') COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'gpt-4o-mini' COMMENT '모델',
  `temperature` float NOT NULL DEFAULT '0.7' COMMENT '모델 temperature 설정',
  `max_tokens` int NOT NULL DEFAULT '1000' COMMENT '최대 토큰 수',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시간',
  PRIMARY KEY (`user_id`),
  KEY `user_chat_setting_update_at_IDX` (`update_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='사용자별 챗봇 설정';


-- eng_base.vocabulary definition

CREATE TABLE `vocabulary` (
  `vocabulary_id` int unsigned NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `word` varchar(100) COLLATE utf8mb4_general_ci NOT NULL COMMENT '단어',
  `past_tense` varchar(100) COLLATE utf8mb4_general_ci NOT NULL COMMENT '과거형',
  `past_participle` varchar(100) COLLATE utf8mb4_general_ci NOT NULL COMMENT '과거분사',
  `rule` enum('규칙','불규칙') COLLATE utf8mb4_general_ci NOT NULL DEFAULT '규칙' COMMENT '규칙성',
  `cycle` tinyint unsigned NOT NULL DEFAULT '0' COMMENT '싸이클',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록일자',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일자',
  PRIMARY KEY (`vocabulary_id`),
  FULLTEXT KEY `vocabulary_word_FTX` (`word`) /*!50100 WITH PARSER `ngram` */
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='뜻이 많은 단어';


-- eng_base.vocabulary_meaning definition

CREATE TABLE `vocabulary_meaning` (
  `meaning_id` int unsigned NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `vocabulary_id` int unsigned NOT NULL COMMENT 'FK',
  `meaning` varchar(180) COLLATE utf8mb4_general_ci NOT NULL COMMENT '의미',
  `classes` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '품사',
  `example` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '예문 없음' COMMENT '예문',
  `parenthesis` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '부연 설명',
  `order_no` tinyint unsigned NOT NULL DEFAULT '1' COMMENT '순서',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록일자',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일자',
  PRIMARY KEY (`meaning_id`),
  KEY `vocabulary_meaning_vocabulary_id_IDX` (`vocabulary_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='단어 뜻';


-- eng_base.diary definition

CREATE TABLE `diary` (
  `diary_id` int unsigned NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `date` date NOT NULL COMMENT '날짜',
  `body` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '본문',
  `feedback` text COLLATE utf8mb4_general_ci COMMENT '피드백',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일자',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일자',
  PRIMARY KEY (`diary_id`),
  UNIQUE KEY `diary_date_IDX` (`date` DESC) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='일기';