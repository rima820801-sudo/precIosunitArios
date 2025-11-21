# Modulos del repositorio

## Backend (`catalogos/`)
- `app.py`: punto de entrada y único módulo de la app. Configura Flask, SQLAlchemy, CORS y las variables de entorno, define los modelos y utilidades (`decimal_field`, heurísticas de IA, generación de PDF) y expone los endpoints `/api/*`.
- `seed_data.py`: se ejecuta desde el contexto de la app para poblar constantes FASAR, catálogos básicos y un concepto de ejemplo cuando se arranca con `python app.py`.
- `test_app.py`: pruebas unitarias con `pytest` que levantan la app en modo testing, crean una base SQLite en memoria y validan funciones clave como `calcular_pu` y `match_mano_obra`.
- `nota_venta_template.html`: template histórico de la nota de venta; se conserva como referencia aunque el flujo actual usa ReportLab.
- `migrations/`: espacio para scripts de Alembic (aun sin migraciones automáticas).
- `requirements.txt`: dependencias actuales (`flask`, `flask-sqlalchemy`, `flask-cors`, `python-dotenv`, `google-generativeai`, `reportlab`, `pytest`).
- `data.sqlite3`: base de datos local que se crea y llena al iniciar la app.
- `__init__.py`, `.env`, `__pycache__`.

## Frontend (`frontend/`)
- `package.json` / `tsconfig*.json` / `vite.config.ts`: configuración de build y scripts (`npm run dev`, `npm run build`, `npm run preview`, y los comandos auxiliares que arrancan el backend desde Node).
- `src/main.tsx`: arranca React con `BrowserRouter` y aplica `styles.css`.
- `src/App.tsx`: orquesta la sesión del usuario, protege rutas y expone `/login`, `/analisis`, `/catalogo`, `/comparador` y `/admin`.
- `src/api/client.ts`: instancia `axios` con `VITE_API_BASE_URL`, `Content-Type: application/json` y `withCredentials`; `apiFetch` reutiliza esta configuración.
- `src/pages/LoginPage.tsx`: formulario de autenticación que propaga la sesión al contexto.
- `src/pages/CatalogoPage.tsx`: vista con datos simulados (materiales, mano de obra, equipos y maquinaria) y controles de UI para crear/eliminar entradas en cada pestaña.
- `src/pages/AnalisisPuPage.tsx`: carga conceptos, lanza peticiones a `/api/ia/chat_apu`, permite editar la matriz con `ConceptoMatrizEditor` y genera notas mediante `NotaVentaModalFixed`.
- `src/pages/ComparadorPage.tsx` y `src/pages/AdminDashboard.tsx`: vistas protegidas que trabajan sobre los datos del backend (comparaciones y administración central).
- `src/components/conceptos/ConceptoMatrizEditor.tsx`: administra las filas de la matriz, sincroniza con `/api/conceptos/calcular_pu`, valida insumos y soporta sugerencias de IA.
- `src/components/conceptos/NotaVentaModal.tsx` y `NotaVentaModalFixed.tsx`: muestran el resultado de la generación de una nota de venta y permiten descargar el PDF backend.
- `src/styles.css`: define el layout global (variables, tablas, tarjetas, modales, grids de acciones).

## Documentos y otros
- Los archivos Markdown (`README.md`, `PROJECT_SUMMARY.md`, `ARCHITECTURE.md`, `API_REFERENCE.md`, `TODOS.md`) concentran la documentacion tecnica y las tareas pendientes.
- El repositorio incluye un entorno virtual (`venv312/`) para ejecutar el backend en Windows, asi como caches de pytest o compilaciones de Vite en `frontend/dist/`.
