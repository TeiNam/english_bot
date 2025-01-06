import React, { useState } from 'react';
import { createSmallTalk } from '../api/index';
import { Plus } from 'lucide-react';

interface Props {
  onSuccess: () => void;
}

export function CreateSmallTalk({ onSuccess }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({
    eng_sentence: '',
    kor_sentence: '',
    parenthesis: '',
    tag: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createSmallTalk(formData);
      setFormData({ eng_sentence: '', kor_sentence: '', parenthesis: '', tag: '' });
      setIsOpen(false);
      onSuccess();
    } catch (error) {
      console.error('Failed to create small talk:', error);
    }
  };

  return (
    <div className="mb-6">
      {!isOpen ? (
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Add New Small Talk
        </button>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4 bg-white p-6 rounded-lg border">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              English Sentence
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
              Korean Sentence
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Parenthesis
            </label>
            <input
              type="text"
              value={formData.parenthesis}
              onChange={(e) =>
                setFormData({ ...formData, parenthesis: e.target.value })
              }
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tag
            </label>
            <input
              type="text"
              value={formData.tag}
              onChange={(e) => setFormData({ ...formData, tag: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
              required
            />
          </div>
          <div className="flex gap-3">
            <button
              type="submit"
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
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