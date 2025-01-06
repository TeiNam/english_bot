import React from 'react';
import { SmallTalk } from '../types/api';
import { MessageSquare } from 'lucide-react';

interface Props {
  smallTalks: SmallTalk[];
  onSelect: (talk: SmallTalk) => void;
  selectedTalkId?: number;
}

export function SmallTalkList({ smallTalks, onSelect, selectedTalkId }: Props) {
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
            <MessageSquare className="w-5 h-5 text-blue-500 mt-1" />
            <div className="flex-1">
              <p className="text-gray-900 font-medium">{talk.eng_sentence}</p>
              <p className="text-gray-600 mt-1">{talk.kor_sentence}</p>
              {talk.parenthesis && (
                <p className="text-gray-500 text-sm mt-2 italic">({talk.parenthesis})</p>
              )}
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
    </div>
  );
}