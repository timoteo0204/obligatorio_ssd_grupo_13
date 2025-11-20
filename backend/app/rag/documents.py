import pandas as pd
from langchain.schema import Document
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def dataframes_to_documents(dataframes: Dict[str, pd.DataFrame]) -> List[Document]:
    """
    Convierte los DataFrames en documentos de LangChain de forma simple.
    Cada fila del DataFrame se convierte en una línea de texto.
    """
    import time
    
    logger.info("Starting dataframes to documents conversion...")
    start_time = time.time()
    documents = []
    
    # Procesar cada DataFrame
    for sheet_name, df in dataframes.items():
        if df is None or df.empty:
            logger.info(f"Skipping empty sheet: '{sheet_name}'")
            continue
            
        logger.info(f"Processing sheet '{sheet_name}' with {len(df)} rows...")
        sheet_start = time.time()
        
        # Convertir cada fila a texto simple
        for idx, row in df.iterrows():
            # Crear una línea de texto con todos los valores de la fila
            row_text_parts = []
            for col_name, value in row.items():
                if pd.notna(value):
                    row_text_parts.append(f"{col_name}: {value}")
            
            if row_text_parts:
                page_content = ", ".join(row_text_parts)
                
                metadata = {
                    'source': sheet_name,
                    'row': int(idx)
                }
                
                documents.append(Document(page_content=page_content, metadata=metadata))
        
        sheet_time = time.time() - sheet_start
        logger.info(f"Sheet '{sheet_name}' processed in {sheet_time:.2f}s")
    
    total_time = time.time() - start_time
    logger.info(f"Document conversion completed: Created {len(documents)} documents in {total_time:.2f}s")
    
    return documents
