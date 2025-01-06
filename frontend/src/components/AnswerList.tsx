import React, { useState } from 'react';
import { Answer } from '../types/api';
import { MessageCircle, Trash2 } from 'lucide-react';
import { deleteAnswer } from '../api';

interface Props {
  answers: Answer[];
  onDelete?: () => void;  // 삭제 후 리스트 새로고침을 위한 콜백
}

export function AnswerList({ answers, onDelete }: Props) {
  const [isDeleting, setIsDeleting] = useState<number | null>(null);

  const handleDelete = async (answerId: number, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!window.confirm('정말 이 답변을 삭제하시겠습니까?')) {
      return;
    }

    try {
      setIsDeleting(answerId);
      await deleteAnswer(answerId);
      onDelete?.();  // 삭제 후 리스트 새로고침
    } catch (error) {
      console.error('Failed to delete answer:', error);
      alert('삭제에 실패했습니다.');
    } finally {
      setIsDeleting(null);
    }
  };

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
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-gray-900 font-medium">{answer.eng_sentence}</p>
                  <p className="text-gray-600 mt-1">{answer.kor_sentence}</p>
                </div>
                <button
                  onClick={(e) => handleDelete(answer.answer_id, e)}
                  disabled={isDeleting === answer.answer_id}
                  className="p-2 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
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