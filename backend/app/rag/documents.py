import pandas as pd
from langchain.schema import Document
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter

import logging

logger = logging.getLogger(__name__)


def dataframes_to_documents(dataframes: List[pd.DataFrame]):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(dataframes)
    return chunks
