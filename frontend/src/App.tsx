import React, { useEffect, useState } from 'react';
import { SmallTalk, Answer } from './types/api';
import { fetchSmallTalks, fetchAnswers } from './api/index';
import { SmallTalkList } from './components/SmallTalkList';
import { AnswerList } from './components/AnswerList';
import { CreateSmallTalk } from './components/CreateSmallTalk';
import { CreateAnswer } from './components/CreateAnswer';
import { BotControl } from './components/BotControl';
import { Pagination } from './components/Pagination';

function App() {
 const [smallTalks, setSmallTalks] = useState<SmallTalk[]>([]);
 const [selectedTalk, setSelectedTalk] = useState<SmallTalk | null>(null);
 const [answers, setAnswers] = useState<Answer[]>([]);
 const [currentTag, setCurrentTag] = useState<string>('');
 const [currentPage, setCurrentPage] = useState(1);
 const [totalItems, setTotalItems] = useState(0);
 const [isLoading, setIsLoading] = useState(false);
 const ITEMS_PER_PAGE = 10;

 const loadSmallTalks = async (tag?: string, page = 1) => {
   try {
     setIsLoading(true);
     const offset = (page - 1) * ITEMS_PER_PAGE;
     console.log('Fetching small talks with params:', { tag, limit: ITEMS_PER_PAGE, offset });

     const { items, total } = await fetchSmallTalks(tag, ITEMS_PER_PAGE, offset);
     setSmallTalks(items);
     setTotalItems(total);
   } catch (error) {
     console.error('Failed to fetch small talks:', error);
     setSmallTalks([]);
     setTotalItems(0);
   } finally {
     setIsLoading(false);
   }
 };

 const loadAnswers = async (talkId: number) => {
   try {
     const data = await fetchAnswers(talkId);
     setAnswers(data);
   } catch (error) {
     console.error('Failed to fetch answers:', error);
   }
 };

 useEffect(() => {
   loadSmallTalks(currentTag, currentPage);
 }, [currentTag, currentPage]);

 const handleTalkSelect = async (talk: SmallTalk) => {
   setSelectedTalk(talk);
   await loadAnswers(talk.talk_id);
 };

 const handleSmallTalkSuccess = () => {
   setCurrentPage(1);
   loadSmallTalks(currentTag, 1);
 };

 const handleAnswerSuccess = () => {
   if (selectedTalk) {
     loadAnswers(selectedTalk.talk_id);
   }
 };

 const handlePageChange = (page: number) => {
   setCurrentPage(page);
 };

 const handleSmallTalkDelete = () => {
  loadSmallTalks(currentTag, currentPage);
  // answer 관련 상태 초기화
  setSelectedTalk(null);
  setAnswers([]);
};

 return (
   <div className="min-h-screen bg-gray-100">
     <div className="container mx-auto px-4 py-8">
       <h1 className="text-3xl font-bold text-gray-900 mb-8">English Bot Manager</h1>

       <div className="mb-8">
         <h2 className="text-2xl font-semibold text-gray-800 mb-4">Bot Control</h2>
         <BotControl />
       </div>

       <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
         <div>
           <div className="flex justify-between items-center mb-4">
             <h2 className="text-2xl font-semibold text-gray-800">Small Talks</h2>
             <div className="flex items-center gap-2">
               {isLoading && (
                 <span className="text-sm text-gray-500">Loading...</span>
               )}
               <input
                 type="text"
                 placeholder="Filter by tag..."
                 value={currentTag}
                 onChange={(e) => {
                   setCurrentTag(e.target.value);
                   setCurrentPage(1);
                 }}
                 className="px-3 py-2 border rounded-md"
               />
             </div>
           </div>
           <CreateSmallTalk onSuccess={handleSmallTalkSuccess} />
           <SmallTalkList
             smallTalks={smallTalks}
             onSelect={handleTalkSelect}
             selectedTalkId={selectedTalk?.talk_id}
             onDelete={handleSmallTalkDelete}
             onUpdate={handleSmallTalkSuccess}
           />
           <Pagination
             currentPage={currentPage}
             totalItems={totalItems}
             itemsPerPage={ITEMS_PER_PAGE}
             onPageChange={handlePageChange}
           />
         </div>

         <div>
           <h2 className="text-2xl font-semibold text-gray-800 mb-4">Answers</h2>
           {selectedTalk ? (
             <>
               <CreateAnswer
                 talkId={selectedTalk.talk_id}
                 onSuccess={handleAnswerSuccess}
               />
               <AnswerList
                 answers={answers}
                 onDelete={() => {
                   if (selectedTalk) {
                     loadAnswers(selectedTalk.talk_id);
                   }
                 }}
                 onUpdate={() => {
                   if (selectedTalk) {
                     loadAnswers(selectedTalk.talk_id);
                   }
                 }}
               />
             </>
           ) : (
             <div className="bg-white p-8 rounded-lg border text-center text-gray-500">
               Select a small talk to view and manage answers
             </div>
           )}
         </div>
       </div>
     </div>
   </div>
 );
}

export default App;