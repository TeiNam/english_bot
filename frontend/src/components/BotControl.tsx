import React, { useEffect, useState } from 'react';
import { getBotStatus, toggleBot, sendMessageNow } from '../api/index';
import { Power, Send, Activity } from 'lucide-react';
import { BotStatus } from '../types/api';

interface BotStatus {
  running: boolean;
  jobs?: any[];
}

export function BotControl() {
  const [status, setStatus] = useState<BotStatus>({ running: false });
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    fetchStatus();
    // Poll status every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const data = await getBotStatus();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch bot status:', error);
    }
  };

  const handleToggle = async () => {
    setIsLoading(true);
    try {
      await toggleBot(!status.running);
      await fetchStatus();
    } catch (error) {
      console.error('Failed to toggle bot:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendNow = async () => {
    setIsSending(true);
    try {
      await sendMessageNow();
      await fetchStatus();
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border mb-6">
      <div className="p-4 border-b">
        <h3 className="text-lg font-semibold text-gray-900">Bot Control Panel</h3>
      </div>
      
      <div className="p-4 space-y-4">
        {/* Status Display */}
        <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
          <Activity className={`w-5 h-5 ${status.running ? 'text-green-500' : 'text-gray-400'}`} />
          <div className="flex-1">
            <p className="font-medium text-gray-900">Current Status</p>
            <p className="text-sm text-gray-600">
              {status.running ? 'Bot is active and running' : 'Bot is currently stopped'}
            </p>
            {status.jobs && status.jobs.length > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                Active jobs: {status.jobs.length}
              </p>
            )}
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleToggle}
            disabled={isLoading}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-white ${
              status.running
                ? 'bg-red-500 hover:bg-red-600'
                : 'bg-green-500 hover:bg-green-600'
            } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <Power className="w-4 h-4" />
            {isLoading ? 'Processing...' : status.running ? 'Stop Bot' : 'Start Bot'}
          </button>

          <button
            onClick={handleSendNow}
            disabled={isSending || !status.running}
            className={`flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600
              ${(isSending || !status.running) ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <Send className="w-4 h-4" />
            {isSending ? 'Sending...' : 'Send Message Now'}
          </button>
        </div>

        {/* Status Message */}
        {!status.running && (
          <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg">
            Note: Bot must be running to send immediate messages
          </p>
        )}
      </div>
    </div>
  );
}