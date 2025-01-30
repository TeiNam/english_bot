-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS eng_base;
-- 기본 charset 설정
ALTER DATABASE eng_base CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci;
USE eng_base;

-- answer 테이블 생성
CREATE TABLE `answer` (
  `answer_id` smallint unsigned NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `talk_id` smallint unsigned NOT NULL COMMENT '주체 문장 ID',
  `eng_sentence` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '영어 문장',
  `kor_sentence` text COLLATE utf8mb4_general_ci COMMENT '한국어 문장',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '등록 수정일',
  PRIMARY KEY (`answer_id`),
  KEY `answer_talk_id_IDX` (`talk_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='답변';

-- small_talk 테이블 생성
CREATE TABLE `small_talk` (
  `talk_id` smallint unsigned NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `eng_sentence` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '영어 문장',
  `kor_sentence` text COLLATE utf8mb4_general_ci COMMENT '의미',
  `parenthesis` text COLLATE utf8mb4_general_ci COMMENT '추가설명',
  `tag` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '태그',
  `cycle_number` int unsigned NOT NULL DEFAULT '0' COMMENT '사이클 횟수',
  `last_sent_at` datetime DEFAULT NULL COMMENT '마지막 발송일',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '등록 수정일',
  PRIMARY KEY (`talk_id`),
  KEY `small_talk_cycle_number_IDX` (`cycle_number`,`last_sent_at` DESC) USING BTREE,
  KEY `small_talk_update_at_IDX` (`update_at` DESC) USING BTREE,
  FULLTEXT KEY `small_talk_eng_sentence_FTX` (`eng_sentence`,`kor_sentence`,`parenthesis`,`tag`) /*!50100 WITH PARSER `ngram` */
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='스몰토크 문장';

-- eng_base.`user` definition

CREATE TABLE `user` (
  `user_id` tinyint unsigned NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `username` varchar(20) COLLATE utf8mb4_general_ci NOT NULL COMMENT '유저명',
  `password` varchar(255) COLLATE utf8mb4_general_ci NOT NULL COMMENT '패스워드',
  `email` varchar(100) COLLATE utf8mb4_general_ci NOT NULL COMMENT '이메일',
  `is_active` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Y' COMMENT '활성화 여부',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록일',
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일자',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `user_username_UIDX` (`username`) USING BTREE,
  UNIQUE KEY `user_email_UIDX` (`email`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='유저 테이블';