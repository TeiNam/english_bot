import React, { useState } from 'react';
import { SmallTalk } from '../types/api';
import { MessageSquare, Trash2 } from 'lucide-react';
import { deleteSmallTalk } from '../api';

interface Props {
  smallTalks: SmallTalk[];
  onSelect: (talk: SmallTalk) => void;
  selectedTalkId?: number;
  onDelete?: () => void;  // 삭제 후 리스트 새로고침을 위한 콜백
}

export function SmallTalkList({ smallTalks = [], onSelect, selectedTalkId, onDelete }: Props) {
  const [isDeleting, setIsDeleting] = useState<number | null>(null);

  const handleDelete = async (talkId: number, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!window.confirm('정말 이 스몰톡을 삭제하시겠습니까?')) {
      return;
    }

    try {
      setIsDeleting(talkId);
      await deleteSmallTalk(talkId);
      onDelete?.();  // 삭제 후 리스트 새로고침
    } catch (error) {
      // 실제로 삭제는 됐지만 커넥션 close에서 에러가 발생한 경우
      console.error('Error occurred but deletion might have succeeded:', error);
      onDelete?.();  // 리스트를 새로고침해서 확인
    } finally {
      setIsDeleting(null);
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
                </div>
                <button
                  onClick={(e) => handleDelete(talk.talk_id, e)}
                  disabled={isDeleting === talk.talk_id}
                  className="p-2 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              {/* ... 나머지 렌더링 코드 ... */}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}