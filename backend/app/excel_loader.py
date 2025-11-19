import pandas as pd
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ExcelLoader:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.ventas_df = None
        self.clientes_df = None
        self.productos_df = None
        self.ventas_completas_df = None
        
    def load(self) -> Dict[str, pd.DataFrame]:
        """
        Carga y procesa el archivo Excel con las hojas de ventas, clientes y productos.
        
        Estructura esperada:
        - Productos: IdProducto, NombreProducto, Categoria, Precio
        - Clientes: IdCliente, NombreCliente, Ciudad
        - Ventas: IdVenta, IdProducto, IdCliente, Cantidad, FechaVenta
        """
        logger.info(f"Cargando Excel desde: {self.excel_path}")
        
        try:
            # Cargar las hojas
            excel_file = pd.ExcelFile(self.excel_path)
            
            # Identificar hojas disponibles
            logger.info(f"Hojas disponibles: {excel_file.sheet_names}")
            
            # Cargar hojas (buscar nombres en español e inglés)
            # Productos
            if 'Productos' in excel_file.sheet_names:
                self.productos_df = pd.read_excel(excel_file, 'Productos')
            elif 'productos' in excel_file.sheet_names:
                self.productos_df = pd.read_excel(excel_file, 'productos')
            elif 'Products' in excel_file.sheet_names:
                self.productos_df = pd.read_excel(excel_file, 'Products')
            else:
                logger.warning("No se encontró hoja de Productos")
                self.productos_df = pd.DataFrame()
            
            # Clientes
            if 'Clientes' in excel_file.sheet_names:
                self.clientes_df = pd.read_excel(excel_file, 'Clientes')
            elif 'clientes' in excel_file.sheet_names:
                self.clientes_df = pd.read_excel(excel_file, 'clientes')
            elif 'Customers' in excel_file.sheet_names:
                self.clientes_df = pd.read_excel(excel_file, 'Customers')
            else:
                logger.warning("No se encontró hoja de Clientes")
                self.clientes_df = pd.DataFrame()
            
            # Ventas
            if 'Ventas' in excel_file.sheet_names:
                self.ventas_df = pd.read_excel(excel_file, 'Ventas')
            elif 'ventas' in excel_file.sheet_names:
                self.ventas_df = pd.read_excel(excel_file, 'ventas')
            elif 'Sales' in excel_file.sheet_names:
                self.ventas_df = pd.read_excel(excel_file, 'Sales')
            else:
                # Intentar con la primera hoja si no se encuentra
                logger.warning("No se encontró hoja de Ventas, usando primera hoja")
                self.ventas_df = pd.read_excel(excel_file, 0)
            
            # Procesar dataframes
            self._process_productos()
            self._process_clientes()
            self._process_ventas()
            
            # Combinar las tablas mediante JOIN
            self._join_tables()
            
            logger.info(f"Excel cargado: {len(self.ventas_df)} ventas, "
                       f"{len(self.clientes_df)} clientes, {len(self.productos_df)} productos")
            
            return {
                'ventas': self.ventas_df,
                'clientes': self.clientes_df,
                'productos': self.productos_df,
                'ventas_completas': self.ventas_completas_df
            }
            
        except Exception as e:
            logger.error(f"Error al cargar Excel: {e}")
            raise
    
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
        
        # Convertir columnas de fecha (FechaVenta)
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
        
        # Copiar ventas
        result = self.ventas_df.copy()
        
        # JOIN con Clientes
        if self.clientes_df is not None and not self.clientes_df.empty:
            # Identificar columnas de ID de cliente
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
            # Identificar columnas de ID de producto
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
