# MattinAI

## Configuración de entorno personalizado con LangFlow

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

### Uso

Una vez generada la imagen, es necesario indicar en el docker-compose su nombre:

```docker-compose 
services:
  langflow:
    image: 'image:tag'
```