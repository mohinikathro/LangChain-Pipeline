{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "304beda9",
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "from dotenv import load_dotenv\n",
    "\n",
    "load_dotenv()\n",
    "\n",
    "os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')\n",
    "os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')\n",
    "os.environ['LANGCHAIN_TRACING_V2'] = 'true'\n",
    "os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "id": "d249b904",
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "/Users/mohinikathrotiya/Desktop/Langchain/lcenv/lib/python3.13/site-packages/tqdm/auto.py:21: TqdmWarning: IProgress not found. Please update jupyter and ipywidgets. See https://ipywidgets.readthedocs.io/en/stable/user_install.html\n",
      "  from .autonotebook import tqdm as notebook_tqdm\n"
     ]
    }
   ],
   "source": [
    "from fastapi import FastAPI, Query\n",
    "from pydantic import BaseModel\n",
    "from typing import Dict\n",
    "from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder\n",
    "from langchain_core.runnables.history import RunnableWithMessageHistory\n",
    "from langchain_community.chat_message_histories import ChatMessageHistory\n",
    "from langchain_openai import ChatOpenAI"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "id": "5c4a89ba",
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "/Users/mohinikathrotiya/Desktop/Langchain/lcenv/lib/python3.13/site-packages/IPython/core/interactiveshell.py:3641: UserWarning: WARNING! mode is not default parameter.\n",
      "                mode was transferred to model_kwargs.\n",
      "                Please confirm that mode is what you intended.\n",
      "  if await self.run_code(code, result, async_=asy):\n"
     ]
    }
   ],
   "source": [
    "# ---------------------------\n",
    "# 1) Model setup\n",
    "# ---------------------------\n",
    "\n",
    "model = ChatOpenAI(mode = 'gpt-4o-mini', temperature = 0.2)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "d1971acd",
   "metadata": {},
   "outputs": [],
   "source": [
    "# ---------------------------\n",
    "# 2) Prompt setup\n",
    "# ---------------------------\n",
    "\n",
    "prompt = ChatPromptTemplate.from_messages(\n",
    "    [\n",
    "        ('system', 'You are a helpful AI Assiatant. Use teh chat history to answer correctly.'),\n",
    "        MessagesPlaceholder('history'),\n",
    "        ('human', '{input}'),\n",
    "    ]\n",
    ")\n",
    "\n",
    "chain = prompt | model"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "id": "8a5f1bc1",
   "metadata": {},
   "outputs": [],
   "source": [
    "# --------------------------------------\n",
    "# 3) In-memory store for multiple users\n",
    "# --------------------------------------\n",
    "\n",
    "store: Dict[str, ChatMessageHistory] = {}\n",
    "\n",
    "def get_session_history(session_id: str) -> ChatMessageHistory:\n",
    "    if session_id not in store:\n",
    "        store[session_id] = ChatMessageHistory()\n",
    "    return store[session_id]"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "id": "2f7d77e0",
   "metadata": {},
   "outputs": [],
   "source": [
    "# ------------------------------\n",
    "# 4) Wrappinf chain with memory\n",
    "# ------------------------------\n",
    "\n",
    "with_history  = RunnableWithMessageHistory(\n",
    "    chain,\n",
    "    get_session_history,\n",
    "    input_messages_key= 'input',\n",
    "    history_messages_key= 'history'\n",
    ")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 10,
   "id": "81b2133a",
   "metadata": {},
   "outputs": [],
   "source": [
    "# ---------------------------\n",
    "# 5) FastAPI setup\n",
    "# ---------------------------\n",
    "\n",
    "app = FastAPI(title= 'Multi-User Memory Chatbot')\n",
    "\n",
    "class ChatRequet(BaseModel):\n",
    "    message: str\n",
    "\n",
    "class ChatResponse(BaseModel):\n",
    "    reply: str\n",
    "\n",
    "\n",
    "@app.post('/chat', response_model = ChatResponse)\n",
    "\n",
    "def chat_endpoint(req: ChatRequet, session_id: str = Query(..., description= 'Unique user ID')):\n",
    "    \"\"\"\n",
    "    Send a message to the bot as a specific user.\n",
    "    session_id ensures separate memory per user.\n",
    "    \"\"\"\n",
    "    config = {'configurable': {'session_id': session_id}}\n",
    "    result = with_history.invoke({'input': req.message}, config=config)\n",
    "    return ChatResponse(reply = result.content)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "id": "ff85a34f",
   "metadata": {},
   "outputs": [],
   "source": [
    "# ------------------------------\n",
    "# 6) Endpoint to inspect memory\n",
    "# ------------------------------\n",
    "\n",
    "@app.get(\"/memory/{session_id}\")\n",
    "def memory_endpoint(session_id: str):\n",
    "    \"\"\"View the stored messages for a session.\"\"\"\n",
    "    if session_id not in store:\n",
    "        return {\"messages\": []}\n",
    "    return {\"messages\": [{\"type\": m.type, \"content\": m.content} for m in store[session_id].messages]}"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "3beaffc3",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "lcenv (3.13.9)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.13.9"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
