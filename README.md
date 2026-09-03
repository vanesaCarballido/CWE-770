# Demo CWE-770: Allocation of Resources Without Limits or Throttling

Laboratorio local en Docker para comparar un servidor **vulnerable** con uno **mitigado** frente al consumo excesivo de recursos.

Ambos contenedores tienen un límite de **256 MB de RAM y 1 CPU**. El objetivo es observar cómo la falta de límites puede provocar un **OOM (Out Of Memory)** y cómo diferentes controles de seguridad pueden evitarlo.


---

## 1. Objetivos

* Comprender la vulnerabilidad **CWE-770**.
* Observar el consumo excesivo de memoria provocado por peticiones grandes y concurrentes.
* Comparar un servidor vulnerable con uno protegido.
* Analizar un **OOM Kill** en Docker.
* Comprobar las mitigaciones mediante códigos HTTP y estado de los contenedores.
* Demostrar el principio de **Defense in Depth**.

---

## 2. Estructura del Proyecto

```text
cwe770-demo/
├── docker-compose.yml   # Servicios y límites de recursos
├── vulnerable/          # Puerto 5000: servidor vulnerable
├── fixed/               # Puerto 5001: Nginx + Gunicorn + Flask
├── loadtest/            # Script de prueba de carga
└── dashboard/           # Puerto 8000: interfaz de monitoreo
```

| Servicio   | Puerto | Descripción                        |
| ---------- | -----: | ---------------------------------- |
| Vulnerable | `5000` | Flask sin límites adecuados        |
| Fixed      | `5001` | Nginx + Gunicorn + Flask           |
| Dashboard  | `8000` | Interfaz para ejecutar las pruebas |

---

## 3. Prerrequisitos

Se necesita:

* Docker
* Docker Compose v2
* Navegador web
* Entorno aislado para realizar las pruebas

Verificar la instalación:

```bash
docker --version
docker compose version
```
<img width="376" height="65" alt="Captura de pantalla 2026-09-03 a la(s) 11 37 56" src="https://github.com/user-attachments/assets/4b2e1102-9aa7-4d1b-bc26-f18ffbc665cf" />

---

## 4. Arquitectura

### Servidor Vulnerable

```text
Cliente
   │
   ▼
Flask / Werkzeug
   │
   ▼
Sin límites adecuados
   │
   ▼
Alto consumo de memoria
   │
   ▼
OOM Kill
```

### Servidor Fixed

```text
Cliente
   │
   ▼
Nginx
   ├── Límite de payload
   ├── Rate limiting
   └── Timeouts
        │
        ▼
     Gunicorn
        │
        ▼
      Flask
        │
        └── MAX_CONTENT_LENGTH
```

---

# 5. Ejecutar el Laboratorio

Desde la carpeta raíz:

```bash
docker compose up --build -d
```
<img width="911" height="215" alt="Captura de pantalla 2026-09-03 a la(s) 11 38 58" src="https://github.com/user-attachments/assets/2d8223e5-34be-48de-82b0-ec37c32bd7f1" />

Verificar los contenedores:

```bash
docker compose ps
```
<img width="894" height="137" alt="Captura de pantalla 2026-09-03 a la(s) 11 39 56" src="https://github.com/user-attachments/assets/3fc23121-c673-4589-8ee4-946d41197167" />

### Comprobar el servidor vulnerable

```bash
curl http://localhost:5000/health
```

### Comprobar el servidor Fixed

```bash
curl http://localhost:5001/health
```

### Comprobar el Dashboard

```bash
curl http://localhost:8000
```

También se puede acceder desde el navegador:

**http://localhost:8000**

---

# 6. Dashboard

La interfaz permite:

* Ver el estado de los contenedores.
* Seleccionar el servidor vulnerable o Fixed.
* Configurar cantidad de peticiones.
* Configurar concurrencia.
* Configurar tamaño del payload.
* Ver los resultados de la prueba en tiempo real.
* Reiniciar los contenedores.

---

# 7. Demostración de CWE-770

## 7.1 Servidor Vulnerable

Desde el Dashboard:

1. Seleccionar **Vulnerable (`5000`)**.
2. Configurar, por ejemplo:

```text
Peticiones: 150
Concurrencia: 60
Payload: 6 MB
```

3. Presionar **"Ejecutar Carga"**.
4. Observar el consumo de memoria y el estado del contenedor.

### Resultado esperado

El servidor vulnerable procesa las solicitudes sin aplicar límites suficientes.

El consumo de memoria aumenta hasta alcanzar el límite de **256 MB**.

El contenedor puede terminar debido a un **OOM Kill** y aparecer como:

```text
EXITED
```

---

## 7.2 Servidor Fixed

Repetir la misma prueba seleccionando:

**Fixed (`5001`)**

El servidor mitigado aplica diferentes controles antes de procesar las solicitudes.

Los resultados esperados pueden incluir:

| Código | Significado              |
| -----: | ------------------------ |
|  `413` | Payload demasiado grande |
|  `429` | Demasiadas solicitudes   |
|  `502` | Bad Gateway              |
|  `503` | Service Unavailable      |

El objetivo es que el contenedor permanezca:

```text
RUNNING
```

en lugar de terminar por falta de memoria.

---

# 8. Comprobar el OOM

Después de una prueba contra el servidor vulnerable, comprobar:

```bash
docker inspect cwe770-vulnerable \
  --format='OOMKilled={{.State.OOMKilled}}'
```

Resultado esperado:

```text
OOMKilled=true
```

Consultar también el código de salida:

```bash
docker inspect cwe770-vulnerable \
  --format='ExitCode={{.State.ExitCode}}'
```

Normalmente:

```text
ExitCode=137
```

El código `137` corresponde normalmente a un proceso terminado mediante `SIGKILL`.

---

# 9. Monitorización

Durante la prueba se puede observar el consumo de recursos con:

```bash
docker stats
```

Para consultar específicamente el servidor vulnerable:

```bash
docker stats cwe770-vulnerable
```

También se pueden revisar los logs:

```bash
docker compose logs vulnerable
docker compose logs fixed
```

---

# 10. Mitigaciones

El servidor Fixed utiliza diferentes capas de protección:

| Control                  | Vulnerable | Fixed |
| ------------------------ | ---------- | ----- |
| Límite de payload        | ✗          | ✓     |
| Rate limiting            | ✗          | ✓     |
| Timeouts                 | ✗          | ✓     |
| Control de concurrencia  | ✗          | ✓     |
| Validación en Flask      | ✗          | ✓     |
| Nginx Reverse Proxy      | ✗          | ✓     |
| Límite de memoria Docker | ✓          | ✓     |

La combinación de estos mecanismos implementa **Defense in Depth**, evitando depender de una única medida de seguridad.

---

# 11. Limpieza

Para detener el laboratorio:

```bash
docker compose down
```

Para volver a construirlo desde cero:

```bash
docker compose down
docker compose up --build -d
```

---

## 12. Conclusión

La demo muestra cómo **CWE-770** puede provocar un consumo excesivo de recursos cuando una aplicación no establece límites adecuados.

En el servidor vulnerable, una carga elevada puede provocar que el contenedor alcance el límite de memoria y sea terminado mediante un **OOM Kill**.

El servidor Fixed incorpora controles en diferentes capas para limitar:

* Tamaño de las peticiones.
* Frecuencia de solicitudes.
* Concurrencia.
* Tiempo de conexión.
* Recursos disponibles.

De esta forma, las solicitudes excesivas son rechazadas o reguladas antes de provocar la caída del servicio.
