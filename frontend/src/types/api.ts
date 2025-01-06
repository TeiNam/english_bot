export interface SmallTalk {
  talk_id: number;
  eng_sentence: string;
  kor_sentence: string;
  parenthesis: string;
  tag: string;
  update_at: string;
}

export interface Answer {
  answer_id: number;
  talk_id: number;
  eng_sentence: string;
  kor_sentence: string;
  update_at: string;
}

export interface BotStatus {
  running: boolean;
  jobs?: any[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}