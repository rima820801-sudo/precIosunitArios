import os
import json
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.sqlite3")

app = Flask(__name__)

# --- 1. CONFIGURACIÓN DE BASE DE DATOS (INTELIGENTE) ---
# Detecta si estás en Render (PostgreSQL) o en tu PC (SQLite)
database_url = os.environ.get("DATABASE_URL")
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("SECRET_KEY", "super_secreto_clave_maestra_apu")
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True # Pon False si pruebas sin HTTPS localmente

db = SQLAlchemy(app)

# --- 2. CORS UNIVERSAL (Para que Vercel no falle) ---
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# --- 3. CONFIGURACIÓN IA ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- UTILIDADES ---
def decimal_field(value):
    if value is None: return Decimal("0")
    return Decimal(str(value)) if str(value).strip() else Decimal("0")

def limpiar_json_md(texto: str) -> str:
    """Limpia las respuestas de la IA si vienen con formato Markdown."""
    texto = texto.strip()
    if texto.startswith("```"):
        inicio = texto.find("{")
        fin = texto.rfind("}")
        if inicio != -1 and fin != -1: return texto[inicio : fin + 1]
    return texto

# --- MODELOS DE BASE DE DATOS ---

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Proyecto(db.Model):
    __tablename__ = "proyectos"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    nombre = db.Column(db.String(255), nullable=False)
    tipo_documento = db.Column(db.String(50), default="Presupuesto")
    descripcion = db.Column(db.Text, nullable=True)
    total = db.Column(db.Numeric(14, 2), default=Decimal("0.00"))
    fecha = db.Column(db.Date, default=date.today)
    data_json = db.Column(db.Text, nullable=True)
    def to_dict(self):
        return {
            "id": self.id, "nombre": self.nombre, "tipo_documento": self.tipo_documento,
            "descripcion": self.descripcion, "total": float(self.total),
            "fecha": self.fecha.isoformat(),
            "data": json.loads(self.data_json) if self.data_json else {}
        }

class Material(db.Model):
    __tablename__ = "materiales"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    unidad = db.Column(db.String(50), nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 4), nullable=False)
    fecha_actualizacion = db.Column(db.Date, default=date.today)
    def to_dict(self): return {"id": self.id, "nombre": self.nombre, "unidad": self.unidad, "precio": float(self.precio_unitario)}

class ManoObra(db.Model):
    __tablename__ = "mano_obra"
    id = db.Column(db.Integer, primary_key=True)
    puesto = db.Column(db.String(255), nullable=False)
    salario_base = db.Column(db.Numeric(12, 2), nullable=False)
    def to_dict(self): return {"id": self.id, "puesto": self.puesto, "salario": float(self.salario_base)}

class Equipo(db.Model):
    __tablename__ = "equipos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    unidad = db.Column(db.String(50), nullable=False)
    costo_hora_maq = db.Column(db.Numeric(12, 4), nullable=False)
    def to_dict(self): return {"id": self.id, "nombre": self.nombre, "costo_hora": float(self.costo_hora_maq)}

class Maquinaria(db.Model):
    __tablename__ = "maquinaria"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    costo_adquisicion = db.Column(db.Numeric(14, 2), nullable=False)
    def to_dict(self): return {"id": self.id, "nombre": self.nombre, "costo_adq": float(self.costo_adquisicion)}

# --- FUNCIONES HELPER (NECESARIAS PARA TESTS) ---

def match_material(keyword: str, catalogo_materiales: List[Material]) -> Optional[Material]:
    if not catalogo_materiales: return None
    palabra = keyword.lower()
    for item in catalogo_materiales:
        if palabra in item.nombre.lower(): return item
    return catalogo_materiales[0] if catalogo_materiales else None

def match_mano_obra(keyword: str, catalogo_mano_obra: List[ManoObra]) -> Optional[ManoObra]:
    if not catalogo_mano_obra: return None
    palabra = (keyword or "").lower()
    if not palabra: return catalogo_mano_obra[0]
    for item in catalogo_mano_obra:
        texto = (getattr(item, "puesto", "") or "").lower()
        if palabra in texto: return item
    return catalogo_mano_obra[0]

# --- LÓGICA IA (BLINDADA) ---

def generar_apu_con_gemini(descripcion: str, unidad: str = "m2") -> Optional[Dict]:
    if not GEMINI_API_KEY: return None
    try:
        generation_config = {
            "temperature": 0.2, "top_p": 0.8, "top_k": 40, "max_output_tokens": 8192, "response_mime_type": "application/json",
        }
        model = genai.GenerativeModel(model_name=GEMINI_MODEL, generation_config=generation_config)
        
        system_prompt = """
        Actúa como experto analista de costos. Genera una matriz APU detallada.
        REGLAS:
        1. Si hay dimensiones ("Muro 10x3"), calcula 'cantidad_obra_detectada'.
        2. 'precio_unitario' SIEMPRE 0.
        3. Responde JSON válido."""
        
        prompt = f"{system_prompt}\nCONCEPTO: {descripcion}\nUNIDAD SUGERIDA: {unidad}"
        response = model.generate_content(prompt)
        return json.loads(limpiar_json_md(response.text))
    except Exception as e:
        print(f"Error Gemini APU: {e}")
        return None

def construir_matriz_desde_gemini(data_gemini: Dict) -> List[Dict]:
    if not data_gemini or not isinstance(data_gemini, dict): return []
    resultado = []
    for insumo in data_gemini.get("insumos", []):
        def sf(v): 
            try: return float(v)
            except: return 0.0
        
        resultado.append({
            "tipo_insumo": insumo.get("tipo_insumo", "Material"),
            "nombre": insumo.get("nombre", ""),
            "unidad": insumo.get("unidad", "pza"),
            "cantidad": sf(insumo.get("cantidad")),
            "merma": sf(insumo.get("merma")),
            "flete_unitario": sf(insumo.get("flete_unitario")),
            "precio_unitario": 0.0, # Candado de seguridad
            "costo_unitario": 0.0,
            "justificacion_breve": insumo.get("justificacion_breve", ""),
            "id_insumo": 0
        })
    return resultado

# --- ENDPOINTS ---

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(username=data.get("username")).first()
    if user and user.check_password(data.get("password")):
        session['user_id'] = user.id
        return jsonify({"message": "OK", "user": {"id": user.id, "username": user.username}}), 200
    return jsonify({"error": "Credenciales inválidas"}), 401

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Sesión cerrada"}), 200

@app.route("/api/auth/me", methods=["GET"])
def me():
    user_id = session.get('user_id')
    if not user_id: return jsonify({"error": "No autenticado"}), 401
    u = User.query.get(user_id)
    return jsonify({"id": u.id, "username": u.username})

@app.route("/api/proyectos", methods=["GET", "POST"])
def proyectos():
    user_id = session.get('user_id')
    if not user_id: return jsonify({"error": "No autorizado"}), 401
    
    if request.method == "GET":
        proyectos = Proyecto.query.filter_by(user_id=user_id).order_by(Proyecto.fecha.desc()).all()
        return jsonify([p.to_dict() for p in proyectos])
    
    data = request.get_json()
    nuevo = Proyecto(
        user_id=user_id,
        nombre=data.get("nombre"),
        tipo_documento=data.get("tipo_documento"),
        descripcion=data.get("descripcion"),
        total=Decimal(str(data.get("total", 0))),
        data_json=json.dumps(data.get("config_completa", {}))
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify(nuevo.to_dict()), 201

@app.route("/api/proyectos/<int:id>", methods=["DELETE"])
def delete_proyecto(id):
    user_id = session.get('user_id')
    if not user_id: return jsonify({"error": "No autorizado"}), 401
    p = Proyecto.query.filter_by(id=id, user_id=user_id).first()
    if p:
        db.session.delete(p)
        db.session.commit()
        return jsonify({"message": "Eliminado"}), 200
    return jsonify({"error": "No encontrado"}), 404

@app.route("/api/ia/chat_apu", methods=["POST"])
def chat_apu():
    d = request.get_json() or {}
    gemini = generar_apu_con_gemini(d.get("descripcion"), d.get("unidad"))
    
    return jsonify({
        "explicacion": gemini.get("explicacion") if gemini else "Error en IA",
        "insumos": construir_matriz_desde_gemini(gemini),
        "cantidad_obra_detectada": gemini.get("cantidad_obra_detectada") if gemini else None,
        "unidad_obra_detectada": gemini.get("unidad_obra_detectada") if gemini else None
    })

@app.route('/api/ia/cotizar', methods=['POST'])
def cotizar():
    try:
        mat = request.get_json().get('material')
        if not mat: return jsonify({"error": "Falta material"}), 400
        
        if not GEMINI_API_KEY:
            return jsonify({"tienda1": "Error API", "precio1": 0}), 500

        model = genai.GenerativeModel(model_name=GEMINI_MODEL)
        prompt = f"""Cotiza 3 precios MXN para: {mat}. JSON: {{ "tienda1": "...", "precio1": 0.0, "tienda2": "...", "precio2": 0.0, "tienda3": "...", "precio3": 0.0 }}"""
        
        response = model.generate_content(prompt)
        return jsonify(json.loads(limpiar_json_md(response.text)))
    except Exception as e:
        print(f"Error cotizar: {e}")
        return jsonify({"tienda1": "Error IA", "precio1": 0}), 500

# --- ENDPOINTS CATALOGO BÁSICO ---
@app.route("/api/materiales", methods=["GET", "POST"])
def materiales():
    if request.method == "GET": return jsonify([m.to_dict() for m in Material.query.all()])
    d = request.get_json()
    m = Material(nombre=d["nombre"], unidad=d["unidad"], precio_unitario=decimal_field(d["precio"]))
    db.session.add(m); db.session.commit()
    return jsonify(m.to_dict()), 201

@app.route("/")
def home():
    return "Backend APU Builder v1.0 - Activo"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="Sarsjs88").first():
            u = User(username="Sarsjs88"); u.set_password("bRyJaSa108288"); db.session.add(u); db.session.commit()
            print("✅ Usuario administrador creado")
    app.run(host="0.0.0.0", port=8000)
