# Guía de despliegue gratuito de DataSmart (paso a paso)

El tablero es un **sitio estático**: todo (incluido el modelo de predicción y el analizador de reseñas) corre en el navegador, así que **no necesitas pagar servidor ni base de datos**. La API (Flask) es opcional y sirve para demostrar el "backend" del curso.

Elige **una** opción. Recomendada: **Opción A (GitHub Pages)**. Si quieres algo de 2 minutos sin Git, usa la **Opción B (Netlify Drop)**.

---
## Antes de empezar: construir el sitio

Necesitas Python 3.10+ en tu computadora (el mismo que usas en el curso).

1. Descomprime `DataSmart_entregable4.zip` en una carpeta, por ejemplo `C:\DataSmart` (Windows) o `~/DataSmart` (Mac/Linux).
2. Abre una terminal **dentro** de esa carpeta (Windows: clic derecho en la carpeta → "Abrir en Terminal").
3. Ejecuta:
   ```
   python tools/construir_sitio.py
   ```
4. Debe decir `dist/ listo; datasmart.html = 1.94 MB`. Se crea la carpeta **`dist/`**: es el sitio completo. Dentro hay un archivo **`datasmart.html`** que funciona solo, con doble clic, sin internet.

> Si ya existe la carpeta `dist/` en el zip, puedes saltarte este paso.

Para probarlo en tu PC antes de publicar:
```
cd dist
python -m http.server 8000
```
y abre http://localhost:8000 en el navegador. (Ctrl+C para detener.)

---
## Opción A · GitHub Pages (gratis, enlace permanente, se actualiza solo)

**Qué obtienes:** una dirección como `https://TU-USUARIO.github.io/datasmart-olist/`.

1. **Crea una cuenta** en https://github.com si no tienes (gratis).
2. Arriba a la derecha pulsa **+ → New repository**.
   - *Repository name*: `datasmart-olist`
   - Marca **Public** (Pages gratis exige repositorio público; el dataset de Olist ya es público y no subimos los datos crudos).
   - **No** marques "Add a README".
   - Pulsa **Create repository**.
3. En la página nueva verás "uploading an existing file" → pulsa ese enlace.
4. **Arrastra el contenido** de la carpeta `DataSmart` (todas las carpetas y archivos, no la carpeta contenedora). Importante: debe incluir la carpeta oculta **`.github`** (con `workflows/pages.yml` y `ci.yml`).
   - Windows: en el Explorador activa *Ver → Mostrar → Elementos ocultos*.
   - Mac: en Finder pulsa `Cmd + Shift + .` para ver ocultos.
   - Si el navegador no te deja arrastrar `.github`, usa la alternativa con Git (abajo).
5. Abajo pulsa **Commit changes**.
6. Ve a **Settings → Pages**. En *Build and deployment → Source* elige **GitHub Actions**.
7. Ve a la pestaña **Actions**. Verás un flujo "Publicar tablero en GitHub Pages" ejecutándose (círculo amarillo). Espera 1–2 minutos hasta el check verde.
8. Vuelve a **Settings → Pages**: arriba aparece la dirección pública. Ábrela: ya está tu tablero.

**Alternativa con Git (terminal):**
```
git init
git add .
git commit -m "DataSmart entregable 4"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/datasmart-olist.git
git push -u origin main
```
(GitHub te pedirá iniciar sesión; usa un *Personal Access Token* como contraseña si te lo solicita: Settings → Developer settings → Tokens.)

**Si el check sale rojo:** abre el flujo fallido → lee la línea en rojo. Los casos típicos: (a) no marcaste *Source: GitHub Actions* en el paso 6; (b) faltó la carpeta `.github` o `tools`.

**Para actualizar:** cada vez que subas cambios a `main`, se vuelve a publicar solo.

---
## Opción B · Netlify Drop (2 minutos, sin Git)

1. Entra a https://app.netlify.com/drop (crea cuenta gratis con tu correo o con Google/GitHub).
2. **Arrastra la carpeta `dist`** (la carpeta completa) a la zona "Drag and drop your site folder here".
3. En unos segundos te da una dirección tipo `https://nombre-aleatorio.netlify.app`.
4. (Opcional) *Site configuration → Change site name* para elegir un nombre legible.

Para actualizar: *Deploys → arrastra de nuevo la carpeta `dist`*.

---
## Opción C · Render (si quieres mostrar también la API Flask)

Render ejecuta `app/api.py`, que sirve el tablero **y** los endpoints `/api/...`.

1. Sube el proyecto a GitHub (pasos 1–5 de la Opción A; para Render el repositorio puede ser privado).
2. Crea cuenta en https://render.com (puedes entrar con GitHub).
3. **New + → Blueprint** → conecta tu repositorio `datasmart-olist` → Render lee `render.yaml` → pulsa **Apply**.
   - Si prefieres manual: **New + → Web Service**, runtime **Python**, *Build Command* `pip install -r requirements-api.txt`, *Start Command* `gunicorn app.api:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`, plan **Free**.
4. Espera ~5 minutos (instala XGBoost). Cuando diga **Live**, abre la URL `https://datasmart-olist.onrender.com`.
5. Prueba la API: abre `https://TU-SERVICIO.onrender.com/api/health` → debe mostrar `{"estado":"ok",...}`.

Notas del plan gratuito: el servicio se **duerme tras 15 minutos sin visitas** y tarda ~50 s en despertar. Abre la URL 1 minuto antes de tu sustentación.

Probar la API con la terminal:
```
curl -X POST https://TU-SERVICIO.onrender.com/api/predict -H "Content-Type: application/json" ^
  -d "{\"customer_state\":\"RJ\",\"categoria_principal\":\"toys\",\"dias_estimados\":18,\"precio_total\":90,\"flete_total\":25,\"seller_state\":\"SP\",\"distancia_km\":400}"
```
(En Mac/Linux cambia `^` por `\`.)

---
## Opción D · Docker (en tu computadora)
```
docker compose up --build
```
y abre http://localhost:8000. (Instala Docker Desktop antes: https://www.docker.com/products/docker-desktop)

---
## Opción E · Solo el archivo único
Envía `dist/datasmart.html` por correo o súbelo a Drive: se abre con doble clic en cualquier navegador moderno, **sin internet**. Es el plan B por si falla el Wi-Fi en la sustentación.

---
## Lista de verificación el día de la sustentación
- [ ] Abre el enlace público 5 minutos antes (Render: 1 minuto antes para despertarlo).
- [ ] Ten `datasmart.html` en el escritorio como respaldo.
- [ ] Prueba el simulador (sección *Simulador*) y el analizador de reseñas.
- [ ] Alterna **Guiado/Experto** y **Claro/Oscuro** para mostrar que existen.
- [ ] Ten abierta la pestaña *Actions* de GitHub (check verde) para mostrar las pruebas automáticas y el despliegue continuo.

## Problemas frecuentes
| Síntoma | Causa | Solución |
|---|---|---|
| Página en blanco al abrir `index.html` con doble clic | El navegador bloquea la lectura de los datos locales | Usa `datasmart.html` o `python -m http.server` |
| "404" en GitHub Pages | Pages sin fuente GitHub Actions o flujo aún corriendo | Settings → Pages → Source: GitHub Actions; espera el check verde |
| Render tarda mucho | Plan gratuito dormido | Abre la URL 1 minuto antes |
| `python` no se reconoce | Python no está en el PATH | Reinstala marcando "Add Python to PATH" o usa `py` en Windows |
