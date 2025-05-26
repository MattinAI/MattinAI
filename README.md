# MattinAI

Para utilizar MattinAI con todas sus funcionalidades, es necesario crear una imagen personalizada de LangFlow. Siga estos pasos para configurar correctamente el entorno:

### Requisitos previos
- Docker instalado en su sistema
- Git

### Instrucciones de instalación

1. Clone el repositorio:
   ```bash
   git clone https://github.com/MattinAI/MattinAI.git
   ```

2. Navegue al directorio de Langflow
    ```bash
    cd langflow/langflow
    ```

3. Genere la imagen Docker utilizando el Makefile
    ```bash
    make dockerfile_build DOCKERFILE=./docker/build_and_push.Dockerfile VERSION=''
    ```

## Initial Setup

Una vez generada la imagen, es necesario indicar en el docker-compose su nombre:

```docker-compose 
services:
  langflow:
    image: 'image:tag'
```

A continuación levantaremos el servicio:
```
docker compose up --build
```

Para poder funcionar con los flows desarrollados es necesario indicar una <API_KEY> de openai en el componente correspondiente de cada flow. Para ello haremos lo siguiente:

1. Entrar a la web de Langflow -> `localhost:7860`
1. Hacer click sobre la foto de perfil y entrar en "Settings".
2. Acceder a "Global Variables".
3. Crear una nueva variable de entorno que sea la api key de openai para poder reutilizarla en todos los flows.
4. Acceder a los flows e indicar la variable de entorno recién creada en cada uno de los agentes que la necesiten.

## Tracing
El archivo de configuración de los contenedores de langflow lleva configurada la parte de tracing con **Langfuse**. 

Para que esté activa es necesario que una vez iniciado el sistema:

1. Entremos a la web de langfuse -> `localhost:3000`

2. Nos demos de alta en la plataforma y creemos una organización + proyecto

3. Recojamos las api keys proporcionadas por Langfuse, tanto la pública como privada

4. Cambiar sus valores en el **docker-compose.yml** 

    - LANGFUSE_SECRET_KEY
    - LANGFUSE_PUBLIC_KEY

5. Arrancar de nuevo el servicio de langflow comentando la linea de carga de flows:

```shell
# Remove this line from environment variables:
# - LANGFLOW_LOAD_FLOWS_PATH=flows
```

```shell
docker-compose up -d --no-deps --force-recreate langflow
```

## Subsequent Starts
Después de la primera inicialización:

```bash
docker start <service_name>  # Recommended method
```
O si se usa docker-compose:

```yaml
# Remove this line from environment variables:
# - LANGFLOW_LOAD_FLOWS_PATH=flows
```

Esto es necesario ya que como el sistema ha cargado los flows del backup en la primera inizialización, se volverían a intentar cargar lo que causaría error.