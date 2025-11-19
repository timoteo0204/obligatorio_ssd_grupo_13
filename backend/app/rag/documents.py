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
    documents = []
    
    # Procesar cada DataFrame
    for sheet_name, df in dataframes.items():
        if df is None or df.empty:
            continue
            
        logger.info(f"Procesando hoja '{sheet_name}' con {len(df)} filas")
        
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
    
    logger.info(f"Creados {len(documents)} documentos desde los DataFrames")
    
    return documents
