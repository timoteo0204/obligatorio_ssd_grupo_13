# Sample Excel file structure
# Place your actual dataset.xlsx file here

This directory should contain your Excel file with sales data.

Expected structure (EXACT format):

Sheet "Productos":
  - IdProducto (int)
  - NombreProducto (string)
  - Categoria (string)
  - Precio (numeric)

Sheet "Clientes":
  - IdCliente (int)
  - NombreCliente (string)
  - Ciudad (string)

Sheet "Ventas":
  - IdVenta (int)
  - IdProducto (int, foreign key to Productos)
  - IdCliente (int, foreign key to Clientes)
  - Cantidad (int)
  - FechaVenta (date)

Note: The system will automatically JOIN these tables to create a complete view
with customer names, product names, prices, and calculate totals (Cantidad * Precio)
