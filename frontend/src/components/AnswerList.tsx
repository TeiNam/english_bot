import React, { useState } from 'react';
import { Answer } from '../types/api';
import { MessageCircle, Trash2, Pencil } from 'lucide-react';
import { deleteAnswer, updateAnswer } from '../api';

interface Props {
  answers: Answer[];
  onDelete?: () => void;
  onUpdate?: () => void;
}

export function AnswerList({ answers, onDelete, onUpdate }: Props) {
  const [isDeleting, setIsDeleting] = useState<number | null>(null);
  const [editingAnswer, setEditingAnswer] = useState<Answer | null>(null);

  const handleDelete = async (answerId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('정말 이 답변을 삭제하시겠습니까?')) {
      return;
    }

    try {
      setIsDeleting(answerId);
      await deleteAnswer(answerId);
      onDelete?.();
    } catch (error) {
      console.error('Failed to delete answer:', error);
      alert('삭제에 실패했습니다.');
    } finally {
      setIsDeleting(null);
    }
  };

  const handleEdit = async (answer: Answer, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingAnswer(answer);
  };

  const handleUpdate = async (answer: Answer) => {
    try {
      await updateAnswer(answer.answer_id, {
        eng_sentence: answer.eng_sentence,
        kor_sentence: answer.kor_sentence,
      });
      setEditingAnswer(null);
      onUpdate?.();
    } catch (error) {
      console.error('Failed to update answer:', error);
      alert('수정에 실패했습니다.');
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
                <div className="flex gap-2">
                  <button
                    onClick={(e) => handleEdit(answer, e)}
                    className="p-2 text-gray-400 hover:text-blue-500 transition-colors"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => handleDelete(answer.answer_id, e)}
                    disabled={isDeleting === answer.answer_id}
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <span className="text-gray-400 text-xs block mt-2">
                {new Date(answer.update_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
      ))}

      {editingAnswer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg w-full max-w-lg">
            <h3 className="text-lg font-semibold mb-4">답변 수정</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">영어 답변</label>
                <input
                  type="text"
                  value={editingAnswer.eng_sentence}
                  onChange={e => setEditingAnswer({...editingAnswer, eng_sentence: e.target.value})}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">한글 답변</label>
                <input
                  type="text"
                  value={editingAnswer.kor_sentence}
                  onChange={e => setEditingAnswer({...editingAnswer, kor_sentence: e.target.value})}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setEditingAnswer(null)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  취소
                </button>
                <button
                  type="button"
                  onClick={() => handleUpdate(editingAnswer)}
                  className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                >
                  수정
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}