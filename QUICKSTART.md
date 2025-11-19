# Quick Start Guide

Guía rápida para poner en marcha el chatbot Retail 360.

## Prerequisitos

- Docker y Docker Compose instalados
- Al menos 8GB de RAM disponible
- 10GB de espacio en disco

## Inicio Rápido (5 minutos)

### Opción 1: Script Automático

```bash
./start.sh
```

Este script:
1. Verifica que Docker esté instalado
2. Genera datos de ejemplo si no existe dataset.xlsx
3. Levanta todos los servicios
4. Descarga el modelo llama3
5. Inicia el sistema completo

### Opción 2: Manual

```bash
# 1. Generar datos de ejemplo (o coloca tu Excel)
python3 generate_sample_data.py

# 2. Levantar servicios
docker compose up --build -d

# 3. Descargar modelo
docker exec retail360-ollama ollama pull llama3

# 4. Verificar que todo funciona
curl http://localhost:8000/api/health
```

## Acceso

Una vez iniciado:

- **Aplicación Web**: http://localhost
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Primeros Pasos

1. Abre http://localhost en tu navegador
2. Espera a que cargue la interfaz del chat
3. Escribe una pregunta, por ejemplo:
   - "¿Cuántas ventas hubo en marzo de 2023?"
   - "¿Cuál fue el cliente que más compró?"
   - "¿Cuál es el producto más vendido?"
4. El chatbot responderá basándose en los datos del Excel

## Ver Logs

```bash
# Todos los servicios
docker compose logs -f

# Solo backend
docker compose logs -f backend

# Solo Ollama
docker compose logs -f ollama
```

## Detener Servicios

```bash
docker compose down
```

## Problemas Comunes

### El backend no inicia
**Solución**: Verifica que exista `data/dataset.xlsx`
```bash
ls -la data/dataset.xlsx
```

### Ollama da error de memoria
**Solución**: Ajusta la memoria de Docker a al menos 8GB

### El modelo tarda mucho en responder
**Solución**: La primera vez es más lento. Las siguientes son más rápidas.

### Puerto 80 ya está en uso
**Solución**: Cambia el puerto en docker-compose.yml:
```yaml
frontend:
  ports:
    - "8080:80"  # Cambiar 80 por otro puerto
```

## Reiniciar el Índice

Si actualizas el Excel:

```bash
curl -X POST http://localhost:8000/api/rebuild-index
```

## Usar tu Propio Dataset

1. Coloca tu Excel en `data/dataset.xlsx`
2. Debe tener las hojas: Ventas, Clientes (opcional), Productos (opcional)
3. Reinicia los servicios:
   ```bash
   docker compose restart backend
   ```

## Siguiente Paso

Lee [EJEMPLOS_PREGUNTAS.md](EJEMPLOS_PREGUNTAS.md) para ver ejemplos de preguntas que puedes hacer.
