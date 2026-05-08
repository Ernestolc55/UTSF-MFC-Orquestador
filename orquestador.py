name: Orquestador UTSF-MFC

on:
  workflow_dispatch:

jobs:
  investigar:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repositorio
        uses: actions/checkout@v4
      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Instalar dependencias
        run: |
          pip install --upgrade pip
          pip install requests psycopg2-binary
      - name: Listar archivos (verificar que orquestador.py existe)
        run: ls -la
      - name: Ejecutar orquestador con verbose
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          NEON_DB_URL: ${{ secrets.NEON_DB_URL }}
        run: |
          python -u orquestador.py
