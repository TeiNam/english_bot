import React, { useEffect, useState } from 'react';
import { SmallTalk, Answer } from './types/api';
import { fetchSmallTalks, fetchAnswers } from './api/client';
import { SmallTalkList } from './components/SmallTalkList';
import { AnswerList } from './components/AnswerList';
import { CreateSmallTalk } from './components/CreateSmallTalk';
import { CreateAnswer } from './components/CreateAnswer';
import { BotControl } from './components/BotControl';

// ... rest of the file remains the same ...