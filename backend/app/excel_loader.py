import pandas as pd
from datetime import datetime
from typing import Dict, Any
from langchain_core.documents import Document

import logging

logger = logging.getLogger(__name__)


class ExcelLoader:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.ventas_df = None
        self.clientes_df = None
        self.productos_df = None
        self.ventas_completas_df = None
        
    def load(self):
        """Carga el Excel con layout fijo y genera documentos enriquecidos.
        Hojas esperadas: Productos, Clientes, Ventas.
        Devuelve lista de Document listos para embedding.
        """
        xls = pd.ExcelFile(self.excel_path)

        try:
            self.productos_df = pd.read_excel(xls, "Productos")
        except Exception as e:
            logger.warning(f"No se pudo leer hoja Productos: {e}")
            self.productos_df = pd.DataFrame()
        try:
            self.clientes_df = pd.read_excel(xls, "Clientes")
        except Exception as e:
            logger.warning(f"No se pudo leer hoja Clientes: {e}")
            self.clientes_df = pd.DataFrame()
        try:
            self.ventas_df = pd.read_excel(xls, "Ventas")
        except Exception as e:
            logger.warning(f"No se pudo leer hoja Ventas: {e}")
            self.ventas_df = pd.DataFrame()

        self._process_productos()
        self._process_clientes()
        self._process_ventas()

        self._join_tables()

        documentos = []

        # Productos
        if self.productos_df is not None and not self.productos_df.empty:
            for row in self.productos_df.to_dict(orient="records"):
                contenido = (
                    "[PRODUCTO]\n"
                    f"IdProducto: {row.get('IdProducto')}\n"
                    f"NombreProducto: {row.get('NombreProducto')}\n"
                    f"Categoria: {row.get('Categoria')}\n"
                    f"Precio: {row.get('Precio')}\n"
                )
                documentos.append(
                    Document(
                        page_content=contenido,
                        metadata={"tipo": "producto", "id": row.get("IdProducto")}
                    )
                )

        # Clientes
        if self.clientes_df is not None and not self.clientes_df.empty:
            for row in self.clientes_df.to_dict(orient="records"):
                contenido = (
                    "[CLIENTE]\n"
                    f"IdCliente: {row.get('IdCliente')}\n"
                    f"NombreCliente: {row.get('NombreCliente')}\n"
                    f"Ciudad: {row.get('Ciudad')}\n"
                )
                documentos.append(
                    Document(
                        page_content=contenido,
                        metadata={"tipo": "cliente", "id": row.get("IdCliente")}
                    )
                )

        # Ventas completas 
        if self.ventas_completas_df is not None and not self.ventas_completas_df.empty:
            for row in self.ventas_completas_df.to_dict(orient="records"):
                fecha = row.get("FechaVenta") or row.get("fecha")
                if isinstance(fecha, datetime):
                    fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    fecha_str = str(fecha)
                contenido = (
                    "[VENTA]\n"
                    f"IdVenta: {row.get('IdVenta')}\n"
                    f"IdProducto: {row.get('IdProducto') or row.get('IdProducto_producto')}\n"
                    f"IdCliente: {row.get('IdCliente') or row.get('IdClient') or row.get('IdCliente_cliente')}\n"
                    f"Producto: {row.get('NombreProducto')}\n"
                    f"CategoriaProducto: {row.get('Categoria')}\n"
                    f"Cliente: {row.get('NombreCliente')}\n"
                    f"CiudadCliente: {row.get('Ciudad')}\n"
                    f"Cantidad: {row.get('Cantidad')}\n"
                    f"FechaVenta: {fecha_str}\n"
                    f"Año: {row.get('año')}\n"
                    f"Mes: {row.get('mes')}\n"
                    f"Dia: {row.get('dia')}\n"
                    f"Total: {row.get('Total')}\n"
                )
                documentos.append(
                    Document(
                        page_content=contenido,
                        metadata={
                            "tipo": "venta",
                            "id": row.get("IdVenta"),
                            "id_producto": row.get('IdProducto') or row.get('IdProducto_producto'),
                            "id_cliente": row.get('IdCliente') or row.get('IdClient') or row.get('IdCliente_cliente')
                        }
                    )
                )
        else:
            # Si no hay join usamos la tabla ventas cruda
            if self.ventas_df is not None and not self.ventas_df.empty:
                for row in self.ventas_df.to_dict(orient="records"):
                    fecha = row.get("FechaVenta")
                    contenido = (
                        "[VENTA]\n"
                        f"IdVenta: {row.get('IdVenta')}\n"
                        f"IdProducto: {row.get('IdProducto')}\n"
                        f"IdCliente: {row.get('IdCliente') or row.get('IdClient')}\n"
                        f"Cantidad: {row.get('Cantidad')}\n"
                        f"FechaVenta: {fecha}\n"
                    )
                    documentos.append(
                        Document(
                            page_content=contenido,
                            metadata={"tipo": "venta", "id": row.get("IdVenta")}
                        )
                    )

        logger.info(f"Generados {len(documentos)} documentos enriquecidos desde Excel")
        return documentos
    
    def _process_productos(self):
        """Procesa y normaliza el DataFrame de productos."""
        if self.productos_df is None or self.productos_df.empty:
            return
        
        logger.info(f"Columnas de Productos: {list(self.productos_df.columns)}")
        
        # Convertir columnas numéricas (Precio)
        precio_col = None
        for col in self.productos_df.columns:
            if 'precio' in col.lower() or 'price' in col.lower():
                precio_col = col
                try:
                    self.productos_df[col] = pd.to_numeric(self.productos_df[col], errors='coerce')
                except:
                    pass
    
    def _process_clientes(self):
        """Procesa y normaliza el DataFrame de clientes."""
        if self.clientes_df is None or self.clientes_df.empty:
            return
        
        logger.info(f"Columnas de Clientes: {list(self.clientes_df.columns)}")
    
    def _process_ventas(self):
        """Procesa y normaliza el DataFrame de ventas."""
        if self.ventas_df is None or self.ventas_df.empty:
            return
        
        logger.info(f"Columnas de Ventas: {list(self.ventas_df.columns)}")
        
        # Convertir columnas de fecha
        date_columns = [col for col in self.ventas_df.columns 
                       if 'fecha' in col.lower() or 'date' in col.lower()]
        for col in date_columns:
            try:
                self.ventas_df[col] = pd.to_datetime(self.ventas_df[col], errors='coerce')
                # Agregar columnas derivadas
                self.ventas_df['año'] = self.ventas_df[col].dt.year
                self.ventas_df['mes'] = self.ventas_df[col].dt.month
                self.ventas_df['dia'] = self.ventas_df[col].dt.day
                self.ventas_df['mes_nombre'] = self.ventas_df[col].dt.strftime('%B')
            except Exception as e:
                logger.warning(f"Error procesando fecha {col}: {e}")
        
        # Convertir Cantidad a numérico
        cantidad_col = None
        for col in self.ventas_df.columns:
            if 'cantidad' in col.lower() or 'quantity' in col.lower():
                cantidad_col = col
                try:
                    self.ventas_df[col] = pd.to_numeric(self.ventas_df[col], errors='coerce')
                except:
                    pass
    
    def _join_tables(self):
        """
        Combina las tres tablas mediante JOIN para crear una vista completa.
        Ventas JOIN Clientes ON IdCliente JOIN Productos ON IdProducto
        """
        if self.ventas_df is None or self.ventas_df.empty:
            logger.warning("No hay ventas para procesar")
            self.ventas_completas_df = pd.DataFrame()
            return
        
        result = self.ventas_df.copy()
        
        # JOIN con Clientes
        if self.clientes_df is not None and not self.clientes_df.empty:
            cliente_id_col_ventas = None
            cliente_id_col_clientes = None
            
            for col in result.columns:
                if 'idcliente' in col.lower():
                    cliente_id_col_ventas = col
                    break
            
            for col in self.clientes_df.columns:
                if 'idcliente' in col.lower():
                    cliente_id_col_clientes = col
                    break
            
            if cliente_id_col_ventas and cliente_id_col_clientes:
                result = result.merge(
                    self.clientes_df,
                    left_on=cliente_id_col_ventas,
                    right_on=cliente_id_col_clientes,
                    how='left',
                    suffixes=('', '_cliente')
                )
                logger.info(f"JOIN con Clientes completado: {len(result)} filas")
        
        # JOIN con Productos
        if self.productos_df is not None and not self.productos_df.empty:
            producto_id_col_ventas = None
            producto_id_col_productos = None
            
            for col in result.columns:
                if 'idproducto' in col.lower():
                    producto_id_col_ventas = col
                    break
            
            for col in self.productos_df.columns:
                if 'idproducto' in col.lower():
                    producto_id_col_productos = col
                    break
            
            if producto_id_col_ventas and producto_id_col_productos:
                result = result.merge(
                    self.productos_df,
                    left_on=producto_id_col_ventas,
                    right_on=producto_id_col_productos,
                    how='left',
                    suffixes=('', '_producto')
                )
                logger.info(f"JOIN con Productos completado: {len(result)} filas")
        
        # Calcular Total (Cantidad * Precio)
        cantidad_col = None
        precio_col = None
        
        for col in result.columns:
            if 'cantidad' in col.lower():
                cantidad_col = col
            if 'precio' in col.lower() and 'producto' not in col.lower():
                precio_col = col
        
        if cantidad_col and precio_col:
            result['Total'] = result[cantidad_col] * result[precio_col]
            logger.info("Columna Total calculada")
        
        self.ventas_completas_df = result
        logger.info(f"Tabla completa generada con {len(result)} filas y {len(result.columns)} columnas")
