# Demo CWE-770: Allocation of Resources Without Limits or Throttling

Laboratorio local (Docker) para comparar un servidor **vulnerable** contra
uno **mitigado**, ambos con los mismos límites de contenedor (256MB RAM,
1 CPU), para que la diferencia observada venga del código, no de Docker.

⚠️ Uso exclusivo en tu entorno aislado (VM Kali + Docker). No apuntes el
script de carga a ningún host que no sea `localhost`.

## Estructura

```
cwe770-demo/
├── docker-compose.yml
├── vulnerable/       # puerto 5000 - sin límites ni rate limiting
├── fixed/             # puerto 5001 - con límites y rate limiting
└── loadtest/          # script de carga para comparar ambos
```

## 1. Levantar el laboratorio

Desde la carpeta `cwe770-demo/`:

```bash
docker compose up --build -d
```

Verificá que ambos respondan:

```bash
curl http://localhost:5000/health   # vulnerable
curl http://localhost:5001/health   # fixed
```

## 2. Preparar el script de carga

```bash
cd loadtest
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## 3. Observar recursos en vivo

En una terminal aparte, antes de lanzar la carga:

```bash
docker stats cwe770-vulnerable cwe770-fixed
```

Esto te muestra el % de CPU y MB de RAM usados por cada contenedor en tiempo real.

## 4. Ejecutar la prueba contra el servidor VULNERABLE

En otra terminal:

```bash
python3 load_test.py --target http://localhost:5000 --requests 150 --concurrency 60 --payload-mb 6
python3 load_test.py --target http://localhost:5001 --requests 150 --concurrency 60 --payload-mb 6
```

Qué vas a observar:
- La memoria del contenedor `cwe770-vulnerable` sube rápido en `docker stats`.
- Con carga suficiente, el contenedor puede llegar al límite de 256MB y
  el proceso Flask puede caerse (OOM) o volverse muy lento -> **Denegación
  de Servicio**.
- Todas las requests son aceptadas sin control, sin importar cuántas ni
  cuán grandes sean.
- el contendor `cwe770-vulnerable` probablemente se caiga

## 5. Ejecutar la misma prueba contra el servidor MITIGADO

```bash
python3 load_test.py --target http://localhost:5001 --requests 200 --concurrency 50 --payload-mb 5
```

Qué vas a observar:
- Muchas requests devuelven **413** (payload too large, porque cada
  archivo de 5MB excede el límite de 2MB configurado).
- Si subís el límite de tamaño para que pasen, vas a ver **429** (rate
  limit exceeded) apenas se superan las 10 requests/min al endpoint
  `/upload`.
- El consumo de memoria del contenedor `cwe770-fixed` se mantiene estable
  y bajo, incluso bajo la misma carga.

## 6. Variar la demo

- Subí `--payload-mb` a 20 o 50 para ver más rápido el efecto en el
  servidor vulnerable.
- Probá el endpoint `--endpoint /echo` (carga el body entero en memoria
  sin guardarlo a disco -> presión de RAM más directa).
- Ajustá `mem_limit` en `docker-compose.yml` para simular un servidor
  con menos recursos (ej. `128m`) y ver la caída más rápido.

## 7. Apagar todo

```bash
docker compose down -v
```

## Resumen para tu presentación/informe

| Aspecto                         | Vulnerable (5000)          | Mitigado (5001)                       |
|----------------------------------|-----------------------------|----------------------------------------|
| Límite de tamaño de request       | Ninguno                     | 2 MB (`MAX_CONTENT_LENGTH`)            |
| Rate limiting                    | Ninguno                     | 10-20 req/min por IP (`flask-limiter`) |
| Comportamiento bajo carga         | Consumo de RAM sin control, riesgo de OOM/crash | Rechazos controlados (413/429), servicio estable |
| CWE relacionado                  | CWE-770                     | Mitigación de CWE-770                  |
