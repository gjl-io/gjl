# gjl

**Un límite de políticas autohospedado para el tráfico de LLM.**

Inspeccione las solicitudes salientes, bloquee contenido o reescriba cuerpos de solicitud decodificados con reglas ordenadas de expresiones regulares, y controle las credenciales del proveedor en un límite operado por usted.

[English](README.md) · [한국어](README.ko.md) · [简体中文](README.zh-Hans.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md)

[Sitio web](https://gjl.io/) · [Lanzamientos](https://github.com/gjl-io/gjl/releases) ·
[Instalación y verificación](docs/install.md) · [Informes de seguridad](SECURITY.md) ·
[Acceso remoto](docs/remote-exposure.md) ·
[Observador de conexiones](docs/connection-observer.md) ·
[Licencias](LICENSE.md)

## Instalación rápida y puesta en marcha

Instale gjl con un solo comando. El instalador detecta automáticamente su sistema operativo, la arquitectura de la CPU y el entorno de pantalla, configura su variable `PATH` y prepara los componentes correspondientes.

### Windows (PowerShell)

```powershell
irm https://gjl.io/install.ps1 | iex
```

*O mediante `curl.exe`:*
```powershell
curl.exe -fsSL https://gjl.io/install.ps1 | powershell -Command -
```

### macOS y Linux (curl)

```bash
curl -fsSL https://gjl.io/install.sh | sh
```

### Instalación solo de CLI (excluir Desktop GUI)

Si prefiere instalar únicamente la CLI independiente de `gjl` en un sistema con entorno de escritorio gráfico:

* **Windows:**
  ```powershell
  $env:GJL_CLI_ONLY=1; irm https://gjl.io/install.ps1 | iex
  # o: & ([scriptblock]::Create((irm https://gjl.io/install.ps1))) -CliOnly
  ```
* **macOS y Linux:**
  ```bash
  curl -fsSL https://gjl.io/install.sh | sh -s -- --cli-only
  # o: curl -fsSL https://gjl.io/install.sh | GJL_CLI_ONLY=1 sh
  ```

> [!TIP]
> **Entornos sin interfaz gráfica (Headless) y servidores**: En sistemas sin servidor de pantalla (como servidores Linux, sesiones SSH headless o Windows Server Core), el instalador omite automáticamente la descarga de Flutter Desktop e instala únicamente la CLI autónoma de `gjl`.

### Ejecución

Inmediatamente después de la instalación en su terminal actual:

- **Desktop GUI:**
  ```bash
  gjl gui
  ```
- **Terminal / Sin interfaz gráfica (Headless):**
  ```bash
  gjl run
  ```

### Actualización de gjl

Mantenga su instalación al día con `gjl update`:

```bash
gjl update             # Actualizar todos los componentes instalados localmente (CLI y/o Desktop)
gjl update --cli-only  # Actualizar únicamente la CLI de gjl
gjl update --gui-only  # Actualizar únicamente la GUI de Desktop
gjl update --dry-run   # Comprobar actualizaciones sin descargarlas
```

Para descargas manuales de binarios y verificación de sumas de comprobación, consulte [Instalar y verificar gjl](docs/install.md).

## A quién está dirigido gjl

- **Personas y equipos enfocados en la seguridad** que desean bloquear o enmascarar contenido confidencial antes de que llegue a un proveedor, mantener las credenciales del proveedor en un límite bajo su propio control y, opcionalmente, capturar solicitudes de LLM y copias de respuestas saneadas en registros locales.
- **Usuarios que buscan mejores resultados de LLM** que utilizan reglas de ruta para ajustar el texto de los prompts o seleccionar otro modelo compatible con el proveedor en solicitudes inspeccionables, según lo que mejor funcione para un flujo de trabajo concreto.
- **Individuos u organizaciones con varias cuentas para un mismo proveedor de LLM** que desean una ruta separada para cada credencial y un control explícito sobre qué cuenta utiliza un cliente. gjl no balancea la carga automáticamente ni realiza conmutación por error entre cuentas.
- **Desarrolladores y equipos que utilizan múltiples herramientas de agentes de código** que desean realizar un seguimiento del consumo de tokens, calcular costos estimados y comparar patrones de uso entre diferentes agentes o flujos de trabajo.
- **Líderes de equipo y organizaciones** que necesitan agregar el consumo de tokens y los costos estimados por miembro individual, identidad de cliente o credencial en una infraestructura compartida.

## Qué hace gjl

gjl se ejecuta entre un cliente de LLM (como un agente de código, una extensión de IDE o una herramienta para desarrolladores) y un proveedor de LLM. Cada ruta pertenece a Door o Gate y posee su destino de proveedor, fuente de credenciales, política de autenticación entrante y reglas de enmascaramiento.

La ruta de solicitud protegida es:

```text
cuerpo decodificado
  → comprobación previa de regla de bloqueo
  → reemplazos ordenados
  → límite de credenciales
  → proveedor
```

- **Bloquear o reemplazar contenido coincidente en solicitudes inspeccionadas**: Las reglas de ruta se ejecutan antes de que se inyecte la autenticación del proveedor. Cubren cuerpos HTTP decodificados compatibles, cargas útiles Connect JSON no comprimidas y mensajes de texto WebSocket. No inspeccionan cargas útiles de gRPC o Connect Protobuf, tramas comprimidas de Connect, mensajes binarios de WebSocket, encabezados o rutas y parámetros de URL. Una regla protege únicamente el contenido con el que coincide en una ruta compatible.
- **Adaptar el contenido de la solicitud deliberadamente**: Una ruta también puede reescribir una frase del prompt o un campo de modelo cuando el cuerpo decodificado tiene una estructura identificable de forma fiable. Estas son las mismas reglas de cuerpo utilizadas para datos confidenciales.
- **Mantener las credenciales del proveedor fuera de los clientes mediante rutas**: Asocie una fuente de credenciales a cada ruta y reemplace la autenticación únicamente en el límite de salida, manteniendo las claves ascendentes fuera de las configuraciones de los clientes.
- **Intermediar credenciales hacia retransmisores emparejados con Vault**: Vault proporciona claves API estáticas y administra los ciclos de vida de actualización de OAuth a través de RPC mTLS entre Door y Vault sin actuar como proxy del tráfico de LLM. Para OAuth, los retransmisores toman prestados solo tokens de acceso de corta duración bajo demanda, mientras que el material de actualización nunca abandona Vault.
- **Registrar el uso de tokens y costos estimados**: gjl registra los tokens de prompt, finalización y caché informados por el proveedor junto con valoraciones de costos en USD fuera de línea en un libro mayor protegido por el propietario. El seguimiento de uso es independiente del registro de tráfico, no almacena cuerpos de prompts ni secretos, y no requiere servicios de monitoreo externos.
- **Preservar los cuerpos de respuesta del proveedor**: El enmascaramiento de ruta nunca reescribe el cuerpo de respuesta entregado al cliente; solo sanea una copia de registro local de tamaño limitado. El relay elimina los encabezados HTTP hop-by-hop según sea necesario al reenviar la respuesta.
- **Reenviar metadatos de auditoría sin cuerpos de tráfico**: Los operadores pueden configurar un receptor de auditoría remoto para recopilar metadatos de eventos y tokens, pero este recibe únicamente metadatos. Los cuerpos de solicitudes y respuestas saneadas permanecen estrictamente en el almacenamiento de auditoría local protegido por el propietario hasta que se eliminen explícitamente.
- **Operar sin la nube de un proveedor**: gjl no tiene un plano de control alojado, cuenta de producto, inicio de sesión, servidor de licencias, registro de dispositivos ni telemetría.

## Door, Gate y Vault

Door, Gate y Vault son capacidades concurrentes de un único demonio (iniciado con `gjl run`), no ediciones separadas.

| Rol | Propósito | Límite típico |
| --- | --- | --- |
| **Door** | Retransmisor local y conmutador de rutas | Estación de trabajo de desarrollador o servidor local |
| **Gate** | Puerta de enlace TLS compartida, límite de políticas organizacionales y punto de inyección de credenciales | Un límite de red operado por el usuario o la organización |
| **Vault** | Intermediario de credenciales que sirve claves API y custodia el material de actualización | Un límite dedicado para la gestión de credenciales |

Las rutas de despliegue admitidas incluyen:

```text
Cliente LLM --> Door --------------------> Proveedor
Cliente LLM --> Door --> Gate -----------> Proveedor
Cliente LLM ------------> Gate -----------> Proveedor
                Door <-> Vault
           solo RPC de credenciales
```

Vault nunca recibe prompts, código fuente, solicitudes normales de proveedores ni respuestas sin procesar.

## Descarga de gjl

Descargue el archivo correspondiente a su sistema operativo y arquitectura desde [GitHub Releases](https://github.com/gjl-io/gjl/releases).
Las versiones alfa están marcadas como **Pre-release**. Lea las notas de la versión y [verifique la descarga](docs/install.md) antes de instalar. Los paquetes de escritorio incluyen el binario `gjl` coincidente.

La versión preliminar inicial no cuenta con firmas de editores de confianza para Windows/macOS ni notarización de macOS. Por lo tanto, el paquete Windows MSIX no está disponible; macOS puede requerir una confirmación individual de **Abrir de todos modos (Open Anyway)**. Consulte la guía de instalación para conocer los límites de confianza y las verificaciones precisas.

| Plataforma | Desktop + `gjl` | `gjl` autónomo |
| --- | --- | --- |
| Windows x64 | `gjl-windows-amd64.zip` | `gjl-windows-amd64.exe` |
| Windows Arm64 | — | `gjl-windows-arm64.exe` |
| Linux x64 | `gjl-linux-amd64.deb` o `gjl-linux-amd64.zip` | `gjl-linux-amd64` |
| Linux Arm64 | `gjl-linux-arm64.deb` o `gjl-linux-arm64.zip` | `gjl-linux-arm64` |
| macOS Intel | `gjl-darwin-amd64.pkg` o `gjl-darwin-amd64.zip` | `gjl-darwin-amd64` |
| macOS Apple silicon | `gjl-darwin-arm64.pkg` o `gjl-darwin-arm64.zip` | `gjl-darwin-arm64` |

### Idiomas de la aplicación de escritorio

La aplicación Desktop admite ocho idiomas de interfaz. Sigue la configuración regional del sistema y recurre al inglés cuando no coincide ningún idioma admitido. Los nombres de producto centrales gjl, Door, Gate y Vault se mantienen en inglés en todas las configuraciones regionales.

### Retención de perfiles en versión Alpha

Las versiones alfa no prometen compatibilidad de archivos de estado con versiones alfa posteriores. Utilice un nuevo perfil cuando pruebe una versión más reciente. gjl no elimina ni convierte automáticamente perfiles anteriores. Exporte o haga una copia de seguridad explícita de cualquier configuración, credenciales, material TLS, registros de emparejamiento, auditoría y datos de uso antes de cambiar de perfil.

## Comenzando

Los paquetes de escritorio incluyen la CLI y el daemon `gjl`. La aplicación Desktop administra el daemon local a través de IPC protegido por el propietario. Acepta credenciales durante la entrada y las envía al daemon; el daemon es propietario del almacenamiento persistente y aplica las políticas.

Enrutamiento del tráfico de LLM a través de gjl requiere tres elementos:

1. **Una Ruta (Route)**: Define el destino del proveedor ascendente, las reglas de enmascaramiento y la política de autenticación para Door o Gate. Por defecto, las credenciales del cliente pasan sin cambios (passthrough), y el registro de tráfico y la auditoría de enmascaramiento están desactivados.
2. **Un Listener correspondiente**: El punto de entrada del cliente—ya sea Door (bucle invertido local loopback) para una estación de trabajo o Gate (TLS) para acceso compartido en red—vinculado a esa ruta. (Los listeners solo se vinculan a rutas del mismo rol.)
3. **La URL base del cliente de LLM**: Configurar su agente de código, extensión de IDE o herramienta de desarrollador para que apunte a la dirección de ese listener.

### Configuración en Desktop

En la aplicación de escritorio, puede configurar estos elementos a través del asistente o manualmente:

- **Configuración rápida (Asistente)**: Haga clic en **+ (Agregar)** en el HUD superior del panel de control. Al elegir **Usar en este dispositivo**, se agrupan los pasos 1 y 2, creando automáticamente una ruta local de Door y un listener loopback con credenciales en passthrough. Al elegir **Compartir con el equipo**, se le guiará para configurar un extremo compartido de **Gate** o un intermediario de credenciales de **Vault**.
- **Configuración manual**: Abra la vista **Rutas** para crear e inspeccionar rutas y listeners individualmente.

> [!TIP]
> **Gestión de credenciales de proveedor (opcional):** Por defecto, gjl pasa las credenciales entrantes del cliente al proveedor sin almacenarlas. Si desea que gjl administre, inyecte o intermedie credenciales en el límite, registre primero la credencial en el catálogo independiente de **Credenciales** antes de hacer referencia a ella en su ruta.

### Gestión sin interfaz gráfica o por CLI

En un entorno sin interfaz gráfica (headless) o desde la línea de comandos, ejecute el daemon y administre entidades mediante el binario integrado `gjl`:

```console
$ gjl run
```

En otra terminal:

```console
$ gjl status
$ gjl doctor
$ gjl route --help
$ gjl listener --help
$ gjl --help
```

La CLI y Desktop utilizan un socket de dominio Unix en macOS/Linux y una canalización con nombre (named pipe) en Windows. No escriben directamente en la configuración, credenciales o almacenamiento de auditoría propiedad del daemon.

## Uso de reemplazos de ruta

`replace` (reemplazo) es una regla para el cuerpo de la solicitud, no solo un enmascarador de secretos. Una ruta con un alcance acotado puede cambiar `an apple` por `the green apple` si se demuestra que ese cambio mejora una tarea concreta. También puede actualizar el modelo solicitado de `gpt-5.6-sol` a `gpt-6-sol` cuando el proveedor admita el modelo más nuevo pero la herramienta del cliente aún no lo haya incorporado. Una reescritura no puede hacer disponible un modelo no disponible ni cambiar un nombre de modelo transportado únicamente en un encabezado o URL.

**Diseñe el patrón a partir del cuerpo decodificado real.** Antes de habilitar una regla, considere si su patrón identifica de forma unívoca el texto deseado. Un nombre de modelo aislado o palabras cotidianas también pueden aparecer en prompts, código, ejemplos u otros campos. Habilite temporalmente el registro de tráfico de la ruta, inspeccione el cuerpo de la solicitud local (`body`) en la actividad de Desktop o mediante `gjl audit query`, `gjl audit bodies` y `gjl audit body-save`, y use su estructura para definir el patrón. Los encabezados no son objeto de reemplazo de cuerpo. Realice la captura antes de activar una reescritura si necesita ver el cuerpo original del cliente: el cuerpo de la solicitud en la auditoría registra lo que se envió al proveedor después del reemplazo. El registro de tráfico está desactivado de manera predeterminada y retiene los cuerpos localmente hasta su eliminación explícita. Los cuerpos guardados en archivos independientes requieren eliminación separada.

Por ejemplo, un cuerpo de solicitud WebSocket `response.create` capturado utilizaba JSON compacto sin espacios: `{"type":"response.create","model":"gpt-6-sol",...}` con el campo de modelo delimitado por comas. Para un cliente que envía la misma estructura con el modelo anterior, la siguiente regla de ruta aborda ese campo:

```json
{
  "id": "upgrade-model",
  "mode": "replace",
  "pattern": ",\"model\":\"gpt-5\\.6-sol\",",
  "replacement": ",\"model\":\"gpt-6-sol\","
}
```

Este ejemplo depende de una estructura específica: no coincidirá con un JSON con formato legible (pretty-printed) ni con un campo `model` en otra posición. Inspeccione el cuerpo de la solicitud de ese cliente y ajuste la regla si la estructura difiere. gjl utiliza la sintaxis de expresiones regulares Go RE2 y aplica las reglas de reemplazo en el orden de la ruta tras verificar todas las reglas de bloqueo en el cuerpo decodificado original. Las reglas nunca reescriben el cuerpo de respuesta enviado al cliente; únicamente sanean la copia de registro local.

Para reglas de texto confidencial, puede ser útil indicar a la IA del cliente que el contenido saliente se reescribe en el límite de la red. Describa el marcador de posición y el comportamiento esperado sin revelar el secreto en sí. El proveedor recibe la solicitud ya modificada, por lo que una instrucción dentro de ella no puede brindarle acceso al texto original. Para una ruta configurada con `<GJL_MASKED>`, una instrucción de agente puede ser:

> gjl replaces matching sensitive text with `<GJL_MASKED>` before the provider receives the request. Keep that placeholder intact; do not try to reconstruct its original value.

Verifique una solicitud real tras modificar una regla, luego desactive el registro temporal de tráfico y elimine explícitamente los eventos de auditoría innecesarios.

Consulte la [habilidad de reemplazo de rutas](skills/route-replacements/SKILL.md) para conocer el flujo de trabajo que parte de la estructura capturada y comprueba la especificidad de las reglas.

## Modelo de seguridad

- Las rutas pertenecen estrictamente a Door o Gate. Un listener de Door solo se vincula a rutas de Door, mientras que un listener de Gate solo se vincula a rutas de Gate; una misma ruta no puede compartirse entre roles.
- Las reglas de enmascaramiento pertenecen a una ruta. Cada regla de bloqueo comprueba la solicitud decodificada original antes de cualquier reemplazo; luego, los reemplazos se ejecutan en el orden de la lista.
- La autenticación del proveedor se gestiona de forma independiente del enmascaramiento del cuerpo y se selecciona según el mecanismo de protocolo del proveedor, no por el nombre de un agente de código.
- Las solicitudes y credenciales del proveedor nunca pasan por infraestructura operada por los desarrolladores de gjl.
- Door opera con prioridad local (Local-first). Para acceso remoto o compartido, utilice Gate con controles TLS y CIDR. No exponga un extremo de Door sin controles estrictos de acceso perimetral.
- Los cuerpos de tráfico locales no caducan automáticamente. La eliminación es una operación de gestión explícita, filtrada o confirmada.
- Gate puede conservar metadatos de clientes observados (Observed Client, como IP de origen, User-Agent limitado, notaciones complementarias y huellas dactilares HMAC de autenticación) en un almacenamiento local separado y protegido por el propietario, según el mejor esfuerzo. Estas observaciones no constituyen identidades humanas verificadas, y eliminar eventos de auditoría no borra dicho almacenamiento independiente.
- Un receptor de auditoría remoto configurado por el operador puede recibir metadatos (como identificadores de actores/clientes observados y uso de tokens), pero nunca cuerpos de tráfico ni señales brutas de observación. Trate estos metadatos como potencialmente confidenciales al configurar la retención y el acceso remoto.
- Las comprobaciones de actualización son consultivas. El daemon de lanzamiento lee únicamente etiquetas públicas de este repositorio de GitHub; nunca descarga ni instala actualizaciones automáticamente.

Lea [Acceso remoto a través de Gate](docs/remote-exposure.md) antes de exponer cualquier listener fuera de su host.

## Por qué el código fuente es privado

Consideramos que los avances en IA han facilitado la recreación de un retransmisor básico, reduciendo los beneficios de publicar la implementación completa. gjl maneja credenciales y tráfico de LLM altamente sensible, y estimamos que publicar el código fuente completo facilitaría a los atacantes la búsqueda de debilidades. Por lo tanto, mantenemos el código fuente bajo un modelo propietario como parte de nuestro enfoque de seguridad.

Puede verificar a dónde se conectan sus procesos de gjl en ejecución mediante nuestro [observador de conexiones](docs/connection-observer.md) público en Python. Este etiqueta los upstreams de rutas visibles, conexiones Gate/Vault, servidores OAuth conocidos y GitHub; los destinos no identificados se marcan como `UNKNOWN` para su revisión. No emite juicios de seguridad ni lee credenciales o cuerpos de solicitudes.

Inicie gjl y ejecute lo siguiente desde la raíz del repositorio:

```sh
python -m pip install -r tools/requirements.txt
python tools/observe_connections.py --duration 600
```

## Contenido del repositorio

Este repositorio es la sede de distribución pública de gjl. Contiene:

- Descargas oficiales de lanzamientos y etiquetas de versiones canónicas;
- Documentación pública operativa y de seguridad;
- Un [observador de conexiones local](docs/connection-observer.md) opcional que etiqueta pares de red visibles;
- Habilidades de agente (Agent Skills) para configurar flujos de trabajo admitidos de forma segura;
- [`llms.txt`](llms.txt), una guía de tareas de IA para la CLI, Desktop y la documentación del producto.

Las habilidades de agente disponibles cubren:

- [`skills/gjl-operations`](skills/gjl-operations/SKILL.md) — comprueba la CLI instalada y guía por las vistas de Desktop y la administración local.
- [`skills/route-replacements`](skills/route-replacements/SKILL.md) — diseña reglas de bloqueo y reemplazo del cuerpo a partir de estructuras observadas (incluyendo texto confidencial, frases de prompts y campos de modelo).
- [`skills/remote-exposure`](skills/remote-exposure/SKILL.md) — guía el emparejamiento mTLS entre Door y Gate y verifica los límites de acceso remoto.

## Informes de vulnerabilidades y licencias

Informe sobre vulnerabilidades de seguridad de forma privada a través del [formulario de informes de vulnerabilidades de GitHub](https://github.com/gjl-io/gjl/security/advisories/new).
Para errores no relacionados con la seguridad, utilice [GitHub Issues](https://github.com/gjl-io/gjl/issues/new). No incluya secretos ni tráfico privado en un problema público. Consulte [SECURITY.md](SECURITY.md).

Los términos de licencia del repositorio y la licencia de binarios del producto se unifican en [LICENSE.md](LICENSE.md). Los scripts de instalación públicos, las herramientas en Python y las habilidades de agente tienen [licencia MIT](LICENSE-MIT). Los binarios oficiales del producto siguen siendo propietarios bajo la [licencia de binarios del producto](PRODUCT-LICENSE.md). El [aviso del repositorio (NOTICE.md)](NOTICE.md) y los [avisos de terceros (THIRD-PARTY-NOTICES.md)](THIRD-PARTY-NOTICES.md) detallan el alcance.

## Garantías del proyecto

gjl está diseñado en torno al principio de autoridad local y soberanía del operador:

- Sin backend ni servicios en la nube gestionados por el proveedor;
- Sin cuentas de producto, inicios de sesión, bloqueo de funciones de pago ni registro de dispositivos;
- Sin telemetría;
- Sin solicitudes de proveedores, credenciales, configuraciones ni datos de auditoría en las comprobaciones de actualización;
- Sin instalación ni reversión automática de actualizaciones.

Las únicas interacciones de red del lado del proveedor son lecturas sin autenticación de las etiquetas públicas de GitHub, la descarga de recursos oficiales de la versión cuando el usuario ejecuta explícitamente `gjl update` y la apertura de la página pública de versiones desde la GUI de Desktop cuando se solicita.
