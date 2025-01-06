import React, { useState } from 'react';
import { createAnswer } from '../api/index';
import { Plus } from 'lucide-react';

interface Props {
  talkId: number;
  onSuccess: () => void;
}

export function CreateAnswer({ talkId, onSuccess }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({
    eng_sentence: '',
    kor_sentence: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createAnswer({ ...formData, talk_id: talkId });
      setFormData({ eng_sentence: '', kor_sentence: '' });
      setIsOpen(false);
      onSuccess();
    } catch (error) {
      console.error('Failed to create answer:', error);
    }
  };

  return (
    <div className="mb-6">
      {!isOpen ? (
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Add New Answer
        </button>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4 bg-white p-6 rounded-lg border">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              English Answer
            </label>
            <input
              type="text"
              value={formData.eng_sentence}
              onChange={(e) =>
                setFormData({ ...formData, eng_sentence: e.target.value })
              }
              className="w-full px-3 py-2 border rounded-md"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Korean Answer
            </label>
            <input
              type="text"
              value={formData.kor_sentence}
              onChange={(e) =>
                setFormData({ ...formData, kor_sentence: e.target.value })
              }
              className="w-full px-3 py-2 border rounded-md"
              required
            />
          </div>
          <div className="flex gap-3">
            <button
              type="submit"
              className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}