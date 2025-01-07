import React, { useState } from 'react';
import { SmallTalk } from '../types/api';
import { Trash2, Pencil } from 'lucide-react';
import { deleteSmallTalk, updateSmallTalk } from '../api';

interface Props {
  smallTalks: SmallTalk[];
  onSelect: (talk: SmallTalk) => void;
  selectedTalkId?: number;
  onDelete?: () => void;
  onUpdate?: () => void;
}

export function SmallTalkList({ smallTalks = [], onSelect, selectedTalkId, onDelete, onUpdate }: Props) {
  const [isDeleting, setIsDeleting] = useState<number | null>(null);
  const [editingTalk, setEditingTalk] = useState<SmallTalk | null>(null);

  const handleDelete = async (talkId: number, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!window.confirm('정말 이 스몰톡을 삭제하시겠습니까?')) {
      return;
    }

    try {
      setIsDeleting(talkId);
      await deleteSmallTalk(talkId);
      onDelete?.();
    } catch (error) {
      console.error('Error occurred but deletion might have succeeded:', error);
      onDelete?.();
    } finally {
      setIsDeleting(null);
    }
  };

  const handleEdit = async (talk: SmallTalk, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingTalk(talk);
  };

  const handleUpdate = async (talk: SmallTalk) => {
    try {
      await updateSmallTalk(talk.talk_id, {
        eng_sentence: talk.eng_sentence,
        kor_sentence: talk.kor_sentence,
        parenthesis: talk.parenthesis,
        tag: talk.tag
      });
      setEditingTalk(null);
      onUpdate?.();
    } catch (error) {
      console.error('Failed to update small talk:', error);
      alert('수정에 실패했습니다.');
    }
  };

  if (!smallTalks || !Array.isArray(smallTalks)) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 text-gray-500 text-center">
        No small talks available
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {smallTalks.map((talk) => (
        <div
          key={talk.talk_id}
          className={`p-4 rounded-lg border cursor-pointer transition-colors ${
            selectedTalkId === talk.talk_id
              ? 'bg-blue-50 border-blue-200'
              : 'bg-white border-gray-200 hover:bg-gray-50'
          }`}
          onClick={() => onSelect(talk)}
        >
          <div className="flex items-start gap-3">
            <div className="flex-1">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-gray-900 font-medium">{talk.eng_sentence}</p>
                  <p className="text-gray-600 mt-1">{talk.kor_sentence}</p>
                  {talk.parenthesis && (
                    <p className="text-gray-500 text-sm mt-2 italic">({talk.parenthesis})</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={(e) => handleEdit(talk, e)}
                    className="p-2 text-gray-400 hover:text-blue-500 transition-colors"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => handleDelete(talk.talk_id, e)}
                    disabled={isDeleting === talk.talk_id}
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                  {talk.tag}
                </span>
                <span className="text-gray-400 text-xs">
                  {new Date(talk.update_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      ))}

      {editingTalk && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg w-full max-w-lg">
            <h3 className="text-lg font-semibold mb-4">스몰톡 수정</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">영어 문장</label>
                <input
                  type="text"
                  value={editingTalk.eng_sentence}
                  onChange={e => setEditingTalk({...editingTalk, eng_sentence: e.target.value})}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">한글 문장</label>
                <input
                  type="text"
                  value={editingTalk.kor_sentence || ''}
                  onChange={e => setEditingTalk({...editingTalk, kor_sentence: e.target.value})}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">부가 설명</label>
                <input
                  type="text"
                  value={editingTalk.parenthesis || ''}
                  onChange={e => setEditingTalk({...editingTalk, parenthesis: e.target.value})}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">태그</label>
                <input
                  type="text"
                  value={editingTalk.tag || ''}
                  onChange={e => setEditingTalk({...editingTalk, tag: e.target.value})}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setEditingTalk(null)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  취소
                </button>
                <button
                  type="button"
                  onClick={() => handleUpdate(editingTalk)}
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