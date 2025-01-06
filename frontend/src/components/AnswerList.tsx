import React from 'react';
import { Answer } from '../types/api';
import { MessageCircle } from 'lucide-react';

interface Props {
  answers: Answer[];
}

export function AnswerList({ answers }: Props) {
  return (
    <div className="space-y-4">
      {answers.map((answer) => (
        <div
          key={answer.answer_id}
          className="p-4 rounded-lg border border-gray-200 bg-white"
        >
          <div className="flex items-start gap-3">
            <MessageCircle className="w-5 h-5 text-green-500 mt-1" />
            <div className="flex-1">
              <p className="text-gray-900 font-medium">{answer.eng_sentence}</p>
              <p className="text-gray-600 mt-1">{answer.kor_sentence}</p>
              <span className="text-gray-400 text-xs block mt-2">
                {new Date(answer.update_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}