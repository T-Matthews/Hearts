# Hearts

## Setup

### Requirements:
- Docker
- Docker Compose

### Building Image:
Run this to build the docker image
```bash
docker-compose build
```

### Running the Server with All Dependencies:
```bash
docker-compose up
```

### Running Django Manage Commands:
```
docker-compose run web python manage.py <command>
```
For example:
```bash
docker-compose run web python manage.py migrate
docker-compose run web python manage.py makemigrations
docker-compose run web python manage.py test
docker-compose run web python manage.py shell_plus
```